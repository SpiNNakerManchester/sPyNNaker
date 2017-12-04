import logging
import numpy

from data_specification.enums import DataType
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils
from spinn_front_end_common.utilities import exceptions as fec_excceptions
from spinn_front_end_common.utilities import globals_variables

logger = logging.getLogger(__name__)


class NeuronRecorder(object):
    N_BYTES_PER_NEURON = 4
    N_CPU_CYCLES_PER_NEURON = 4

    def __init__(self, allowed_variables):
        self._record = dict()
        for variable in allowed_variables:
            self._record[variable] = False

    def n_neurons_recording(self, variable, vertex_slice):
        return vertex_slice.n_atoms

    def neurons_recording(self, variable, vertex_slice):
        return range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1)

    def sampling_interval(self, variable):
        return globals_variables.get_simulator().machine_time_step

    def get_matrix_data(
            self, label, buffer_manager, region, placements, graph_mapper,
            application_vertex, variable, n_machine_time_steps):
        """ method for reading a uint32 mapped to time and neuron ids from\
        the SpiNNaker machine

        :param label: vertex label
        :param buffer_manager: the manager for buffered data
        :param region: the dsg region id used for this data
        :param placements: the placements object
        :param graph_mapper: the mapping between application and machine\
            vertices
        :param application_vertex:
        :param variable: PyNN name for the variable (V, gsy_ihn ect
        :type variable: str
        :param n_machine_time_steps:
        :return:
        """
        vertices = graph_mapper.get_machine_vertices(application_vertex)
        progress = ProgressBar(
                vertices, "Getting {} for {}".format(variable, label))
        sampling_interval = self.sampling_interval(variable)
        missing_str = ""
        data = None
        ids = []
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)
            neurons = self.neurons_recording(variable, vertex_slice)
            n_neurons = len(neurons)
            ids.extend(neurons)
            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, missing_data = \
                buffer_manager.get_data_for_vertex(
                    placement, region)
            record_raw = neuron_param_region_data_pointer.read_all()
            record_length = len(record_raw)
            row_length = (n_neurons + 1) * self.N_BYTES_PER_NEURON
            # There is one column for time and one for each neuron recording
            n_rows = record_length / row_length
            # Converts bytes to ints and make a matrix
            record = (numpy.asarray(record_raw, dtype="uint8").
                      view(dtype="<i4")).reshape((n_rows, (n_neurons + 1)))
            # Check if you have the expected data
            if missing_data or n_rows != n_machine_time_steps:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
                # Start the fragment for this slice empty
                fragment = numpy.empty((n_machine_time_steps, n_neurons))
                for i in xrange(0, n_machine_time_steps):
                    timestep = i * sampling_interval
                    # Check if there is data for this timestep
                    indexes = numpy.where(record[:, 0] == timestep)
                    if len(indexes[0]) > 0:
                        # Set row to data for that timestep
                        fragment[i] = record[indexes[0][0], 1:]
                    else:
                        # Set row to nan
                        fragment[i] = numpy.full(n_neurons, numpy.nan)
            else:
                # Just cut the timestamps off to get the fragment
                fragment = (record[:, 1:] / float(DataType.S1615.scale))
            if data is None:
                data = fragment
            else:
                # Add the slice fragment on axis 1 which is ids/ channel_index
                data = numpy.append(data, fragment, axis=1)
        return (data, ids, sampling_interval)

    def get_recordable_variables(self):
        return self._record.keys()

    def is_recording(self, variable):
        if variable in self._record:
            return self._record[variable]
        msg = "Variable {} is not supported. Supported variables include {}" \
              "".format(variable, self._record.keys())
        raise fec_excceptions.ConfigurationException(msg)

    @property
    def recording_variables(self):
        results = list()
        for key, value in self._record.iteritems():
            if value:
                results.append(key)
        return results

    def set_recording(self, variable, new_state):
        if variable == "all":
            for key in self._record.keys():
                self._record[key] = new_state
        elif variable in self._record:
            self._record[variable] = new_state
        else:
            msg = "Variable {} is not supported ".format(variable)
            raise fec_excceptions.ConfigurationException(msg)

    def get_sdram_usage_in_bytes(self, variable, n_neurons,
                                 n_machine_time_steps):
        if self.is_recording(variable):
            return recording_utils.get_recording_region_size_in_bytes(
                n_machine_time_steps,  self.N_BYTES_PER_NEURON * n_neurons)
        else:
            return 0

    def get_dtcm_usage_in_bytes(self):
        return self.N_BYTES_PER_NEURON * sum(self._record.values())

    def get_n_cpu_cycles(self, n_neurons):
        return n_neurons * self.N_CPU_CYCLES_PER_NEURON * \
                sum(self._record.values())
