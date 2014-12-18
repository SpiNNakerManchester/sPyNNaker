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

    @abstractmethod
    def is_recordable(self):
        """helper method for is isinstance"""

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

        spike_times = list()
        spike_ids = list()
        ms_per_tick = self._machine_time_step / 1000.0

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

            # check that the number of spikes written is smaller or the same as
            #  the size of the memory region we allocated for spikes
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
            spike_data = transciever.read_memory(
                x, y, spike_region_base_address + 4, number_of_bytes_written)

            data_list = bytearray()
            for data in spike_data:
                data_list.extend(data)

            numpy_data = numpy.asarray(data_list, dtype="uint8").view(
                dtype="<i4").byteswap().view("uint8")
            bits = numpy.fliplr(numpy.unpackbits(numpy_data).reshape(
                (-1, 32))).reshape((-1, out_spike_bytes * 8))
            indices = [numpy.add(numpy.where(items)[0], lo_atom)
                       for items in bits]
            times = [numpy.repeat(i * ms_per_tick, len(indices[i]))
                     for i in range(len(indices))]
            spike_ids.extend([item for sublist in indices for item in sublist])
            spike_times.extend([item for sublist in times for item in sublist])

        result = numpy.dstack((spike_ids, spike_times))[0]
        result = result[numpy.lexsort((spike_times, spike_ids))]

        return result

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
