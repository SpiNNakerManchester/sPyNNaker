# Copyright (c) 2017-2021 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from datetime import datetime
import logging
import numpy
import neo
import quantities
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.ordered_set import OrderedSet
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.data_cache import DataCache
from spynnaker.pyNN.models.common import RecordingType

# needed as dealing with quantities
# pylint: disable=c-extension-no-member

logger = FormatAdapter(logging.getLogger(__name__))


class Recorder(object):
    """ Object to hold recording behaviour, used by populations.
    """

    __slots__ = [
        "__data_cache",
        "__population",
        "__recording_start_time",
        "__vertex",
        "__write_to_files_indicators"]

    def __init__(self, population, vertex):
        """
        :param ~spynnaker.pyNN.models.populations.Population population:
            the population to record for
        :param ~pacman.model.graphs.application.ApplicationVertex vertex:
            the SpiNNaker graph vertex used by the population
        """
        self.__population = population
        self.__vertex = vertex

        # file flags, allows separate files for the recorded variables
        self.__write_to_files_indicators = {
            'spikes': None,
            'gsyn_exc': None,
            'gsyn_inh': None,
            'v': None}
        self.__recording_start_time = \
            SpynnakerDataView.get_current_run_time_ms()
        self.__data_cache = {}

    @property
    def write_to_files_indicators(self):
        """ What variables should be written to files, and where should they\
            be written.

        :rtype: dict(str, neo.io.baseio.BaseIO or str or None)
        """
        return self.__write_to_files_indicators

    def record(self, variables, to_file, sampling_interval, indexes):
        """ Same as record but without non-standard PyNN warning

        This method is non-standard PyNN and is intended only to be called by
        record in a Population, View or Assembly

        :param variables: either a single variable name or a list of variable
            names. For a given celltype class, ``celltype.recordable`` contains
            a list of variables that can be recorded for that celltype.
            Can also be ``None`` to reset the list of variables.
        :type variables: str or list(str) or None
        :param to_file: a file to automatically record to (optional).
            :py:meth:`write_data` will be automatically called when
            `sim.end()` is called.
        :type to_file: ~neo.io or ~neo.rawio or str
        :param int sampling_interval: a value in milliseconds, and an integer
            multiple of the simulation timestep.
        :param indexes: The indexes of neurons to record from.
            This is non-standard PyNN and equivalent to creating a view with
            these indexes and asking the View to record.
        :type indexes: None or list(int)
        """
        if variables is None:  # reset the list of things to record
            if sampling_interval is not None:
                raise ConfigurationException(
                    "Clash between parameters in record."
                    "variables=None turns off recording,"
                    "while sampling_interval!=None implies turn on recording")
            if indexes is not None:
                warn_once(
                    logger,
                    "View.record with variable None is non-standard PyNN. "
                    "Only the neurons in the view have their record turned "
                    "off. Other neurons already set to record will remain "
                    "set to record")

            # note that if record(None) is called, its a reset
            self.turn_off_all_recording(indexes)
            # handle one element vs many elements
        elif isinstance(variables, str):
            # handle special case of 'all'
            if variables == "all":
                warn_once(
                    logger, 'record("all") is non-standard PyNN, and '
                    'therefore may not be portable to other simulators.')

                # iterate though all possible recordings for this vertex
                for variable in self.__vertex.get_recordable_variables():
                    self.turn_on_record(
                        variable, sampling_interval, to_file, indexes)
            else:
                # record variable
                self.turn_on_record(
                    variables, sampling_interval, to_file, indexes)

        else:  # list of variables, so just iterate though them
            for variable in variables:
                self.turn_on_record(
                    variable, sampling_interval, to_file, indexes)

    def turn_on_record(self, variable, sampling_interval=None, to_file=None,
                       indexes=None):
        """ Tell the vertex to record data.

        :param str variable: The variable to record, supported variables to
            record are: ``gsyn_exc``, ``gsyn_inh``, ``v``, ``spikes``.
        :param int sampling_interval: the interval to record them
        :param to_file: If set, a file to write to (by handle or name)
        :type to_file: neo.io.baseio.BaseIO or str or None
        :param indexes: List of indexes to record or None for all
        :type indexes: list(int) or None
        :raises SimulatorRunningException: If sim.run is currently running
        :raises SimulatorNotSetupException: If called before sim.setup
        :raises SimulatorShutdownException: If called after sim.end
        """

        SpynnakerDataView.check_user_can_act()

        # update file writer
        self.__write_to_files_indicators[variable] = to_file

        if variable == "gsyn_exc":
            if not self.__vertex.conductance_based:
                warn_once(
                    logger, "You are trying to record the excitatory "
                    "conductance from a model which does not use conductance "
                    "input. You will receive current measurements instead.")
        elif variable == "gsyn_inh":
            if not self.__vertex.conductance_based:
                warn_once(
                    logger, "You are trying to record the inhibitory "
                    "conductance from a model which does not use conductance "
                    "input. You will receive current measurements instead.")

        # Tell the vertex to record
        self.__vertex.set_recording(variable, sampling_interval, indexes)

    def get_recorded_pynn7(self, variable, as_matrix=False, view_indexes=None):
        """ Get recorded data in PyNN 0.7 format. Must not be spikes.

        :param str variable:
            The name of the variable to get. Supported variable names are:
            ``gsyn_exc``, ``gsyn_inh``, ``v``
        :param bool as_matrix: If set True the data is returned as a 2d matrix
        :param view_indexes: The indexes for which data should be returned.
            If ``None``, all data (view_index = data_indexes)
        :type view_indexes: list(int) or None
        :rtype: ~numpy.ndarray
        """
        # Only matrix variables are currently supported through this function
        if self.__vertex.get_recording_type(variable) != RecordingType.MATRIX:
            raise NotImplementedError(f"{variable} not supported")
        data = self.get_data(variable)
        sampling_interval = self.__vertex.get_recording_sampling_interval(
            variable)
        ids = self.__vertex.get_recording_indices(variable)
        if view_indexes is None:
            if len(ids) != self.__vertex.n_atoms:
                warn_once(logger, self._SELECTIVE_RECORDED_MSG)
            indexes = ids
        elif view_indexes == list(ids):
            indexes = ids
        else:
            # keep just the view indexes in the data
            indexes = [i for i in view_indexes if i in ids]
            # keep just data columns in the view
            map_indexes = [list(ids).index(i) for i in indexes]
            data = data[:, map_indexes]

        if as_matrix:
            return data

        # Convert to triples as Pynn 0,7 did
        n_machine_time_steps = len(data)
        n_neurons = len(indexes)
        column_length = n_machine_time_steps * n_neurons
        times = [i * sampling_interval
                 for i in range(0, n_machine_time_steps)]
        return numpy.column_stack((
                numpy.repeat(indexes, n_machine_time_steps, 0),
                numpy.tile(times, n_neurons),
                numpy.transpose(data).reshape(column_length)))

    def __get_empty_data(self, variable):
        """ Get an empty array for the given recording type

        :param str variable: the variable to get the array for
        :rtype: ~numpy.ndarray
        """
        if not self.__vertex.is_recording_variable(variable):
            raise KeyError(f"Variable {variable} is not being recorded")
        var_type = self.__vertex.get_recording_type(variable)
        if var_type == RecordingType.MATRIX:
            return numpy.zeros((0, 3))
        if var_type == RecordingType.BIT_FIELD:
            return numpy.zeros((0, 2))
        if var_type == RecordingType.EVENT:
            return numpy.zeros((0, 4))
        raise ValueError(f"Unknown type {var_type}")

    def get_data(self, variable):
        """ Get the data for the given variable with safety checks

        :param str variable: the variable to get the data for
        :rtype: ~numpy.ndarray
        """
        SpynnakerDataView.check_user_can_act()

        if not SpynnakerDataView.is_ran_last():
            if SpynnakerDataView.is_ran_ever():
                logger.warning(

                    f"The simulation has been reset, therefore {variable} "
                    f"cannot be retrieved, hence the list/last segment list "
                    f"will be empty")
            else:
                logger.warning(
                    f"The simulation has not yet run, therefore {variable} "
                    f"cannot be retrieved, hence the list will be empty")
            return self.__get_empty_data(variable)

        if get_config_bool("Machine", "virtual_board"):
            logger.warning(
                "The simulation is using a virtual machine and so has not "
                "truly ran, hence the list will be empty")
            return self.__get_empty_data(variable)

        return self.__vertex.get_recorded_data(variable)

    def turn_off_all_recording(self, indexes=None):
        """ Turns off recording, is used by a pop saying ``.record()``

        :param indexes:
        :type indexes: list or None
        """
        for variable in self.__vertex.get_recordable_variables():
            self.__vertex.set_not_recording(variable, indexes)

    def extract_neo_block(self, variables, view_indexes, clear, annotations):
        """ Extracts block from the vertices and puts them into a Neo block

        :param list(str) variables: the variables to extract
        :param slice view_indexes: the indexes to be included in the view
        :param bool clear: if the variables should be cleared after reading
        :param dict(str,object) annotations:
            annotations to put on the Neo block
        :return: The Neo block
        :rtype: ~neo.core.Block
        """
        block = neo.Block()

        for previous in range(0, SpynnakerDataView.get_segment_counter()):
            self.__append_previous_segment(
                block, previous, variables, view_indexes)

        # add to the segments the new block
        self.__append_current_segment(block, variables, view_indexes, clear)

        # add fluff to the neo block
        block.name = self.__population.label
        block.description = self.__population.describe()
        # pylint: disable=no-member
        block.rec_datetime = block.segments[0].rec_datetime
        block.annotate(**self.__metadata())
        if annotations:
            block.annotate(**annotations)
        return block

    def cache_data(self):
        """ Store data for later extraction
        """
        variables = self.__vertex.get_recording_variables()
        if variables:
            segment_number = SpynnakerDataView.get_segment_counter()
            logger.info("Caching data for segment {:d}", segment_number)

            data_cache = DataCache(
                label=self.__population.label,
                description=self.__population.describe(),
                segment_number=segment_number,
                recording_start_time=self.__recording_start_time,
                t=SpynnakerDataView.get_current_run_time_ms())

            for variable in variables:
                samp_interval = self.__vertex.get_recording_sampling_interval(
                    variable)
                indexes = self.__vertex.get_recording_indices(variable)
                data = self.get_data(variable)
                data_cache.save_data(
                    variable=variable, data=data, indexes=indexes,
                    n_neurons=self.__population.size,
                    units=self.__vertex.get_units(variable),
                    sampling_interval=samp_interval)
            self.__data_cache[segment_number] = data_cache

    def __clean_variables(self, variables):
        """ Sorts out variables for processing usage

        :param variables: list of variables names, or 'all', or single.
        :type variables: str or list(str)
        :return: ordered set of variables' names.
        :rtype: iterable(str)
        """
        # if variable is a base string, plonk into a array for ease of
        # conversion
        if isinstance(variables, str):
            variables = [variables]

        # if all are needed to be extracted, extract each and plonk into the
        # neo block segment. ensures whatever was in variables stays in
        # variables, regardless of all
        if 'all' in variables:
            variables = OrderedSet(variables)
            variables.remove('all')
            variables.update(self.__vertex.get_recording_variables())
        return variables

    def __append_current_segment(self, block, variables, view_indexes, clear):
        # build segment for the current data to be gathered in
        segment = neo.Segment(
            name="segment{}".format(SpynnakerDataView.get_segment_counter()),
            description=self.__population.describe(),
            rec_datetime=datetime.now())

        # sort out variables for using
        variables = self.__clean_variables(variables)

        for variable in variables:
            data = self.get_data(variable)
            s_intrval = self.__vertex.get_recording_sampling_interval(variable)
            var_type = self.__vertex.get_recording_type(variable)
            if var_type == RecordingType.BIT_FIELD:
                self.__add_neo_spiketrains(
                    segment=segment, spikes=data,
                    t=SpynnakerDataView.get_current_run_time_ms(),
                    n_neurons=self.__population.size,
                    recording_start_time=self.__recording_start_time,
                    sampling_interval=s_intrval, indexes=view_indexes,
                    label=self.__population.label)
            elif var_type == RecordingType.EVENT:
                self.__add_neo_events(
                    segment=segment, event_array=data, variable=variable,
                    recording_start_time=self.__recording_start_time)
            elif var_type == RecordingType.MATRIX:
                indices = self.__vertex.get_recording_indices(variable)
                self.__add_neo_analog_signals(
                    segment=segment, block=block, signal_array=data,
                    data_indexes=indices, view_indexes=view_indexes,
                    variable=variable,
                    recording_start_time=self.__recording_start_time,
                    sampling_interval=s_intrval,
                    units=self.__vertex.get_units(variable),
                    label=self.__population.label)
            else:
                raise ValueError(f"Unknown recording type {var_type}")
        block.segments.append(segment)

        if clear:
            self.__clear_recording(variables)

    def __append_previous_segment(
            self, block, segment_number, variables, view_indexes):
        if segment_number not in self.__data_cache:
            logger.warning("No Data available for Segment {}", segment_number)
            segment = neo.Segment(
                name="segment{}".format(segment_number),
                description="Empty",
                rec_datetime=datetime.now())
            block.segments.append(segment)
            return

        data_cache = self.__data_cache[segment_number]

        # sort out variables
        variables = self.__clean_variables(variables)

        # build segment for the previous data to be gathered in
        segment = neo.Segment(
            name="segment{}".format(segment_number),
            description=data_cache.description,
            rec_datetime=data_cache.rec_datetime)

        for variable in variables:
            if variable not in data_cache.variables:
                logger.warning("No Data available for Segment {} variable {}",
                               segment_number, variable)
                continue
            variable_cache = data_cache.get_data(variable)
            var_type = self.__vertex.get_recording_type(variable)
            if var_type == RecordingType.BIT_FIELD:
                self.__add_neo_spiketrains(
                    segment=segment, spikes=variable_cache.data,
                    t=data_cache.t, n_neurons=variable_cache.n_neurons,
                    recording_start_time=data_cache.recording_start_time,
                    sampling_interval=variable_cache.sampling_interval,
                    indexes=view_indexes, label=data_cache.label)
            elif var_type == RecordingType.EVENT:
                self.__add_neo_events(
                    segment=segment, event_array=variable_cache.data,
                    variable=variable,
                    recording_start_time=data_cache.recording_start_time)
            elif var_type == RecordingType.MATRIX:
                self.__add_neo_analog_signals(
                    segment=segment, block=block,
                    signal_array=variable_cache.data,
                    data_indexes=variable_cache.indexes,
                    view_indexes=view_indexes, variable=variable,
                    recording_start_time=data_cache.recording_start_time,
                    sampling_interval=variable_cache.sampling_interval,
                    units=variable_cache.units, label=data_cache.label)

        block.segments.append(segment)

    def __metadata(self):
        metadata = {
            'size': self.__population.size,
            'first_index': 0,
            'last_index': self.__population.size,
            'first_id': int(self.__population.first_id),
            'last_id': int(self.__population.last_id),
            'label': self.__population.label,
            'simulator': SpynnakerDataView.get_sim_name()
        }
        metadata.update(self.__population.annotations)
        metadata['dt'] = SpynnakerDataView.get_simulation_time_step_ms()
        metadata['mpi_processes'] = 1  # meaningless on Spinnaker
        return metadata

    def __clear_recording(self, variables):
        for variable in variables:
            self.__vertex.clear_recording_data(variable)

    def __add_neo_spiketrains(
            self, segment, spikes, t, n_neurons, recording_start_time,
            sampling_interval, indexes, label):
        """ Adds data that is spike-train-like to a neo segment.

        :param ~neo.core.Segment segment: Segment to add spikes to
        :param ~numpy.ndarray spikes: Spike data in raw sPyNNaker format
        :param int t: last simulation time
        :param int n_neurons:
            total number of neurons including ones not recording
        :param int recording_start_time: time recording started
        :param int sampling_interval: how often a neuron is recorded
        :param str label: recording elements label
        """
        # pylint: disable=too-many-arguments

        # Put the times for each neuron into the right place
        times = [[] for _ in range(n_neurons)]
        for neuron_id, time in spikes:
            times[int(neuron_id)].append(time)

        t_stop = t * quantities.ms

        if indexes is None:
            indexes = range(n_neurons)
        for index in indexes:
            spiketrain = neo.SpikeTrain(
                times=times[index],
                t_start=recording_start_time,
                t_stop=t_stop,
                units='ms',
                sampling_interval=sampling_interval,
                source_population=label,
                source_id=self.__population.index_to_id(index),
                source_index=index)
            segment.spiketrains.append(spiketrain)

    _SELECTIVE_RECORDED_MSG = (
        "Getting data on a whole population when selective recording is "
        "active will result in only the requested neurons being returned "
        "in numerical order and without repeats.")

    def __add_neo_analog_signals(
            self, segment, block, signal_array, data_indexes, view_indexes,
            variable, recording_start_time, sampling_interval, units, label):
        """ Adds a data item that is an analog signal to a neo segment

        :param ~neo.core.Segment segment: Segment to add data to
        :param ~neo.core.Block block: neo block
        :param ~numpy.ndarray signal_array: the raw signal data
        :param list(int) data_indexes: The indexes for the recorded data
        :param view_indexes: The indexes for which data should be returned.
            If ``None``, all data (view_index = data_indexes)
        :type view_indexes: list(int) or None
        :param str variable: the variable name
        :param recording_start_time: when recording started
        :type recording_start_time: float or int
        :param sampling_interval: how often a neuron is recorded
        :type sampling_interval: float or int
        :param units: the units of the recorded value
        :type units: quantities.quantity.Quantity or str
        :param str label: human readable label
        """
        # pylint: disable=too-many-arguments, no-member
        t_start = recording_start_time * quantities.ms
        sampling_period = sampling_interval * quantities.ms
        if view_indexes is None:
            if len(data_indexes) != self.__population.size:
                warn_once(logger, self._SELECTIVE_RECORDED_MSG)
            indexes = numpy.array(data_indexes)
        elif list(view_indexes) == list(data_indexes):
            indexes = numpy.array(data_indexes)
        else:
            # keep just the view indexes in the data
            indexes = [i for i in view_indexes if i in data_indexes]
            # keep just data columns in the view
            map_indexes = [list(data_indexes).index(i) for i in indexes]
            signal_array = signal_array[:, map_indexes]

        ids = list(map(self.__population.index_to_id, indexes))
        data_array = neo.AnalogSignal(
            signal_array,
            units=units,
            t_start=t_start,
            sampling_period=sampling_period,
            name=variable,
            source_population=label,
            source_ids=ids)
        channel_index = self.__get_channel_index(indexes, block)
        data_array.channel_index = channel_index
        data_array.shape = (data_array.shape[0], data_array.shape[1])
        segment.analogsignals.append(data_array)
        channel_index.analogsignals.append(data_array)

    def __add_neo_events(
            self, segment, event_array, variable, recording_start_time):
        """ Adds data that is events to a neo segment.

        :param ~neo.core.Segment segment: Segment to add data to
        :param ~numpy.ndarray signal_array: the raw "event" data
        :param str variable: the variable name
        :param recording_start_time: when recording started
        :type recording_start_time: float or int
        """
        # pylint: disable=too-many-arguments, no-member
        t_start = recording_start_time * quantities.ms

        formation_times = []
        formation_labels = []
        formation_annotations = dict()
        elimination_times = []
        elimination_labels = []
        elimination_annotations = dict()

        for i in range(len(event_array)):
            event_time = t_start + event_array[i][0] * quantities.ms
            pre_id = int(event_array[i][1])
            post_id = int(event_array[i][2])
            if event_array[i][3] == 1:
                formation_times.append(event_time)
                formation_labels.append(
                    str(pre_id)+"_"+str(post_id)+"_formation")
            else:
                elimination_times.append(event_time)
                elimination_labels.append(
                    str(pre_id)+"_"+str(post_id)+"_elimination")

        formation_event_array = neo.Event(
            times=formation_times,
            labels=formation_labels,
            units="ms",
            name=variable+"_form",
            description="Synapse formation events",
            array_annotations=formation_annotations)

        elimination_event_array = neo.Event(
            times=elimination_times,
            labels=elimination_labels,
            units="ms",
            name=variable+"_elim",
            description="Synapse elimination events",
            array_annotations=elimination_annotations)

        segment.events.append(formation_event_array)

        segment.events.append(elimination_event_array)

    @staticmethod
    def __get_channel_index(ids, block):
        for channel_index in block.channel_indexes:
            if numpy.array_equal(channel_index.index, ids):
                return channel_index
        count = len(block.channel_indexes)
        channel_index = neo.ChannelIndex(
            name="Index {}".format(count), index=ids)
        block.channel_indexes.append(channel_index)
        return channel_index

def _convert_extracted_data_into_neo_expected_format(signal_array, indexes):
    """ Converts data between sPyNNaker format and Neo format

    :param ~numpy.ndarray signal_array: Draw data in sPyNNaker format
    :param list(int) indexes:
    :rtype: ~numpy.ndarray
    """
    processed_data = [
        signal_array[:, 2][signal_array[:, 0] == index]
        for index in indexes]
    processed_data = numpy.vstack(processed_data).T
    return processed_data
