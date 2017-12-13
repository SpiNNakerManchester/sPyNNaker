from spinn_utilities import logger_utils
from spinn_utilities.timer import Timer
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spinn_front_end_common.utilities import globals_variables

from spynnaker.pyNN.models.common import AbstractSpikeRecordable
from spynnaker.pyNN.models.common import AbstractNeuronRecordable
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance

from collections import defaultdict
import numpy
import logging

logger = logging.getLogger(__name__)


class RecordingCommon(object):
    def __init__(self, population):
        """ object to hold recording behaviour

        :param population: the population to record for
        :param simulator: the spinnaker control class
        """

        self._population = population

        # file flags, allows separate files for the recorded variables
        self._write_to_files_indicators = {
            'spikes': None,
            'gsyn_exc': None,
            'gsyn_inh': None,
            'v': None}

        # Create a dict of variable name -> bool array of indices in population
        # that are recorded (initially all False)
        self._indices_to_record = defaultdict(
            lambda: numpy.repeat(False, population.size))

    def _record(self, variable, new_ids, sampling_interval=None, to_file=None):
        """ tells the vertex to record data

        :param variable: the variable to record, valued variables to record
        are: 'gsyn_exc', 'gsyn_inh', 'v', 'spikes'
        :param new_ids:  ids to record
        :param sampling_interval: the interval to record them
        :return:  None
        """

        globals_variables.get_simulator().verify_not_running()
        # tell vertex its recording
        if variable == "spikes":
            self._set_spikes_recording()
        elif variable == "all":
            raise Exception("Illegal call with all")
        else:
            self._population._vertex.set_recording(
                variable, sampling_interval=sampling_interval)

        # update file writer
        self._write_to_files_indicators[variable] = to_file

        # Get bit array of indices to record for this variable
        indices = self._indices_to_record[variable]

        # Loop through the new ids
        for new_id in new_ids:
            # Convert to index
            new_index = self._population.id_to_index(new_id)

            # Set this bit in indices
            indices[new_index] = True

        if variable == "gsyn_exc":
            if not isinstance(self._population._vertex.input_type,
                              InputTypeConductance):
                msg = "You are trying to record the excitatory conductance " \
                      "from a model which does not use conductance input. " \
                      "You will receive current measurements instead."
                logger_utils.warn_once(logger, msg)
        elif variable == "gsyn_inh":
            if not isinstance(self._population._vertex.input_type,
                              InputTypeConductance):
                msg = "You are trying to record the excitatory conductance " \
                      "from a model which does not use conductance input. " \
                      "You will receive current measurements instead."
                logger_utils.warn_once(logger, msg)

    def _set_v_recording(self):
        """ sets the parameters etc that are used by the v recording

        :return: None
        """
        self._population._vertex.set_recording("v")

    def _set_spikes_recording(self):
        """ sets the parameters etc that are used by the spikes recording

        :return: None
        """
        if not isinstance(self._population._vertex, AbstractSpikeRecordable):
            raise Exception(
                "This population does not support the recording of spikes!")
        self._population._vertex.set_recording_spikes()

    @staticmethod
    def pynn7_format(data, ids, sampling_interval, data2=None):
        n_machine_time_steps = len(data)
        n_neurons = len(ids)
        column_length = n_machine_time_steps * n_neurons
        times = [i * sampling_interval
                 for i in xrange(0, n_machine_time_steps)]
        if data2 is None:
            pynn7 = numpy.empty((column_length, 3))
        else:
            pynn7 = numpy.empty((column_length, 4))
        pynn7[:, 0] = numpy.repeat(ids, n_machine_time_steps, 0).\
            reshape(1, column_length)
        pynn7[:, 1] = numpy.tile(times, n_neurons).\
            reshape(1, column_length)
        pynn7[:, 2] = numpy.transpose(data).reshape(1, column_length)
        if data2 is not None:
            pynn7[:, 3] = numpy.transpose(data2).reshape(1, column_length)
        return pynn7

    def _get_recorded_pynn7(self, variable):
        if variable == "spikes":
            data = self._get_spikes()

        (data, ids, sampling_interval) = self._get_recorded_matrix(variable)
        return self.pynn7_format(data, ids, sampling_interval)
        (data, ids, sampling_interval) = self._get_recorded_matrix(variable)
        return self.pynn7_format(data, ids, sampling_interval)

    def _get_recorded_matrix(self, variable):
        """ method that contains all the safety checks and gets the recorded
        data from the vertex in matrix format

        :param variable: the variable name to read. supported variable names
        are :'gsyn_exc', 'gsyn_inh', 'v'
        :return: the data
        """
        timer = Timer()
        timer.start_timing()
        data = None
        sim = get_simulator()

        globals_variables.get_simulator().verify_not_running()

        # check that we're in a state to get voltages
        if not isinstance(
                self._population._vertex, AbstractNeuronRecordable):
            raise ConfigurationException(
                "This population has not got the capability to record {}"
                .format(variable))

        if not self._population._vertex.is_recording(variable):
            raise ConfigurationException(
                "This population has not been set to record {}"
                .format(variable))

        if not sim.has_ran:
            logger.warn(
                "The simulation has not yet run, therefore {} cannot"
                " be retrieved, hence the list will be empty".format(
                    variable))
            data = numpy.zeros((0, 3))
            indexes = []
            sampling_interval = self._population._vertex.\
                get_sampling_interval(variable)
        elif sim.use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            data = numpy.zeros((0, 3))
            indexes = []
            sampling_interval = self._population._vertex.\
                get_neuron_sampling_interval(variable)
        else:
            # assuming we got here, everything is ok, so we should go get the
            # data
            results = self._population._vertex.get_data(
                variable, sim.no_machine_time_steps, sim.placements,
                sim.graph_mapper, sim.buffer_manager, sim.machine_time_step)
            (data, indexes, sampling_interval) = results

        get_simulator().add_extraction_timing(
            timer.take_sample())
        return (data, indexes, sampling_interval)

    def _get_spikes(self):
        """ method for getting spikes from a vertex

        :return: the spikes from a vertex
        """

        # check we're in a state where we can get spikes
        if not isinstance(self._population._vertex, AbstractSpikeRecordable):
            raise ConfigurationException(
                "This population has not got the capability to record spikes")
        if not self._population._vertex.is_recording_spikes():
            raise ConfigurationException(
                "This population has not been set to record spikes")

        sim = get_simulator()
        if not sim.has_ran:
            logger.warn(
                "The simulation has not yet run, therefore spikes cannot"
                " be retrieved, hence the list will be empty")
            return numpy.zeros((0, 2))

        if sim.use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 2))

        # assuming we got here, everything is ok, so we should go get the
        # spikes
        return self._population._vertex.get_spikes(
            sim.placements, sim.graph_mapper, sim.buffer_manager,
            sim.machine_time_step)

    def _turn_off_all_recording(self):
        """
        turns off recording, is used by a pop saying .record()
        :rtype: None
        """

        # check for standard record
        if isinstance(self._population._vertex, AbstractNeuronRecordable):
            self._population._vertex.set_recording("all", False)

        # check for spikes
        if isinstance(self._population._vertex, AbstractSpikeRecordable):
            self._population._vertex.set_recording_spikes(False)
