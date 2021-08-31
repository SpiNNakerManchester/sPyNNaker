# Copyright (c) 2020-2021 The University of Manchester
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
from pacman.operations.partition_algorithms import SplitterPartitioner
from data_specification import ReferenceContext


class SpynnakerSplitterPartitioner(SplitterPartitioner):
    """ a splitter partitioner that's bespoke for spynnaker vertices.
    """

    __slots__ = []

    def __call__(
            self, app_graph, machine, plan_n_time_steps,
            pre_allocated_resources=None):
        """
        :param ApplicationGraph app_graph: app graph
        :param ~spinn_machine.Machine machine: machine
        :param int plan_n_time_steps: the number of time steps to run for
        :param pre_allocated_resources: any pre-allocated res to account for
            before doing any splitting.
        :type pre_allocated_resources: PreAllocatedResourceContainer or None
        :rtype: tuple(~pacman.model.graphs.machine.MachineGraph, int)
        :raise PacmanPartitionException: when it cant partition
        """

        # do partitioning in same way, but in a context of references
        with ReferenceContext():
            machine_graph, chips_used = super().__call__(
                app_graph, machine, plan_n_time_steps, pre_allocated_resources)

        # return the accepted things
        return machine_graph, chips_used
