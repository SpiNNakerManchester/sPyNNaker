# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
import logging
from typing import (
    Any, Collection, Dict, Mapping, Optional, Sequence, TYPE_CHECKING)

import neo  # type: ignore[import]

from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once

from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from spynnaker.pyNN.types import IoDest

if TYPE_CHECKING:
    from spynnaker.pyNN.models.common.types import Names
    from spynnaker.pyNN.models.populations import Population
    from spynnaker.pyNN.models.common import PopulationApplicationVertex

logger = FormatAdapter(logging.getLogger(__name__))


class Recorder(object):
    """
    Object to hold recording behaviour, used by populations.
    """

    __slots__ = (
        "__population",
        "__vertex",
        "__write_to_files_indicators")

    def __init__(
            self, population: Population, vertex: PopulationApplicationVertex):
        """
        :param population:
            the population to record for
        :param vertex:
            the SpiNNaker graph vertex used by the population
        """
        self.__population = population
        self.__vertex = vertex

        # file flags, allows separate files for the recorded variables
        self.__write_to_files_indicators: Dict[str, IoDest] = {
            'spikes': None,
            'gsyn_exc': None,
            'gsyn_inh': None,
            'v': None}

    @property
    def write_to_files_indicators(self) -> Mapping[str, IoDest]:
        """
        What variables should be written to files, and where should they
        be written.
        """
        return self.__write_to_files_indicators

    def record(
            self, variables: Names, to_file: IoDest,
            sampling_interval: Optional[int],
            indexes: Optional[Collection[int]]) -> None:
        """
        Turns on (or off) recording.

        :param variables: either a single variable name or a list of variable
            names. For a given `celltype` class, `celltype.recordable` contains
            a list of variables that can be recorded for that `celltype`.
            Can also be ``None`` to reset the list of variables.
        :param to_file: a file to automatically record to (optional).
            :py:meth:`write_data` will be automatically called when
            `sim.end()` is called.
        :param sampling_interval: a value in milliseconds, and an integer
            multiple of the simulation timestep.
        :param indexes: The indexes of neurons to record from.
            This is non-standard PyNN and equivalent to creating a view with
            these indexes and asking the View to record.
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
                self.__turn_on_all_record(sampling_interval, to_file, indexes)
            else:
                # record variable
                self.turn_on_record(
                    variables, sampling_interval, to_file, indexes)

        else:  # list of variables, so just iterate though them
            if "all" in variables:
                self.__turn_on_all_record(sampling_interval, to_file, indexes)
            else:
                for variable in variables:
                    self.turn_on_record(
                        variable, sampling_interval, to_file, indexes)

    def __turn_on_all_record(
            self, sampling_interval: Optional[int], to_file: IoDest,
            indexes: Optional[Collection[int]]) -> None:
        """
        :param sampling_interval: the interval to record them
        :param to_file: If set, a file to write to (by handle or name)
        :param indexes: List of indexes to record or `None` for all
        :raises SimulatorRunningException: If `sim.run` is currently running
        :raises SimulatorNotSetupException: If called before `sim.setup`
        :raises SimulatorShutdownException: If called after `sim.end`
        """
        warn_once(
            logger, 'record("all") is non-standard PyNN, and '
                    'therefore may not be portable to other simulators.')

        # iterate though all possible recordings for this vertex
        for variable in self.__vertex.get_recordable_variables():
            self.turn_on_record(
                variable, sampling_interval, to_file, indexes)

    def turn_on_record(
            self, variable: str, sampling_interval: Optional[int] = None,
            to_file: IoDest = None,
            indexes: Optional[Collection[int]] = None) -> None:
        """
        Tell the vertex to record data.

        :param variable: The variable to record, supported variables to
            record are: ``gsyn_exc``, ``gsyn_inh``, ``v``, ``spikes``.
        :param sampling_interval: the interval to record them
        :param to_file: If set, a file to write to (by handle or name)
        :param indexes: List of indexes to record or `None` for all
        :raises SimulatorRunningException: If `sim.run` is currently running
        :raises SimulatorNotSetupException: If called before `sim.setup`
        :raises SimulatorShutdownException: If called after `sim.end`
        """
        SpynnakerDataView.check_user_can_act()

        if variable not in self.__write_to_files_indicators:
            logger.warning("unrecognised recording variable")

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
    def recording_label(self) -> str:
        """
        The label from the vertex is applicable or a default.
        """
        SpynnakerDataView.check_user_can_act()
        return self.__vertex.label or "!!UNLABELLED VERTEX!!"

    def turn_off_all_recording(
            self, indexes: Optional[Collection[int]] = None) -> None:
        """
        Turns off recording, is used by a pop saying ``.record()``.

        :param indexes:
        """
        for variable in self.__vertex.get_recordable_variables():
            self.__vertex.set_not_recording(variable, indexes)

    def extract_neo_block(
            self, variables: Names, view_indexes: Optional[Sequence[int]],
            clear: bool, annotations: Optional[Dict[str, Any]]) -> neo.Block:
        """
        Extracts block from the vertices and puts them into a Neo block.

        :param variables: the variables to extract
        :param view_indexes: the indexes to be included in the view
        :param clear: if the variables should be cleared after reading
        :param annotations:
            annotations to put on the Neo block
        :return: The Neo block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording not setup correctly
        """
        SpynnakerDataView.check_user_can_act()

        block: Optional[neo.Block] = None
        for previous in range(SpynnakerDataView.get_reset_number()):
            block = self.__append_previous_segment(
                block, previous, variables, view_indexes, clear, annotations)

        # add to the segments the new block
        return self.__append_current_segment(
            block, variables, view_indexes, clear, annotations)

    def write_data(
            self, csv_file: str, variables: Optional[Names],
            view_indexes: Optional[Sequence[int]] = None,
            annotations: Optional[Dict[str, Any]] = None) -> None:
        """
        Extracts block from the vertices and puts them into a Neo block.

        :param variables: the variables to extract
        :param variables: the variables to extract
        :param view_indexes: the indexes to be included in the view
        :param annotations:
            annotations to put on the Neo block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording not setup correctly
        """
        pop_label = self.__population.label

        wrote_metadata = False
        for segment in range(SpynnakerDataView.get_reset_number()):
            with NeoBufferDatabase.segement_db(segment) as db:
                if not wrote_metadata:
                    wrote_metadata = db.csv_block_metadata(
                        csv_file, pop_label, annotations)
                if wrote_metadata:
                    db.csv_segment(csv_file, pop_label, variables,
                                   view_indexes, allow_missing=True)

        if SpynnakerDataView.is_reset_last():
            if wrote_metadata:
                logger.warning(
                    "Due to the call directly after reset, "
                    "the data will only contain {} segments",
                    SpynnakerDataView.get_reset_number() - 1)
                return
            else:
                raise ConfigurationException(
                    f"Unable to write data for {pop_label}")

        with NeoBufferDatabase() as db:
            if not wrote_metadata:
                wrote_metadata = db.csv_block_metadata(
                    csv_file, pop_label, annotations)
            if wrote_metadata:
                db.csv_segment(csv_file, pop_label, variables,
                               view_indexes, allow_missing=False)
            else:
                raise ConfigurationException(
                    f"Unable to write data for {pop_label}")

    def __append_current_segment(
            self, block: neo.Block, variables: Names,
            view_indexes: Optional[Sequence[int]], clear: bool,
            annotations: Optional[Dict[str, Any]]) -> neo.Block:
        """
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording not setup correctly
        """
        with NeoBufferDatabase() as db:
            if block is None:
                block = db.get_empty_block(
                    self.__population.label, annotations)
                if block is None:
                    raise ConfigurationException(
                        f"No data for {self.__population.label}")
            if SpynnakerDataView.is_reset_last():
                logger.warning(
                    "Due to the call directly after reset, "
                    "the data will only contain {} segments",
                    SpynnakerDataView.get_reset_number() - 1)
            else:
                db.add_segment(
                    block, self.__population.label, variables, view_indexes,
                    allow_missing=False)
                if clear:
                    db.clear_data(self.__population.label, variables)
            return block

    def __append_previous_segment(
            self, block: Optional[neo.Block], segment_number: int,
            variables: Names, view_indexes: Optional[Sequence[int]],
            clear: bool,
            annotations: Optional[Dict[str, Any]]) -> Optional[neo.Block]:
        """
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the recording not setup correctly
        """
        with NeoBufferDatabase.segement_db(
                segment_number, read_only=not clear) as db:
            if block is None:
                block = db.get_empty_block(
                    self.__population.label, annotations)
            if block is not None:
                db.add_segment(
                    block, self.__population.label, variables, view_indexes,
                    allow_missing=True)
                if clear:
                    db.clear_data(self.__population.label, variables)
            return block
