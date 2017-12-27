from __future__ import division
from collections import OrderedDict
import logging
import math
import numpy

from spinn_utilities.progress_bar import ProgressBar
from data_specification.enums import DataType
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spinn_front_end_common.utilities import exceptions as fec_excceptions
from spinn_front_end_common.utilities import globals_variables

logger = logging.getLogger(__name__)

MAX_RATE = 2 ** 32 - 1  # To allow a unit32_t to be used to store the rate


class NeuronRecorder(object):
    N_BYTES_PER_NEURON = 4
    N_BYTES_FOR_TIMESTAMP = 4
    N_CPU_CYCLES_PER_NEURON = 4

    def __init__(self, allowed_variables, n_neurons):
        self._sampling_rates = OrderedDict()
        self._n_neurons = n_neurons
        for variable in allowed_variables:
            self._sampling_rates[variable] = 0

    def n_neurons_recording(self, variable, vertex_slice):
        return vertex_slice.n_atoms

    def neurons_recording(self, variable, vertex_slice):
        return range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1)

    def get_neuron_sampling_interval(self, variable):
        """
        Returns the current sampling interval for this variable
        :param variable: PyNN name of the variable
        :return: Sampling interval in micro seconds
        """
        return self._sampling_rates[variable]

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
        sampling_interval = self._sampling_rates[variable]
        expected_rows = int(math.ceil(
            n_machine_time_steps / sampling_interval))
        missing_str = ""
        data = None
        indexes = []
        for vertex in progress.over(vertices):
            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)
            neurons = self.neurons_recording(variable, vertex_slice)
            n_neurons = len(neurons)
            indexes.extend(neurons)
            # for buffering output info is taken form the buffer manager
            neuron_param_region_data_pointer, missing_data = \
                buffer_manager.get_data_for_vertex(
                    placement, region)
            record_raw = neuron_param_region_data_pointer.read_all()
            record_length = len(record_raw)
            row_length = (n_neurons + 1) * self.N_BYTES_PER_NEURON
            # There is one column for time and one for each neuron recording
            n_rows = record_length // row_length
            # Converts bytes to ints and make a matrix
            record = (numpy.asarray(record_raw, dtype="uint8").
                      view(dtype="<i4")).reshape((n_rows, (n_neurons + 1)))
            # Check if you have the expected data
            if missing_data or n_rows != expected_rows:
                missing_str += "({}, {}, {}); ".format(
                    placement.x, placement.y, placement.p)
                # Start the fragment for this slice empty
                fragment = numpy.empty((expected_rows, n_neurons))
                for i in xrange(0, expected_rows):
                    time = i * sampling_interval
                    # Check if there is data for this timestep
                    indexes = numpy.where(record[:, 0] == time)
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
        return (data, indexes, sampling_interval)

    def get_recordable_variables(self):
        return self._sampling_rates.keys()

    def is_recording(self, variable):
        return self._sampling_rates[variable] > 0

    @property
    def recording_variables(self):
        results = list()
        for key in self._sampling_rates:
            if self.is_recording(key):
                results.append(key)
        return results

    def set_recording(self, variable, new_state, sampling_interval=None):
        if variable == "all":
            for key in self._sampling_rates.keys():
                self.set_recording(key, new_state, sampling_interval)
        elif variable in self._sampling_rates:
            if new_state:
                if sampling_interval is None:
                    # Record every tick
                    self._sampling_rates[variable] = 1
                else:
                    step = globals_variables.get_simulator().\
                               machine_time_step / 1000
                    rate = int(sampling_interval / step)
                    if sampling_interval != rate * step:
                        msg = "sampling_interval {} is not an an integer " \
                              "multiple of the simulation timestep {}" \
                              "".format(sampling_interval, step)
                        raise fec_excceptions.ConfigurationException(msg)
                    if rate > MAX_RATE:
                        msg = "sampling_interval {} higher than max allowed " \
                              "which is {}" \
                              "".format(sampling_interval, step * MAX_RATE)
                        raise fec_excceptions.ConfigurationException(msg)
                    self._sampling_rates[variable] = rate
            else:
                self._sampling_rates[variable] = 0
        else:
            msg = "Variable {} is not supported ".format(variable)
            raise fec_excceptions.ConfigurationException(msg)

    def _count_recording_per_slice(self, variable, slice):
        if self._sampling_rates[variable] == 0:
            return 0
        return slice.n_atoms

    def get_buffered_sdram_per_timestep(self, variable, slice):
        """
        Returns the sdram used per timestep

        In the case where sampling is used it returns the average
        for recording and none recording based on the recording rate

        :param variable:
        :param slice:
        :return:
        """
        neuron_count = self._count_recording_per_slice(variable, slice)
        if neuron_count == 0:
            return 0
        rate = self._sampling_rates[variable]
        data_size = self.N_BYTES_PER_NEURON * neuron_count
        return (data_size + self.N_BYTES_FOR_TIMESTAMP) / rate

    def get_extra_buffered_sdram(self, variable, slice):
        """
        Returns the maximun extra sdram where sampling is used.

        The assumpt here is that the there has been a previous run which stop
        just before the recording timestep.

        Then it is run for one timestep so a whole row of data must fit.
        This method returns the cost for a whole row
        minus the average returned by get_buffered_sdram_per_timestep

        :param variable:
        :param slice:
        :return:
        """
        rate = self._sampling_rates[variable]
        if rate <= 1:
            # No sampling so get_buffered_sdram_per_timestep was correct
            return 0
        neuron_count = self._count_recording_per_slice(variable, slice)
        data_size = self.N_BYTES_PER_NEURON * neuron_count
        return (data_size + self.N_BYTES_FOR_TIMESTAMP) / rate * (rate - 1)

    def get_dtcm_usage_in_bytes(self):
        return self.N_BYTES_PER_NEURON * len(self.recording_variables)

    def get_n_cpu_cycles(self, n_neurons):
        return n_neurons * self.N_CPU_CYCLES_PER_NEURON * \
                len(self.recording_variables)

    def get_sdram_usage_for_global_parameters_in_bytes(self):
        return len(self._sampling_rates) * 4

    def get_global_parameters(self, slice):
        params = []
        for variable in self._sampling_rates:
            params.append(NeuronParameter(
                self._sampling_rates[variable], DataType.UINT32))
        return params

    def get_indexes_for_slice(self, variable, slice):
        neuron_count = self._count_recording_per_slice(variable, slice)
        indexes = numpy.empty(slice.n_atoms)
        index = 0
        for neuron in xrange(slice.lo_atom, slice.hi_atom+1):
            if self._sampling_rates[variable] > 0:
                indexes[neuron-slice.lo_atom] = index
                index += 1
            else:
                indexes[neuron-slice.lo_atom] = neuron_count
        return indexes
