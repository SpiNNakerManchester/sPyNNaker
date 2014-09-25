from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities.utility_calls \
    import get_region_base_address_offset
from spynnaker.pyNN.utilities import constants

from pacman.utilities import constants as pacman_constants


import logging
import numpy
import struct
import math

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractRecordableVertex(object):
    """
    Underlying AbstractConstrainedVertex model for Neural Applications.
    """

    def __init__(self, machine_time_step, label):
        self._record = False
        self._record_v = False
        self._record_gsyn = False
        self._focus_level = None
        self._app_mask = pacman_constants.DEFAULT_MASK
        self._label = label
        self._machine_time_step = machine_time_step

    @property
    def machine_time_step(self):
        return self._machine_time_step

    @property
    def record(self):
        """
        method to return if the vertex is set to be recorded
        """
        return self._record

    def set_record(self, setted_value):
        """
        method that sets the vertex to be recordable, """
        self._record = setted_value

    @property
    def record_v(self):
        return self._record_v

    @property
    def record_gsyn(self):
        return self._record_gsyn

    def set_record_v(self, setted_value):
        self._record_v = setted_value

    def set_record_gsyn(self, setted_value):
        self._record_gsyn = setted_value

    def get_recording_region_size(self, bytes_per_timestep):
        """
        Gets the size of a recording region in bytes
        """
        if self._no_machine_time_steps is None:
            raise Exception("This model cannot record this parameter"
                            + " without a fixed run time")
        return (constants.RECORDING_ENTRY_BYTE_SIZE +
                (self._no_machine_time_steps * bytes_per_timestep))

    def _get_spikes(
            self, graph_mapper, placements, transciever, compatible_output,
            spike_recording_region, sub_vertex_out_spike_bytes_function):
        """
        Return a 2-column numpy array containing cell ids and spike times for
        recorded cells.   This is read directly from the memory for the board.
        """

        logger.info("Getting spikes for {}".format(self._label))

        spikes = numpy.zeros((0, 2))

        # Find all the sub-vertices that this pynn_population.py exists on
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        for subvertex in subvertices:
            placement = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placement.x, placement.y, placement.p
            subvertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            lo_atom = subvertex_slice.lo_atom
            logger.debug("Reading spikes from chip {}, {}, core {}, "
                         "lo_atom {}".format(x, y, p, lo_atom))

            # Get the App Data for the core
            app_data_base_address = \
                transciever.get_cpu_information_from_core(
                    x, y, p).user[0]

            # Get the position of the spike buffer
            spike_region_base_address_offset = \
                get_region_base_address_offset(app_data_base_address,
                                               spike_recording_region)
            spike_region_base_address_buf = \
                str(list(transciever.read_memory(
                    x, y, spike_region_base_address_offset, 4))[0])
            spike_region_base_address = \
                struct.unpack("<I", spike_region_base_address_buf)[0]
            spike_region_base_address += app_data_base_address

            # Read the spike data size
            number_of_bytes_written_buf =\
                str(list(transciever.read_memory(
                    x, y, spike_region_base_address, 4))[0])
            number_of_bytes_written = \
                struct.unpack_from("<I", number_of_bytes_written_buf)[0]

            #check that the number of spikes written is smaller or the same as
            #  the size of the memory region we allocated for spikes
            out_spike_bytes = sub_vertex_out_spike_bytes_function(subvertex,
                    subvertex_slice)
            size_of_region = \
                self.get_recording_region_size(out_spike_bytes)

            if number_of_bytes_written > size_of_region:
                raise exceptions.MemReadException("the amount of memory written"
                                                  " was larger than was "
                                                  "allocated for it")

            # Read the spikes
            logger.debug("Reading {} ({}) bytes starting at {} + 4"
                         .format(number_of_bytes_written,
                                 hex(number_of_bytes_written),
                                 hex(spike_region_base_address)))
            spike_data = transciever.read_memory(
                x, y, spike_region_base_address + 4, number_of_bytes_written)

            # Extract number of spike bytes from subvertex
            number_of_time_steps_written = \
                number_of_bytes_written / out_spike_bytes

            logger.debug("Processing {} timesteps"
                         .format(number_of_time_steps_written))

            current_word_count = 0
            for block in spike_data:
                read_pointer = 0
                string_based_block = str(block)
                words_in_block = int(math.ceil(len(string_based_block) / 4))
                words_in_a_timer_tic = math.ceil(out_spike_bytes / 4)
                for current_word_index in range(0, words_in_block):
                    # Unpack the word containing the spikingness of 32 neurons
                    spike_vector_word = struct.unpack_from(
                        "<I", string_based_block, read_pointer)
                    read_pointer += 4

                    spikes = self._unpack_word_of_spikes(
                        spikes, subvertex, current_word_count,
                        spike_vector_word, words_in_a_timer_tic,
                        graph_mapper=graph_mapper)
                    current_word_count += 1

        if len(spikes) > 0:
            logger.debug("Arranging spikes as per output spec")

            if compatible_output:
                # Change the order to be neuronID : time (don't know why - this
                # is how it was done in the old code, so I am doing it here too)
                spikes[:, [0, 1]] = spikes[:, [1, 0]]

                # Sort by neuron ID and not by time
                spike_index = numpy.lexsort((spikes[:, 1], spikes[:, 0]))
                spikes = spikes[spike_index]
                return spikes

            # If compatible output, return sorted by spike time
            spike_index = numpy.lexsort((spikes[:, 1], spikes[:, 0]))
            spikes = spikes[spike_index]
            return spikes

        print("No spikes recorded")
        return None

    @staticmethod
    def _unpack_word_of_spikes(spikes, subvertex, current_word_count,
                               spike_vector_word, words_in_a_timer_tic,
                               graph_mapper):
        # if the word is zero no spikes have been recorded
        neurons_per_word = constants.BITS_PER_WORD  # each bit is a neuron
        if spike_vector_word[0] != 0:
            # Loop through each bit in this word
            for neuron_bit_index in range(0, int(constants.BITS_PER_WORD)):
                # If the bit is set
                neuron_bit_mask = (1 << neuron_bit_index)
                if (spike_vector_word[0] & neuron_bit_mask) != 0:
                    # Calculate neuron ID
                    out_word_index = int(current_word_count %
                                         words_in_a_timer_tic)
                    base_neuron_id = out_word_index * neurons_per_word
                    lo_atom = \
                        graph_mapper.get_subvertex_slice(subvertex).lo_atom
                    neuron_id = (neuron_bit_index + base_neuron_id + lo_atom)
                    # Add spike time and neuron ID to returned lists
                    current_tic = int(math.floor(current_word_count /
                                      words_in_a_timer_tic))
                    spikes = numpy.append(spikes, [[current_tic, neuron_id]], 0)
        return spikes

    def get_neuron_parameter(
            self, region, compatible_output, has_ran, graph_mapper, placements,
            txrx, machine_time_step):
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore neuron param cannot "
                "be retrieved")

        value = numpy.zeros((0, 3))

        # Find all the sub-vertices that this pynn_population.py exists on
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        for subvertex in subvertices:
            placment = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placment.x, placment.y, placment.p

            # Get the App Data for the core
            app_data_base_address = txrx.\
                get_cpu_information_from_core(x, y, p).user[0]

            # Get the position of the value buffer
            neuron_param_region_base_address_offset = \
                get_region_base_address_offset(app_data_base_address, region)
            neuron_param_region_base_address_buf = str(list(txrx.read_memory(
                x, y, neuron_param_region_base_address_offset, 4))[0])
            neuron_param_region_base_address = \
                struct.unpack("<I", neuron_param_region_base_address_buf)[0]
            neuron_param_region_base_address += app_data_base_address

            # Read the size
            number_of_bytes_written_buf = \
                str(list(txrx.read_memory(
                    x, y, neuron_param_region_base_address, 4))[0])

            number_of_bytes_written = \
                struct.unpack_from("<I", number_of_bytes_written_buf)[0]

            # Read the values
            logger.debug("Reading {} ({}) bytes starting at {}".format(
                number_of_bytes_written, hex(number_of_bytes_written),
                hex(neuron_param_region_base_address + 4)))

            neuron_param_region_data = txrx.read_memory(
                x, y, neuron_param_region_base_address + 4,
                number_of_bytes_written)

            vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1

            bytes_per_time_step = n_atoms * 4

            number_of_time_steps_written = \
                number_of_bytes_written / bytes_per_time_step

            ms_per_timestep = machine_time_step / 1000.0

            logger.debug("Processing {} timesteps"
                         .format(number_of_time_steps_written))

            temp_buffer = bytearray()

            current_pointer = 0
            for region_block in neuron_param_region_data:
                size = len(region_block)
                temp_buffer.extend(region_block)

            # Standard fixed-point 'accum' type scaling
            size = len(temp_buffer) / 4
            scale = numpy.zeros(size, dtype=numpy.float)
            scale.fill(float(0x7FFF))

            # Add an array for time and neuron id
            time = numpy.array([(int(i / n_atoms) * ms_per_timestep)
                                for i in range(size)], dtype=numpy.float)

            lo_atom = vertex_slice.lo_atom
            neuron_id = numpy.array([int(i % n_atoms) +
                                     lo_atom for i in range(size)],
                                    dtype=numpy.uint32)
            # Get the values
            # noinspection PyNoneFunctionAssignment
            temp_value = numpy.frombuffer(temp_buffer, dtype="<i4")
            # noinspection PyTypeChecker
            temp_value = numpy.divide(temp_value, scale)
            temp_array = numpy.dstack((time, neuron_id, temp_value))
            temp_array = numpy.reshape(temp_array, newshape=(-1, 3))
            value = numpy.append(value, temp_array, axis=0)

        logger.debug("Arranging parameter output")
        if compatible_output:

            # Change the order to be neuronID : time (don't know why - this
            # is how it was done in the old code, so I am doing it here too)
            value[:, [0, 1, 2]] = value[:, [1, 0, 2]]

            # Sort by neuron ID and not by time
            v_index = numpy.lexsort((value[:, 2], value[:, 1], value[:, 0]))
            value = value[v_index]
            return value

        # If not compatible output, we will sort by time (as NEST seems to do)
        v_index = numpy.lexsort((value[:, 2], value[:, 1], value[:, 0]))
        value = value[v_index]
        return value