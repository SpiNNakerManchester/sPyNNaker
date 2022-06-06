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
from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.ordered_set import OrderedSet
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, AbstractNeuronRecordable, AbstractEventRecordable)
from spynnaker.pyNN.utilities.constants import (
    SPIKES, MEMBRANE_POTENTIAL, GSYN_EXCIT, GSYN_INHIB, REWIRING)
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.utilities.data_cache import DataCache

# needed as dealing with quantities
# pylint: disable=c-extension-no-member

logger = FormatAdapter(logging.getLogger(__name__))
_DEFAULT_UNITS = {
    SPIKES: "spikes",
    MEMBRANE_POTENTIAL: "mV",
    GSYN_EXCIT: "uS",
    GSYN_INHIB: "uS",
    REWIRING: "ms"}


class Recorder(object):
    """ Object to hold recording behaviour, used by populations.
    """

    __slots__ = [
        "_data_cache",
        "__population",
        "_recording_start_time",
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
        self._recording_start_time = get_simulator().t
        self._data_cache = {}

    @property
    def write_to_files_indicators(self):
        """ What variables should be written to files, and where should they\
            be written.

        :rtype: dict(str, neo.io.baseio.BaseIO or str or None)
        """
        return self.__write_to_files_indicators

    def record(
            self, variables, to_file, sampling_interval, indexes):
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
                for variable in self.get_all_possible_recordable_variables():
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
        """

        get_simulator().verify_not_running()
        # tell vertex its recording
        if variable == "spikes":
            if not isinstance(self.__vertex, AbstractSpikeRecordable):
                raise Exception("This population does not support the "
                                "recording of spikes!")
            self.__vertex.set_recording_spikes(
                sampling_interval=sampling_interval, indexes=indexes)
        elif variable == "all":
            raise Exception("Illegal call with all")
        else:
            if not isinstance(self.__vertex, AbstractNeuronRecordable):
                raise Exception("This population does not support the "
                                "recording of {}!".format(variable))
            self.__vertex.set_recording(
                variable, sampling_interval=sampling_interval, indexes=indexes)

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
        if variable in [SPIKES, REWIRING]:
            raise NotImplementedError(f"{variable} not supported")
        (data, ids, sampling_interval) = self.get_recorded_matrix(variable)
        if view_indexes is None:
            if len(ids) != self.__population.size:
                warn_once(logger, self._SELECTIVE_RECORDED_MSG)
            indexes = ids
        elif view_indexes == ids:
            indexes = ids
        else:
            # keep just the view indexes in the data
            indexes = [i for i in view_indexes if i in ids]
            # keep just data columns in the view
            map_indexes = [ids.index(i) for i in indexes]
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

    def get_recorded_matrix(self, variable):
        """ Perform safety checks and get the recorded data from the vertex\
            in matrix format.

        :param str variable:
            The variable name to read. Supported variable names are:
            ``gsyn_exc``, ``gsyn_inh``, ``v``
        :return: data, indexes, sampling_interval
        :rtype: tuple(~numpy.ndarray, list(int), float)
        """
        data = None
        sim = get_simulator()

        sim.verify_not_running()

        # check that we're in a state to get voltages
        if not isinstance(self.__vertex, AbstractNeuronRecordable):
            raise ConfigurationException(
                "This population has not got the capability to record {}"
                .format(variable))
        if not self.__vertex.is_recording(variable):
            raise ConfigurationException(
                "This population has not been set to record {}".format(
                    variable))

        if not sim.has_ran:
            logger.warning(
                "The simulation has not yet run, therefore {} cannot be "
                "retrieved, hence the list will be empty".format(
                    variable))
            data = numpy.zeros((0, 3))
            indexes = []
            sampling_interval = self.__vertex.get_neuron_sampling_interval(
                variable)
        elif sim.use_virtual_board:
            logger.warning(
                "The simulation is using a virtual machine and so has not "
                "truly ran, hence the list will be empty")
            data = numpy.zeros((0, 3))
            indexes = []
            sampling_interval = self.__vertex.get_neuron_sampling_interval(
                variable)
        else:
            # assuming we got here, everything is ok, so we should go get the
            # data
            results = self.__vertex.get_data(
                variable, sim.no_machine_time_steps, sim.placements,
                sim.buffer_manager)
            (data, indexes, sampling_interval) = results

        return (data, indexes, sampling_interval)

    def get_spikes(self):
        """ How to get spikes (of a population's neurons) from the recorder.

        :return: the spikes (event times) from the underlying vertex
        :rtype: ~numpy.ndarray
        """

        # check we're in a state where we can get spikes
        if not isinstance(self.__vertex, AbstractSpikeRecordable):
            raise ConfigurationException(
                "This population has not got the capability to record spikes")
        if not self.__vertex.is_recording_spikes():
            raise ConfigurationException(
                "This population has not been set to record spikes")

        sim = get_simulator()
        if not sim.has_ran:
            logger.warning(
                "The simulation has not yet run, therefore spikes cannot "
                "be retrieved, hence the list will be empty")
            return numpy.zeros((0, 2))
        if sim.use_virtual_board:
            logger.warning(
                "The simulation is using a virtual machine and so has not "
                "truly ran, hence the spike list will be empty")
            return numpy.zeros((0, 2))

        # assuming we got here, everything is OK, so we should go get the
        # spikes
        return self.__vertex.get_spikes(sim.placements, sim.buffer_manager)

    def get_events(self, variable):
        """ How to get rewiring events (of a post-population) from recorder

        :return: the rewires (event times, values) from the underlying vertex
        :rtype: ~numpy.ndarray
        """

        # check we're in a state where we can get rewires
        if not isinstance(self.__vertex, AbstractEventRecordable):
            raise ConfigurationException(
                "This population has not got the capability to record rewires")
        if not self.__vertex.is_recording(REWIRING):
            raise ConfigurationException(
                "This population has not been set to record rewires")

        sim = get_simulator()
        if not sim.has_ran:
            logger.warning(
                "The simulation has not yet run, therefore rewires cannot "
                "be retrieved, hence the list will be empty")
            return numpy.zeros((0, 4))
        if sim.use_virtual_board:
            logger.warning(
                "The simulation is using a virtual machine and so has not "
                "truly ran, hence the rewires list will be empty")
            return numpy.zeros((0, 4))

        return self.__vertex.get_events(
            variable, sim.placements, sim.buffer_manager)

    def turn_off_all_recording(self, indexes=None):
        """ Turns off recording, is used by a pop saying ``.record()``

        :param indexes:
        :type indexes: list or None
        """
        # check for standard record which includes spikes
        if isinstance(self.__vertex, AbstractNeuronRecordable):
            variables = self.__vertex.get_recordable_variables()
            for variable in variables:
                self.__vertex.set_recording(
                    variable, new_state=False, indexes=indexes)

        # check for spikes
        if isinstance(self.__vertex, AbstractSpikeRecordable):
            self.__vertex.set_recording_spikes(
                new_state=False, indexes=indexes)

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

        for previous in range(0, get_simulator().segment_counter):
            self._append_previous_segment(
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

    def _get_units(self, variable):
        """ Get units with some safety code if the population has trouble

        :param str variable: name of the variable
        :return: type of the data
        :rtype: str
        """
        try:
            return self.__population.find_units(variable)
        except Exception as e:
            logger.warning("Population: {} Does not support units for {}",
                           self.__population.label, variable)
            if variable in _DEFAULT_UNITS:
                return _DEFAULT_UNITS[variable]
            raise e

    @property
    def __spike_sampling_interval(self):
        """
        :rtype: float
        """
        return self.__vertex.get_spikes_sampling_interval()

    def cache_data(self):
        """ Store data for later extraction
        """
        variables = self.get_all_recording_variables()
        if variables:
            segment_number = get_simulator().segment_counter
            logger.info("Caching data for segment {:d}", segment_number)

            data_cache = DataCache(
                label=self.__population.label,
                description=self.__population.describe(),
                segment_number=segment_number,
                recording_start_time=self._recording_start_time,
                t=get_simulator().t)

            for variable in variables:
                if variable == SPIKES:
                    data = self.get_spikes()
                    sampling_interval = self.__spike_sampling_interval
                    indexes = None
                elif variable == REWIRING:
                    data = self.get_events(variable)
                    sampling_interval = None
                    indexes = None
                else:
                    (data, indexes, sampling_interval) = \
                        self.get_recorded_matrix(variable)
                data_cache.save_data(
                    variable=variable, data=data, indexes=indexes,
                    n_neurons=self.__population.size,
                    units=self._get_units(variable),
                    sampling_interval=sampling_interval)
            self._data_cache[segment_number] = data_cache

    def _filter_recorded(self, filter_ids):
        # TODO: unused?
        record_ids = list()
        for neuron_id in range(0, len(filter_ids)):
            if filter_ids[neuron_id]:
                # add population first ID to ensure all atoms have a unique
                # identifier (PyNN enforcement)
                record_ids.append(neuron_id + self.__population.first_id)
        return record_ids

    def _clean_variables(self, variables):
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
            variables.update(self.get_all_recording_variables())
        return variables

    def __append_current_segment(self, block, variables, view_indexes, clear):
        # build segment for the current data to be gathered in
        segment = neo.Segment(
            name="segment{}".format(get_simulator().segment_counter),
            description=self.__population.describe(),
            rec_datetime=datetime.now())

        # sort out variables for using
        variables = self._clean_variables(variables)

        for variable in variables:
            if variable == SPIKES:
                self.__read_in_spikes(
                    segment=segment,
                    spikes=self.get_spikes(),
                    t=get_simulator().get_current_time(),
                    n_neurons=self.__population.size,
                    recording_start_time=self._recording_start_time,
                    sampling_interval=self.__spike_sampling_interval,
                    indexes=view_indexes,
                    label=self.__population.label)
            elif variable == REWIRING:
                self.__read_in_event(
                    segment=segment,
                    event_array=self.get_events(variable),
                    variable=variable,
                    recording_start_time=self._recording_start_time)
            else:
                (data, data_indexes, sampling_interval) = \
                    self.get_recorded_matrix(variable)
                self.__read_in_signal(
                    segment=segment,
                    block=block,
                    signal_array=data,
                    data_indexes=data_indexes,
                    view_indexes=view_indexes,
                    variable=variable,
                    recording_start_time=self._recording_start_time,
                    sampling_interval=sampling_interval,
                    units=self._get_units(variable),
                    label=self.__population.label)
        block.segments.append(segment)

        if clear:
            self._clear_recording(variables)

    def _append_previous_segment(
            self, block, segment_number, variables, view_indexes):
        if segment_number not in self._data_cache:
            logger.warning("No Data available for Segment {}", segment_number)
            segment = neo.Segment(
                name="segment{}".format(segment_number),
                description="Empty",
                rec_datetime=datetime.now())
            block.segments.append(segment)
            return

        data_cache = self._data_cache[segment_number]

        # sort out variables
        variables = self._clean_variables(variables)

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
            if variable == SPIKES:
                self.__read_in_spikes(
                    segment=segment,
                    spikes=variable_cache.data,
                    t=data_cache.t,
                    n_neurons=variable_cache.n_neurons,
                    recording_start_time=data_cache.recording_start_time,
                    sampling_interval=variable_cache.sampling_interval,
                    indexes=view_indexes,
                    label=data_cache.label)
            elif variable == REWIRING:
                self.__read_in_event(
                    segment=segment,
                    event_array=variable_cache.data,
                    variable=variable,
                    recording_start_time=data_cache.recording_start_time)
            else:
                self.__read_in_signal(
                    segment=segment,
                    block=block,
                    signal_array=variable_cache.data,
                    data_indexes=variable_cache.indexes,
                    view_indexes=view_indexes,
                    variable=variable,
                    recording_start_time=data_cache.recording_start_time,
                    sampling_interval=variable_cache.sampling_interval,
                    units=variable_cache.units,
                    label=data_cache.label)

        block.segments.append(segment)

    def get_all_possible_recordable_variables(self):
        """ All variables that could be recorded.

        :rtype: set(str)
        """
        variables = OrderedSet()
        if isinstance(self.__vertex, AbstractSpikeRecordable):
            variables.add(SPIKES)
        if isinstance(self.__vertex, AbstractNeuronRecordable):
            variables.update(self.__vertex.get_recordable_variables())
        return variables

    def get_all_recording_variables(self):
        """ All variables that have been set to record.

        :rtype: set(str)
        """
        possibles = self.get_all_possible_recordable_variables()
        variables = OrderedSet()
        for possible in possibles:
            if possible == SPIKES:
                if isinstance(self.__vertex, AbstractSpikeRecordable) \
                        and self.__vertex.is_recording_spikes():
                    variables.add(possible)
            elif isinstance(self.__vertex, AbstractNeuronRecordable) \
                    and self.__vertex.is_recording(possible):
                variables.add(possible)
        return variables

    def __metadata(self):
        metadata = {
            'size': self.__population.size,
            'first_index': 0,
            'last_index': self.__population.size,
            'first_id': int(self.__population.first_id),
            'last_id': int(self.__population.last_id),
            'label': self.__population.label,
            'simulator': get_simulator().name,
        }
        metadata.update(self.__population.annotations)
        metadata['dt'] = get_simulator().dt
        metadata['mpi_processes'] = get_simulator().num_processes
        return metadata

    def _clear_recording(self, variables):
        sim = get_simulator()
        for variable in variables:
            if variable == SPIKES:
                self.__vertex.clear_spike_recording(
                    sim.buffer_manager, sim.placements)
            elif variable == MEMBRANE_POTENTIAL:
                self.__vertex.clear_recording(
                    variable, sim.buffer_manager, sim.placements)
            elif variable == GSYN_EXCIT:
                self.__vertex.clear_recording(
                    variable, sim.buffer_manager, sim.placements)
            elif variable == GSYN_INHIB:
                self.__vertex.clear_recording(
                    variable, sim.buffer_manager, sim.placements)
            else:
                raise InvalidParameterType(
                    "The variable {} is not a recordable value".format(
                        variable))

    def __read_in_spikes(
            self, segment, spikes, t, n_neurons, recording_start_time,
            sampling_interval, indexes, label):
        """ Converts the data into SpikeTrains and saves them to the segment.

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
        # Safety check in case spikes are an empty list
        if len(spikes) == 0:
            spikes = numpy.empty(shape=(0, 2))

        t_stop = t * quantities.ms

        if indexes is None:
            indexes = range(n_neurons)
        for index in indexes:
            spiketrain = neo.SpikeTrain(
                times=spikes[spikes[:, 0] == index][:, 1],
                t_start=recording_start_time,
                t_stop=t_stop,
                units='ms',
                sampling_interval=sampling_interval,
                source_population=label,
                source_id=self.__population.index_to_id(index),
                source_index=index)
            # get times per atom
            segment.spiketrains.append(spiketrain)

    _SELECTIVE_RECORDED_MSG = (
        "Getting data on a whole population when selective recording is "
        "active will result in only the requested neurons being returned "
        "in numerical order and without repeats.")

    def __read_in_signal(
            self, segment, block, signal_array, data_indexes, view_indexes,
            variable, recording_start_time, sampling_interval, units, label):
        """ Reads in a data item that's not spikes (likely v, gsyn e, gsyn i)\
            and saves this data to the segment.

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
        elif view_indexes == data_indexes:
            indexes = numpy.array(data_indexes)
        else:
            # keep just the view indexes in the data
            indexes = [i for i in view_indexes if i in data_indexes]
            # keep just data columns in the view
            map_indexes = [data_indexes.index(i) for i in indexes]
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

    def __read_in_event(
            self, segment, event_array, variable, recording_start_time):
        """ Reads in a data item that is an event (i.e. rewiring form/elim)\
            and saves this data to the segment.

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
