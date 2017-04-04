from spinn_front_end_common.utilities import exceptions as fec_excceptions

from spynnaker.pyNN.models.common.abstract_gsyn_excitatory_recordable import \
    AbstractGSynExcitatoryRecordable
from spynnaker.pyNN.models.common.abstract_gsyn_inhibitory_recordable import \
    AbstractGSynInhibitoryRecordable
from spynnaker.pyNN.models.common.abstract_spike_recordable import \
    AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable import \
    AbstractVRecordable
from spynnaker.pyNN.models.neuron.input_types.input_type_conductance import \
    InputTypeConductance
from spynnaker.pyNN.utilities import globals_variables

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
        if variable == "gsyn_exc":
            self._set_gsyn_excitatory_recording()
        elif variable == "gsyn_inh":
            self._set_gsyn_inh_recording()
        elif variable == "v":
            self._set_v_recording()
        elif variable == "spikes":
            self._set_spikes_recording()
        elif variable == "all":
            self._set_gsyn_excitatory_recording()
            self._set_gsyn_inh_recording()
            self._set_v_recording()
            self._set_spikes_recording()
        else:
            raise fec_excceptions.ConfigurationException(
                "The variable {} is not supported by the record method. "
                "Currently supported variables are: 'gsyn_exc', 'gsyn_inh',"
                " 'v', 'spikes', 'all'".format(variable))

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

    def _set_gsyn_excitatory_recording(self):
        """ sets parameters etc that are used by the gsyn exc recording

        :return: None
        """
        if not isinstance(
                self._population._vertex, AbstractGSynExcitatoryRecordable):
            raise Exception(
                "This population does not support the recording of gsyn exc")
        if not isinstance(
                self._population._vertex.input_type, InputTypeConductance):
            logger.warn(
                "You are trying to record the excitatory conductance from a "
                "model which does not use conductance input.  You will "
                "receive current measurements instead.")

        self._population._vertex.set_recording_gsyn_excitatory()

    def _set_gsyn_inh_recording(self):
        """ sets parameters etc that are used by the gsyn inh recording

        :return: None
        """

        if not isinstance(
                self._population._vertex, AbstractGSynInhibitoryRecordable):
            raise Exception(
                "This population does not support the recording of "
                "inhibitory gsyn")
        if not isinstance(
                self._population._vertex.input_type, InputTypeConductance):
            logger.warn(
                "You are trying to record the inhibitory conductance from a "
                "model which does not use conductance input.  You will "
                "receive current measurements instead.")

        self._population._vertex.set_recording_gsyn_inhibitory()

    def _set_v_recording(self):
        """ sets the parameters etc that are used by the v recording

        :return: None
        """

        if not isinstance(self._population._vertex, AbstractVRecordable):
            raise Exception(
                "This population does not support the recording of v")

        self._population._vertex.set_recording_v()

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

        if variable == "gsyn_exc":
            return self._get_gsyn_excitatory()
        elif variable == "gsyn_inh":
            return self._get_gsyn_inhibitory()
        elif variable == "v":
            return self._get_v()
        elif variable == "spikes":
            return self._get_spikes()
        else:
            raise fec_excceptions.ConfigurationException(
                "The variable {} is not supported by the get method. "
                "Currently supported variables are: "
                "'gsyn_exc', 'gsyn_inh', 'v', 'spikes'".format(variable))

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

    def _get_v(self):
        """ get the voltage from the vertex

        :return: the voltages
        """

        # check that we're ina  state to get voltages
        if isinstance(self._population._vertex, AbstractVRecordable):
            if not self._population._vertex.is_recording_v():
                raise fec_excceptions.ConfigurationException(
                    "This population has not been set to record v")
        else:
            raise fec_excceptions.ConfigurationException(
                "This population has not got the capability to record v")

        if not globals_variables.get_simulator().has_ran:
            logger.warn(
                "The simulation has not yet run, therefore v cannot"
                " be retrieved, hence the list will be empty")
            return numpy.zeros((0, 3))

        if globals_variables.get_simulator().use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 3))

            # assuming we got here, everything is ok, so we should go get the
            # voltages
        return self._population._vertex.get_v(
            globals_variables.get_simulator().no_machine_time_steps,
            globals_variables.get_simulator().placements,
            globals_variables.get_simulator().graph_mapper,
            globals_variables.get_simulator().buffer_manager,
            globals_variables.get_simulator().machine_time_step)

    def _get_gsyn_excitatory(self):
        """ get the gsyn inh values from the vertex

        :return: the gsyn inh values
        """
        if isinstance(
                self._population._vertex, AbstractGSynExcitatoryRecordable):
            if not self._population._vertex.is_recording_gsyn_excitatory():
                raise fec_excceptions.ConfigurationException(
                    "This population has not been set to record gsyn "
                    "excitatory")
        else:
            raise fec_excceptions.ConfigurationException(
                "This population has not got the capability to record gsyn "
                "excitatory")

        if not globals_variables.get_simulator().has_ran:
            logger.warn(
                "The simulation has not yet run, therefore gsyn excitatory "
                "cannot be retrieved, hence the list will be empty")
            return numpy.zeros((0, 4))

        if globals_variables.get_simulator().use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 4))

        return self._population._vertex.get_gsyn_excitatory(
            globals_variables.get_simulator().no_machine_time_steps,
            globals_variables.get_simulator().placements,
            globals_variables.get_simulator().graph_mapper,
            globals_variables.get_simulator().buffer_manager,
            globals_variables.get_simulator().machine_time_step)

    def _get_gsyn_inhibitory(self):
        """ get the gsyn inhibitory values from the vertex

        :return: the gsyn inhibitory values
        """
        if isinstance(
                self._population._vertex, AbstractGSynInhibitoryRecordable):
            if not self._population._vertex.is_recording_gsyn_inhibitory():
                raise fec_excceptions.ConfigurationException(
                    "This population has not been set to record gsyn "
                    "inhibitory")
        else:
            raise fec_excceptions.ConfigurationException(
                "This population has not got the capability to record gsyn "
                "inhibitory")

        if not globals_variables.get_simulator().has_ran:
            logger.warn(
                "The simulation has not yet run, therefore gsyn inhibitory "
                "cannot be retrieved, hence the list will be empty")
            return numpy.zeros((0, 4))

        if globals_variables.get_simulator().use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 4))

        return self._population._vertex.get_gsyn_inhibitory(
            globals_variables.get_simulator().no_machine_time_steps,
            globals_variables.get_simulator().placements,
            globals_variables.get_simulator().graph_mapper,
            globals_variables.get_simulator().buffer_manager,
            globals_variables.get_simulator().machine_time_step)

    def _create_full_filter_list(self, filter_value):
        # Create default dictionary of population-size boolean arrays
        return defaultdict(
            lambda: numpy.repeat(filter_value, self._population.size).astype(
                "bool"))

    def _reset(self):
        self._population._vertex.set_recording_gsyn_excitatory(False)
        self._population._vertex.set_recording_gsyn_inhibitory(False)
        self._population._vertex.set_recording_spikes(False)
        self._population._vertex.set_recording_v(False)
