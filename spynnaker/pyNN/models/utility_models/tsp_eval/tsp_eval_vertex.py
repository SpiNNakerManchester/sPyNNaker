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
import numpy
from numpy.typing import NDArray
from typing import List
from spinn_utilities.log import FormatAdapter
from pacman.model.graphs.application.abstract import (
    AbstractOneAppOneMachineVertex)
from spynnaker.pyNN.models.populations.population import Population
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from .tsp_eval_machine_vertex import TSPEvalMachineVertex

logger = FormatAdapter(logging.getLogger(__name__))


class TSPEvalVertex(AbstractOneAppOneMachineVertex):
    """
    A SpiNNaker vertex that evaluates TSP solutions.
    """

    __slots__ = ("__recording_dtype")

    def __init__(
            self, neurons_per_value: int, populations: List[Population],
            min_run_length: int, max_spike_diff: int, n_recordings: int,
            label: str):
        """
        :param int neurons_per_value:
            The number of neurons used to represent each value
        :param List[Population] populations:
            The populations that make up the TSP solver
        :param int min_run_length:
            The minimum run of spikes considered to be a run
        :param int max_spike_diff:
            The maximum time between spikes in a run
        :param int n_recordings:
            The number of recordings to allow overall
        :param str label: The label of the vertex
        """

        # pylint: disable=too-many-arguments
        super(TSPEvalVertex, self).__init__(
            TSPEvalMachineVertex(
                neurons_per_value, populations, min_run_length, max_spike_diff,
                n_recordings, label, self),
            label, len(populations))

        self.__recording_dtype = numpy.dtype(f"<u4, {len(populations)}<u4")

    def set_recording(self, is_recording: bool) -> None:
        """
        Set whether the vertex should record spikes or not.

        :param bool is_recording:
            Whether the vertex should record spikes or not
        """
        self.machine_vertex.set_recording(is_recording)

    def is_recording(self) -> bool:
        """
        Determine whether the vertex is recording spikes or not.

        :rtype: bool
        :return: Whether the vertex is recording spikes or not
        """
        return self.machine_vertex.is_recording()

    def get_recorded_data(self) -> NDArray:
        """ Get the data recorded.  This is an array of
                (time, array of node ids)
            where the time is the time at which a solution was found and the
            list of node ids are the order of cities visited.

        :rtype: NDArray
        """
        buffer_manager = SpynnakerDataView().get_buffer_manager()
        placement = SpynnakerDataView().get_placement_of_vertex(
            self.machine_vertex)
        data, missing = buffer_manager.get_data_by_placement(placement, 0)
        if missing:
            logger.warning(
                "Missing data for vertex %s", self.machine_vertex.label)
        return numpy.frombuffer(data, dtype=self.__recording_dtype)
