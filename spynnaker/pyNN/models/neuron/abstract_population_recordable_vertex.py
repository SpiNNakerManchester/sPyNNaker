from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.common.abstract_spike_recordable_vertex \
    import AbstractSpikeRecordableVertex


from pacman.utilities.progress_bar import ProgressBar

from data_specification import utility_calls as dsg_utility_calls

import logging
import numpy
import struct
import tempfile

logger = logging.getLogger(__name__)


class AbstractPopulationRecordableVertex(AbstractSpikeRecordableVertex):
    """ Neural recording
    """

    def __init__(self, label, machine_time_step):
        AbstractSpikeRecordableVertex.__init__(self, label, machine_time_step)
        self._record_v = False
        self._record_gsyn = False
        self._label = label
        self._machine_time_step = machine_time_step

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
        AbstractSpikeRecordableVertex.add_spike_recordable_subvertex(
            self, subvertex, vertex_slice)

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
            compatible_output, n_timesteps):

        ms_per_tick = self._machine_time_step / 1000.0

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
        progress_bar = ProgressBar(
            len(self._spike_recordable_subvertices),
            "Getting {} for {}".format(parameter_name, self._label))
        for subvertex, vertex_slice in self._spike_recordable_subvertices:
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
            neuron_param_region_base_address_buf = transceiver.read_memory(
                x, y, neuron_param_region_base_address_offset, 4)
            neuron_param_region_base_address = struct.unpack_from(
                "<I", neuron_param_region_base_address_buf)[0]
            neuron_param_region_base_address += app_data_base_address

            # Read the size
            number_of_bytes_written_buf = transceiver.read_memory(
                x, y, neuron_param_region_base_address, 4)

            number_of_bytes_written = struct.unpack_from(
                "<I", number_of_bytes_written_buf)[0]

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
