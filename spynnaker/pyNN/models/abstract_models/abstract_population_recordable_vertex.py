from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import constants as local_constants

from pacman.utilities import constants as pacman_constants
from pacman.utilities.progress_bar import ProgressBar

from data_specification import utility_calls as dsg_utility_calls


import logging
import numpy
import struct
from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPopulationRecordableVertex(object):
    """ Neural recording
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

    @abstractmethod
    def is_recordable(self):
        """helper method for is isinstance"""

    def get_recording_region_size(self, bytes_per_timestep):
        """
        Gets the size of a recording region in bytes
        """
        if self._no_machine_time_steps is None:
            raise Exception("This model cannot record this parameter"
                            " without a fixed run time")
        return (local_constants.RECORDING_ENTRY_BYTE_SIZE +
                (self._no_machine_time_steps * bytes_per_timestep))

    def _get_spikes(
            self, graph_mapper, placements, transceiver, compatible_output,
            spike_recording_region, sub_vertex_out_spike_bytes_function):
        """
        Return a 2-column numpy array containing cell ids and spike times for
        recorded cells.   This is read directly from the memory for the board.
        """

        logger.info("Getting spikes for {}".format(self._label))

        vert_spike_times = list()
        vert_spike_ids = list()
        ms_per_tick = self._machine_time_step / 1000.0

        # Find all the sub-vertices that this pynn_population.py exists on
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        progress_bar = ProgressBar(len(subvertices), "Getting spikes")
        for subvertex in subvertices:
            placement = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placement.x, placement.y, placement.p
            subvertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            lo_atom = subvertex_slice.lo_atom
            hi_atom = subvertex_slice.hi_atom
            n_atoms = hi_atom - lo_atom + 1

            logger.debug("Reading spikes from chip {}, {}, core {}, "
                         "lo_atom {} hi_atom {}".format(
                             x, y, p, lo_atom, hi_atom))

            # Get the App Data for the core
            app_data_base_address = \
                transceiver.get_cpu_information_from_core(x, y, p).user[0]

            # Get the position of the spike buffer
            spike_region_base_address_offset = \
                dsg_utility_calls.get_region_base_address_offset(
                    app_data_base_address, spike_recording_region)
            spike_region_base_address_buf = \
                str(list(transceiver.read_memory(
                    x, y, spike_region_base_address_offset, 4))[0])
            spike_region_base_address = \
                struct.unpack("<I", spike_region_base_address_buf)[0]
            spike_region_base_address += app_data_base_address

            # Read the spike data size
            number_of_bytes_written_buf =\
                str(list(transceiver.read_memory(
                    x, y, spike_region_base_address, 4))[0])
            number_of_bytes_written = \
                struct.unpack_from("<I", number_of_bytes_written_buf)[0]

            # check that the number of spikes written is smaller or the same as
            # the size of the memory region we allocated for spikes
            out_spike_bytes = sub_vertex_out_spike_bytes_function(
                subvertex, subvertex_slice)
            size_of_region = self.get_recording_region_size(out_spike_bytes)

            if number_of_bytes_written > size_of_region:
                raise exceptions.MemReadException(
                    "the amount of memory written ({}) was larger than was "
                    "allocated for it ({})"
                    .format(number_of_bytes_written, size_of_region))

            # Read the spikes
            logger.debug("Reading {} ({}) bytes starting at {} + 4"
                         .format(number_of_bytes_written,
                                 hex(number_of_bytes_written),
                                 hex(spike_region_base_address)))

            # Create numpy array to hold written data
            spike_bytes = numpy.empty(number_of_bytes_written, dtype="uint8")

            # Start reading spike data
            spike_data = transceiver.read_memory(
                x, y, spike_region_base_address + 4, number_of_bytes_written)

            # Loop through returned chunks
            chunk_start_offset = 0
            for chunk_data in spike_data:
                # Convert chunk to numpy array
                chunk_numpy = numpy.asarray(chunk_data, dtype="uint8")

                # Copy chunk into spike bytes
                chunk_length = len(chunk_numpy)
                chunk_end_offset = chunk_start_offset + chunk_length
                spike_bytes[chunk_start_offset:chunk_end_offset] = chunk_numpy
                chunk_start_offset += chunk_length

            # Swap endianess
            spike_bytes = (
                spike_bytes
                .view(dtype="uint32")
                .byteswap()
                .view(dtype="uint8")
            )

            # Unpack the bytes into bits, group these into words and flip order
            spike_bits = numpy.fliplr(
                numpy.reshape(numpy.unpackbits(spike_bytes), (-1, 32))
            )

            # Reshape the data into a out_spike_bytes column matrix
            spike_bits = numpy.reshape(spike_bits, (-1, out_spike_bytes * 8))

            # Slice out neurons that actually exist
            spike_bits = spike_bits[:, :n_atoms]

            # Find indices of where spikes have occurred
            spike_times, spike_ids = numpy.nonzero(spike_bits)

            # Scale spike times by timescale and add lo_atom index to neurons
            spike_times = spike_times * ms_per_tick
            spike_ids = spike_ids + lo_atom

            # Add to lists for the whole vertex
            vert_spike_times.append(spike_times)
            vert_spike_ids.append(spike_ids)
            progress_bar.update()

        progress_bar.end()

        # Stack together lists of spike times and ids
        vert_spike_times = numpy.hstack(vert_spike_times)
        vert_spike_ids = numpy.hstack(vert_spike_ids)

        # Stack and rotate these two arrays into column format
        result = numpy.dstack((vert_spike_ids, vert_spike_times))[0]

        # Sort and return
        return result[numpy.lexsort((vert_spike_times, vert_spike_ids))]

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
        progress_bar = ProgressBar(len(subvertices), "Getting recorded data")
        for subvertex in subvertices:
            placment = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placment.x, placment.y, placment.p

            # Get the App Data for the core
            app_data_base_address = txrx.\
                get_cpu_information_from_core(x, y, p).user[0]

            # Get the position of the value buffer
            neuron_param_region_base_address_offset = \
                dsg_utility_calls.get_region_base_address_offset(
                    app_data_base_address, region)
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
            n_atoms = vertex_slice.hi_atom - vertex_slice.lo_atom + 1

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
            progress_bar.update()

        progress_bar.end()
        result = numpy.dstack((ids, times, values))[0]
        result = result[numpy.lexsort((times, ids))]
        return result
