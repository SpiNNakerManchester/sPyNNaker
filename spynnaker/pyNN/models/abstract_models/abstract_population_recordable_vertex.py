from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import constants as local_constants

from pacman.utilities import constants as pacman_constants
from pacman.utilities.progress_bar import ProgressBar

from pacman.model.partitionable_graph.receive_buffers_to_host_partitionable_vertex import \
    ReceiveBuffersToHostPartitionableVertex

from data_specification import utility_calls as dsg_utility_calls

import logging
import numpy
import struct
import tempfile
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPopulationRecordableVertex(
        ReceiveBuffersToHostPartitionableVertex):
    """ Neural recording
    """

    def __init__(self, machine_time_step, label):
        ReceiveBuffersToHostPartitionableVertex.__init__(self)
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

    @property
    def record_v(self):
        return self._record_v

    @property
    def record_gsyn(self):
        return self._record_gsyn

    def set_record(self, setted_value):
        """
        method that sets the vertex to be recordable, """
        self._record = setted_value
        self.set_buffering_output()

    def set_record_v(self, setted_value):
        self._record_v = setted_value
        self.set_buffering_output()

    def set_record_gsyn(self, setted_value):
        self._record_gsyn = setted_value
        self.set_buffering_output()

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

        spike_times = list()
        spike_ids = list()
        ms_per_tick = self._machine_time_step / 1000.0

        # Find all the sub-vertices that this pynn_population.py exists on
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        progress_bar = ProgressBar(
            len(subvertices), "Getting spikes for {}".format(self._label))
        for subvertex in subvertices:
            placement = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placement.x, placement.y, placement.p
            subvertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            lo_atom = subvertex_slice.lo_atom
            hi_atom = subvertex_slice.hi_atom

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
            spike_region_base_address_buf = buffer(transceiver.read_memory(
                x, y, spike_region_base_address_offset, 4))
            spike_region_base_address = struct.unpack_from(
                "<I", spike_region_base_address_buf)[0]
            spike_region_base_address += app_data_base_address

            # Read the spike data size
            number_of_bytes_written_buf = buffer(transceiver.read_memory(
                x, y, spike_region_base_address, 4))
            number_of_bytes_written = struct.unpack_from(
                "<I", number_of_bytes_written_buf)[0]

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
            spike_data = transceiver.read_memory(
                x, y, spike_region_base_address + 4, number_of_bytes_written)
            numpy_data = numpy.asarray(spike_data, dtype="uint8").view(
                dtype="uint32").byteswap().view("uint8")
            bits = numpy.fliplr(numpy.unpackbits(numpy_data).reshape(
                (-1, 32))).reshape((-1, out_spike_bytes * 8))
            times, indices = numpy.where(bits == 1)
            times = times * ms_per_tick
            indices = indices + lo_atom
            spike_ids.append(indices)
            spike_times.append(times)
            progress_bar.update()

        progress_bar.end()
        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]

    def _get_v(
            self, region, compatible_output, has_ran, graph_mapper, placements,
            txrx, machine_time_step, runtime):
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore neuron param "
                "cannot be retrieved")

        ms_per_tick = self._machine_time_step / 1000.0
        n_timesteps = runtime / ms_per_tick

        tempfilehandle = tempfile.NamedTemporaryFile()
        data = numpy.memmap(
            tempfilehandle.file, shape=(n_timesteps, self._n_atoms),
            dtype="float64,float64,float64")
        data["f0"] = (numpy.arange(self._n_atoms * n_timesteps) %
                      self._n_atoms).reshape((n_timesteps, self._n_atoms))
        data["f1"] = numpy.repeat(numpy.arange(0, n_timesteps * ms_per_tick,
                                  ms_per_tick), self._n_atoms).reshape(
                                      (n_timesteps, self._n_atoms))

        # Find all the sub-vertices that this pynn_population.py exists on
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        progress_bar = ProgressBar(
            len(subvertices), "Getting recorded v for {}".format(self._label))
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
            neuron_param_region_base_address_buf = buffer(txrx.read_memory(
                x, y, neuron_param_region_base_address_offset, 4))
            neuron_param_region_base_address = struct.unpack_from(
                "<I", neuron_param_region_base_address_buf)[0]
            neuron_param_region_base_address += app_data_base_address

            # Read the size
            number_of_bytes_written_buf = buffer(txrx.read_memory(
                x, y, neuron_param_region_base_address, 4))

            number_of_bytes_written = struct.unpack_from(
                "<I", number_of_bytes_written_buf)[0]

            # Read the values
            logger.debug("Reading {} ({}) bytes starting at {}".format(
                number_of_bytes_written, hex(number_of_bytes_written),
                hex(neuron_param_region_base_address + 4)))

            neuron_param_region_data = txrx.read_memory(
                x, y, neuron_param_region_base_address + 4,
                number_of_bytes_written)

            vertex_slice = graph_mapper.get_subvertex_slice(subvertex)

            bytes_per_time_step = vertex_slice.n_atoms * 4

            number_of_time_steps_written = \
                number_of_bytes_written / bytes_per_time_step

            logger.debug("Processing {} timesteps"
                         .format(number_of_time_steps_written))

            numpy_data = (numpy.asarray(
                neuron_param_region_data, dtype="uint8").view(dtype="<i4") /
                32767.0).reshape((n_timesteps, vertex_slice.n_atoms))
            data["f2"][:, vertex_slice.lo_atom:vertex_slice.hi_atom + 1] =\
                numpy_data
            progress_bar.update()

        progress_bar.end()
        data.shape = self._n_atoms * n_timesteps

        # Sort the data - apparently, using lexsort is faster, but it might
        # consume more memory, so the option is left open for sort-in-place
        order = numpy.lexsort((data["f1"], data["f0"]))
        # data.sort(order=['f0', 'f1'], axis=0)

        result = data.view(dtype="float64").reshape(
            (self._n_atoms * n_timesteps, 3))[order]
        return result

    def _get_gsyn(
            self, region, compatible_output, has_ran, graph_mapper, placements,
            txrx, machine_time_step, runtime):
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore neuron param "
                "cannot be retrieved")

        ms_per_tick = self._machine_time_step / 1000.0
        n_timesteps = runtime / ms_per_tick

        tempfilehandle = tempfile.NamedTemporaryFile()
        data = numpy.memmap(
            tempfilehandle.file, shape=(n_timesteps, self._n_atoms),
            dtype="float64,float64,float64,float64")
        data["f0"] = (numpy.arange(self._n_atoms * n_timesteps) %
                      self._n_atoms).reshape((n_timesteps, self._n_atoms))
        data["f1"] = numpy.repeat(numpy.arange(0, n_timesteps * ms_per_tick,
                                  ms_per_tick), self._n_atoms).reshape(
                                      (n_timesteps, self._n_atoms))

        # Find all the sub-vertices that this pynn_population.py exists on
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        progress_bar = ProgressBar(
            len(subvertices), "Getting recorded gsyn for {}".format(
                self._label))
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
            neuron_param_region_base_address_buf = buffer(txrx.read_memory(
                x, y, neuron_param_region_base_address_offset, 4))
            neuron_param_region_base_address = struct.unpack_from(
                "<I", neuron_param_region_base_address_buf)[0]
            neuron_param_region_base_address += app_data_base_address

            # Read the size
            number_of_bytes_written_buf = buffer(txrx.read_memory(
                x, y, neuron_param_region_base_address, 4))

            number_of_bytes_written = struct.unpack_from(
                "<I", number_of_bytes_written_buf)[0]

            # Read the values
            logger.debug("Reading {} ({}) bytes starting at {}".format(
                number_of_bytes_written, hex(number_of_bytes_written),
                hex(neuron_param_region_base_address + 4)))

            neuron_param_region_data = txrx.read_memory(
                x, y, neuron_param_region_base_address + 4,
                number_of_bytes_written)

            vertex_slice = graph_mapper.get_subvertex_slice(subvertex)

            bytes_per_time_step = vertex_slice.n_atoms * 4

            number_of_time_steps_written = \
                number_of_bytes_written / bytes_per_time_step

            logger.debug("Processing {} timesteps"
                         .format(number_of_time_steps_written))

            numpy_data = (numpy.asarray(
                neuron_param_region_data, dtype="uint8").view(dtype="<i4") /
                32767.0).reshape((n_timesteps, vertex_slice.n_atoms * 2))
            data["f2"][:, vertex_slice.lo_atom:vertex_slice.hi_atom + 1] =\
                numpy_data[:, 0::2]
            data["f3"][:, vertex_slice.lo_atom:vertex_slice.hi_atom + 1] =\
                numpy_data[:, 1::2]
            progress_bar.update()

        progress_bar.end()
        data.shape = self._n_atoms * n_timesteps

        # Sort the data - apparently, using lexsort is faster, but it might
        # consume more memory, so the option is left open for sort-in-place
        order = numpy.lexsort((data["f1"], data["f0"]))
        # data.sort(order=['f0', 'f1'], axis=0)

        result = data.view(dtype="float64").reshape(
            (self._n_atoms * n_timesteps, 4))[order]
        return result
