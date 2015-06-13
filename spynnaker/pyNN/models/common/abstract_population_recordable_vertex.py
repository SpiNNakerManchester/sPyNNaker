from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import constants

from pacman.utilities.progress_bar import ProgressBar

from data_specification import utility_calls as dsg_utility_calls

import logging
import numpy
import struct
from collections import OrderedDict

logger = logging.getLogger(__name__)


class AbstractPopulationRecordableVertex(object):
    """ Neural recording
    """

    def __init__(self, label, machine_time_step):
        self._record_v = False
        self._record_gsyn = False
        self._label = label
        self._machine_time_step = machine_time_step
        self._population_recordable_subvertices = OrderedDict()

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

    def add_population_recordable_subvertex(self, subvertex, vertex_slice):
        """ Used to keep track of the population recordable subvertices of this
            vertex, to allow the retrieving of the recorded data
        """
        self._population_recordable_subvertices[subvertex] = vertex_slice

    @staticmethod
    def _get_parameter_recording_region_size(n_machine_time_steps,
                                             vertex_slice):
        """ Get the size of a parameter recording region in bytes
        """
        return (constants.RECORDING_ENTRY_BYTE_SIZE +
                (n_machine_time_steps * vertex_slice.n_atoms * 4))

    @staticmethod
    def get_v_recording_region_size(n_machine_time_steps, vertex_slice):
        return AbstractPopulationRecordableVertex.\
            _get_parameter_recording_region_size(
                n_machine_time_steps, vertex_slice)

    @staticmethod
    def get_gsyn_recording_region_size(n_machine_time_steps, vertex_slice):
        return AbstractPopulationRecordableVertex.\
            _get_parameter_recording_region_size(
                n_machine_time_steps, vertex_slice)

    def _get_neuron_parameter(
            self, get_region_function, parameter_name, placements, transceiver,
            compatible_output, n_machine_timesteps):

        times = numpy.zeros(0)
        ids = numpy.zeros(0)
        values = numpy.zeros(0)
        ms_per_tick = self._machine_time_step / 1000.0

        # Find all the sub-vertices that this pynn_population.py exists on
        progress_bar = ProgressBar(
            len(self._population_recordable_subvertices),
            "Getting {}".format(parameter_name))
        for subvertex, vertex_slice in self._population_recordable_subvertices:
            placment = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placment.x, placment.y, placment.p

            # Get the App Data for the core
            app_data_base_address = transceiver.get_cpu_information_from_core(
                x, y, p).user[0]

            # Get the position of the value buffer
            region = get_region_function(subvertex)
            neuron_param_region_base_address_offset = \
                dsg_utility_calls.get_region_base_address_offset(
                    app_data_base_address, region)
            neuron_param_region_base_address_buf = str(list(
                transceiver.read_memory(
                    x, y, neuron_param_region_base_address_offset, 4))[0])
            neuron_param_region_base_address = struct.unpack(
                "<I", neuron_param_region_base_address_buf)[0]
            neuron_param_region_base_address += app_data_base_address

            # Read the size
            number_of_bytes_written_buf = str(list(transceiver.read_memory(
                x, y, neuron_param_region_base_address, 4))[0])

            number_of_bytes_written = struct.unpack_from(
                "<I", number_of_bytes_written_buf)[0]

            # check that the number of bytes written is smaller or the same as
            # the size of the memory region we allocated for recording
            size_of_region = AbstractPopulationRecordableVertex.\
                _get_parameter_recording_region_size(
                    n_machine_timesteps, vertex_slice)
            if number_of_bytes_written > size_of_region:
                raise exceptions.MemReadException(
                    "the amount of memory written ({}) was larger than was "
                    "allocated for it ({})"
                    .format(number_of_bytes_written, size_of_region))

            # Read the values
            logger.debug("Reading {} ({}) bytes starting at {}".format(
                number_of_bytes_written, hex(number_of_bytes_written),
                hex(neuron_param_region_base_address + 4)))

            neuron_param_region_data = transceiver.read_memory(
                x, y, neuron_param_region_base_address + 4,
                number_of_bytes_written)

            bytes_per_time_step = vertex_slice.n_atoms * 4

            number_of_time_steps_written = (number_of_bytes_written /
                                            bytes_per_time_step)

            logger.debug("Processing {} timesteps"
                         .format(number_of_time_steps_written))

            data_list = bytearray()
            for data in neuron_param_region_data:
                data_list.extend(data)

            numpy_data = numpy.asarray(data_list, dtype="uint8").view(
                dtype="<i4") / 32767.0
            values = numpy.append(values, numpy_data)
            times = numpy.append(
                times, numpy.repeat(range(numpy_data.size /
                                          vertex_slice.n_atoms),
                                    vertex_slice.n_atoms) * ms_per_tick)
            ids = numpy.append(ids, numpy.add(
                numpy.arange(numpy_data.size) % vertex_slice.n_atoms,
                vertex_slice.lo_atom))
            progress_bar.update()

        progress_bar.end()
        result = numpy.dstack((ids, times, values))[0]
        result = result[numpy.lexsort((times, ids))]
        return result

    def get_v(self, placements, transceiver, compatible_output,
              n_machine_timesteps):
        return self._get_neuron_parameter(
            lambda subvertex: subvertex.get_v_recording_region(),
            "membrane voltage", placements, transceiver, compatible_output,
            n_machine_timesteps)

    def get_gsyn(self, placements, transceiver, compatible_output,
                 n_machine_timesteps):
        return self._get_neuron_parameter(
            lambda subvertex: subvertex.get_gsyn_recording_region(),
            "conductance", placements, transceiver, compatible_output,
            n_machine_timesteps)
