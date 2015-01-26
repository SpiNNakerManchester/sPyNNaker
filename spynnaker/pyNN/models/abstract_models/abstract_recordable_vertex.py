from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from spinnman.messages.eieio.eieio_message import EIEIOMessage

from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_comm_models.\
    abstract_buffer_sendable_partitionable_vertex import AbstractBufferSendableVertex
from spynnaker.pyNN.utilities.utility_calls \
    import get_region_base_address_offset
from spynnaker.pyNN.utilities import constants

from pacman.utilities import constants as pacman_constants

from spinnman.data.little_endian_byte_array_byte_reader import \
    LittleEndianByteArrayByteReader

import logging
import numpy
import struct
import math

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractRecordableVertex(AbstractBufferSendableVertex):
    """
    Underlying AbstractConstrainedVertex model for Neural Applications.
    """

    def __init__(self, machine_time_step, label, tag, port, address,
                 max_on_chip_memory_usage_for_recording, strip_sdp=False):
        AbstractBufferSendableVertex.__init__(
            self, tag, port, address, strip_sdp=strip_sdp)
        self._record = False
        self._record_v = False
        self._record_gsyn = False
        self._focus_level = None
        self._app_mask = pacman_constants.DEFAULT_MASK
        self._label = label
        self._machine_time_step = machine_time_step
        self._max_on_chip_memory_usage_for_recording = \
            max_on_chip_memory_usage_for_recording

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

    @abstractmethod
    def is_recordable(self):
        """helper method for is isinstance"""

    def get_recording_region_size(self, spike_region_size, bytes_per_timestep):
        """
        Gets the size of the spike buffer for a range of neurons and time steps
        ASSUMES one spike per timer tic per neuron. Buffers can support more...
        """
        if not self._record or self._no_machine_time_steps is None:
            return 0
        else:
            spike_region_size = \
                constants.RECORDING_ENTRY_BYTE_SIZE + spike_region_size
            if spike_region_size > self._max_on_chip_memory_usage_for_recording:
                self._will_send_buffers = True
                self._recording_region_size_in_bytes = \
                    self._max_on_chip_memory_usage_for_recording
                return self._max_on_chip_memory_usage_for_recording
            else:
                self._recording_region_size_in_bytes = spike_region_size
                return spike_region_size

    def _get_spikes(
            self, graph_mapper, placements, transciever, compatible_output,
            spike_recording_region, buffer_manager):
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
                transciever.get_cpu_information_from_core(x, y, p).user[0]

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

            if number_of_bytes_written > self._recording_region_size_in_bytes:
                raise exceptions.MemReadException(
                    "the amount of memory written ({}) was larger than was "
                    "allocated for it ({})"
                    .format(number_of_bytes_written,
                            self._recording_region_size_in_bytes))

            # Read the spikes
            logger.debug("Reading {} ({}) bytes starting at {} + 4"
                         .format(number_of_bytes_written,
                                 hex(number_of_bytes_written),
                                 hex(spike_region_base_address)))
            buffer_data = transciever.read_memory_return_byte_array(
                x, y, spike_region_base_address + 4, number_of_bytes_written)
            #turn buffers into eieio data messages
            little_endian_byte_reader =\
                LittleEndianByteArrayByteReader(buffer_data)
            eieio_messages = \
                EIEIOMessage.create_eieio_messages_from(little_endian_byte_reader)

            # interpret each message into spikes
            for message in eieio_messages:
                spikes = self._turn_message_info_spike_train(
                    spikes, message,
                    graph_mapper.get_subvertex_slice(subvertex).lo_atom)

        if len(spikes) > 0:
            logger.debug("Arranging spikes as per output spec")

            if compatible_output:
                # Change the order to be neuronID : time (don't know why - this
                # is how it was _done in the old code, so I am doing it here too)
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

    def _turn_message_info_spike_train(self, spikes, message, lo_atom):
        """ turns a message into a collection of spikes and appends to a
        numpy array param

        :param spikes: the numpy array to append to
        :param message: the message to interpret
        :type spikes: numpy array
        :type message: a EIEIOMessage
        :return: the appended numpi array
        :rtype: numpy array
        """
        timer_tic = message.eieio_header.payload_base
        #turn into numpy array of shorts (2 bytes, each representing neuron id)
        core_based_neuron_ids = numpy.frombuffer(message.data, dtype="<i2")
        #translate into the neuron id the pop understands
        pop_based_neuron_ids = numpy.add(core_based_neuron_ids, lo_atom)
        pop_based_neuron_ids_with_timer = \
            numpy.zeros((len(pop_based_neuron_ids), 2))
        pop_based_neuron_ids_with_timer[:, 1] = pop_based_neuron_ids
        pop_based_neuron_ids_with_timer[:, 0].fill(timer_tic)
        return spikes.append(pop_based_neuron_ids_with_timer)

    def get_neuron_parameter(
            self, region, compatible_output, has_ran, graph_mapper, placements,
            txrx, machine_time_step):
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore neuron param "
                "cannot be retrieved")

        times = numpy.zeros(0)
        ids = numpy.zeros(0)
        values = numpy.zeros(0)
        ms_per_tick = self._machine_time_step / 1000.0

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

            logger.debug("Processing {} timesteps"
                         .format(number_of_time_steps_written))

            data_list = bytearray()
            for data in neuron_param_region_data:
                data_list.extend(data)

            numpy_data = numpy.asarray(data_list, dtype="uint8").view(
                dtype="<i4") / 32767.0
            values = numpy.append(values, numpy_data)
            times = numpy.append(
                times, numpy.repeat(range(numpy_data.size / n_atoms),
                                    n_atoms) * ms_per_tick)
            ids = numpy.append(ids, numpy.add(
                numpy.arange(numpy_data.size) % n_atoms, vertex_slice.lo_atom))

        result = numpy.dstack((ids, times, values))[0]
        result = result[numpy.lexsort((times, ids))]
        return result

    
    @abstractmethod
    def is_recordable(self):
        return True

    def is_buffer_sendable_vertex(self):
        return True