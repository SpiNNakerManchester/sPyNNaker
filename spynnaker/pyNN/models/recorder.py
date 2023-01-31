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
import neo
from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase

logger = FormatAdapter(logging.getLogger(__name__))


class Recorder(object):
    """ Object to hold recording behaviour, used by populations.
    """

    __slots__ = [
        "__data_cache",
        "__population",
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

    @property
    def recording_label(self):
        SpynnakerDataView.check_user_can_act()
        return self.__vertex.label

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
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording not setup correctly
        """
        with NeoBufferDatabase() as db:
            block = db.get_empty_block(self.__population.label)

        for previous in range(0, SpynnakerDataView.get_segment_counter()):
            self.__append_previous_segment(
                block, previous, variables, view_indexes, clear)

        # add to the segments the new block
        self.__append_current_segment(block, variables, view_indexes, clear)

        return block

    def csv_neo_block(
            self, csv_file, variables, view_indexes=None, annotations=None):
        """ Extracts block from the vertices and puts them into a Neo block

        :param str variables: the variables to extract
        :param list(str) variables: the variables to extract
        :param slice view_indexes: the indexes to be included in the view
        :param dict(str,object) annotations:
            annotations to put on the Neo block
        :return: The Neo block
        :rtype: ~neo.core.Block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording not setup correctly
        """
        pop_label = self.__population.label
        with NeoBufferDatabase() as db:
            db.csv_block_metadata(csv_file, pop_label, annotations)

        for segment in range(0, SpynnakerDataView.get_segment_counter()):
            if segment not in self.__data_cache:
                logger.warning("No Data available for Segment {}", segment)
                continue
            with NeoBufferDatabase(self.__data_cache[segment]) as db:
                db.csv_segment(
                    csv_file, pop_label, variables, view_indexes)

        with NeoBufferDatabase() as db:
            if SpynnakerDataView.is_reset_last():
                logger.warning(
                    "Due to the call directly after reset. "
                    "The data will only contain "
                    f"{SpynnakerDataView.get_segment_counter()-1} segments")
            else:
                db.csv_segment(
                    csv_file, pop_label, variables, view_indexes)

    def cache_data(self):
        """ Store data for later extraction
        """
        variables = self.__vertex.get_recording_variables()
        if variables:
            segment_number = SpynnakerDataView.get_segment_counter()
            self.__data_cache[segment_number] = \
                NeoBufferDatabase.default_database_file()

    def __append_current_segment(self, block, variables, view_indexes, clear):
        """

        :param block:
        :param variables:
        :param view_indexes:
        :param clear:
        :return:
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording not setup correctly
        """
        SpynnakerDataView.check_user_can_act()

        with NeoBufferDatabase() as db:
            if SpynnakerDataView.is_reset_last():
                logger.warning(
                    "Due to the call directly after reset. "
                    "The data will only contain "
                    f"{SpynnakerDataView.get_segment_counter()-1} segments")
            else:
                db.add_segment(
                    block, self.__population.label, variables, view_indexes)
                if clear:
                    db.clear_data(self.__population.label, variables)

    def __append_previous_segment(
            self, block, segment_number, variables, view_indexes, clear):
        """

        :param block:
        :param segment_number:
        :param variables:
        :param view_indexes:
        :param bool clear:
        :return:
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording not setup correctly
        """
        if segment_number not in self.__data_cache:
            logger.warning("No Data available for Segment {}", segment_number)
            segment = neo.Segment(
                name="segment{}".format(segment_number),
                description="Empty",
                rec_datetime=datetime.now())
            block.segments.append(segment)
            return

        with NeoBufferDatabase(self.__data_cache[segment_number]) as db:
            db.add_segment(
                block, self.__population.label, variables, view_indexes)
            if clear:
                db.clear_data(self.__population.label, variables)
