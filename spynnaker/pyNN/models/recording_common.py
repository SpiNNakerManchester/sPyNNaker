from spinn_utilities import logger_utils
from spinn_front_end_common.utilities import exceptions as fec_excceptions
from spinn_front_end_common.utilities import globals_variables

from spynnaker.pyNN.models.common import AbstractSpikeRecordable
from spynnaker.pyNN.models.common import AbstractNeuronRecordable
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance

from collections import defaultdict
import numpy
import logging

logger = logging.getLogger(__name__)


class RecordingCommon(object):
    def __init__(self, population, sampling_interval=None):
        """ object to hold recording behaviour

        :param population: the population to record for
        :param simulator: the spinnaker control class
        """

        self._population = population

        self._sampling_interval = None
        if sampling_interval is not None:
            self._sampling_interval = sampling_interval

        # file flags, allows separate files for the recorded variables
        self._write_to_files_indicators = {
            'spikes': None,
            'gsyn_exc': None,
            'gsyn_inh': None,
            'v': None}

        # Create default dictionary of population-size filters
        self._indices_to_record = self._create_full_filter_list(0)

    def _record(self, variable, new_ids, sampling_interval, to_file):
        """ tells the vertex to record data

        :param variable: the variable to record, valued variables to record
        are: 'gsyn_exc', 'gsyn_inh', 'v', 'spikes'
        :param new_ids:  ids to record
        :param sampling_interval: the interval to record them
        :return:  None
        """

        # tell vertex its recording
        if variable == "spikes":
            self._set_spikes_recording()
        elif variable == "all":
            self._set_spikes_recording()
            self._population._vertex.set_recording(variable)
        else:
            self._population._vertex.set_recording(variable)

        # update file writer
        self._write_to_files_indicators[variable] = to_file

        # Get bit array of indices to record for this variable
        indices = self._indices_to_record[variable]

        # update sampling interval
        if sampling_interval is not None:
            self._sampling_interval = sampling_interval

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
                      "from a model which does not use conductance input.  " \
                      "You will receive current measurements instead."
                logger_utils.warn_once(logger, msg)
        elif variable == "gsyn_inh":
            if not isinstance(self._population._vertex.input_type,
                              InputTypeConductance):
                msg = "You are trying to record the excitatory conductance " \
                      "from a model which does not use conductance input.  " \
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

    @property
    def sampling_interval(self):
        """ forced by the public nature of pynn variables

        :return:
        """

        return self._sampling_interval

    @sampling_interval.setter
    def sampling_interval(self, new_value):
        """ forced by the public nature of pynn variables

        :param new_value: new value for the sampling_interval
        :return: None
        """
        self._sampling_interval = new_value

    def _get_recorded_variable(self, variable):
        """ method that contains all the safety checks and gets the recorded
        data from the vertex

        :param variable: the variable name to read. supported variable names
        are :'gsyn_exc', 'gsyn_inh', 'v', 'spikes'
        :return: the data
        """

        if variable == "spikes":
            return self._get_spikes()

        # check that we're ina  state to get voltages
        if isinstance(
                self._population._vertex, AbstractNeuronRecordable):
            if not self._population._vertex.is_recording(variable):
                raise fec_excceptions.ConfigurationException(
                    "This population has not been set to record {}"
                    "".format(variable))
        else:
            raise fec_excceptions.ConfigurationException(
                "This population has not got the capability to record {}"
                "".format(variable))

        if not globals_variables.get_simulator().has_ran:
            logger.warn(
                "The simulation has not yet run, therefore {} cannot"
                " be retrieved, hence the list will be empty "
                "".format(variable))
            return numpy.zeros((0, 3))

        if globals_variables.get_simulator().use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 3))

            # assuming we got here, everything is ok, so we should go get the
            # voltages
        return self._population._vertex.get_data(
            variable,
            globals_variables.get_simulator().no_machine_time_steps,
            globals_variables.get_simulator().placements,
            globals_variables.get_simulator().graph_mapper,
            globals_variables.get_simulator().buffer_manager,
            globals_variables.get_simulator().machine_time_step)

    def _get_spikes(self):
        """ method for getting spikes from a vertex

        :return: the spikes from a vertex
        """

        # check we're in a state where we can get spikes
        if isinstance(self._population._vertex, AbstractSpikeRecordable):
            if not self._population._vertex.is_recording_spikes():
                raise fec_excceptions.ConfigurationException(
                    "This population has not been set to record spikes")
        else:
            raise fec_excceptions.ConfigurationException(
                "This population has not got the capability to record spikes")

        if not globals_variables.get_simulator().has_ran:
            logger.warn(
                "The simulation has not yet run, therefore spikes cannot"
                " be retrieved, hence the list will be empty")
            return numpy.zeros((0, 2))

        if globals_variables.get_simulator().use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 2))

        # assuming we got here, everything is ok, so we should go get the
        # spikes
        return self._population._vertex.get_spikes(
            globals_variables.get_simulator().placements,
            globals_variables.get_simulator().graph_mapper,
            globals_variables.get_simulator().buffer_manager,
            globals_variables.get_simulator().machine_time_step)

    def _create_full_filter_list(self, filter_value):
        # Create default dictionary of population-size boolean arrays
        return defaultdict(
            lambda: numpy.repeat(filter_value, self._population.size).astype(
                "bool"))

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
