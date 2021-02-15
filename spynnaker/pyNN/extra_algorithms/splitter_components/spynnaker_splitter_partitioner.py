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
from spinn_utilities.overrides import overrides
from pacman.model.partitioner_interfaces import AbstractSlicesConnect
from pacman.operations.partition_algorithms import SplitterPartitioner


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

        # do partitioning in same way
        machine_graph, chips_used = super().__call__(
            app_graph, machine, plan_n_time_steps, pre_allocated_resources)

        # return the accepted things
        return machine_graph, chips_used

    @overrides(SplitterPartitioner.create_machine_edge)
    def create_machine_edge(
            self, src_machine_vertex, dest_machine_vertex,
            common_edge_type, app_edge, machine_graph,
            app_outgoing_edge_partition, resource_tracker):
        # filter off connectivity
        if (isinstance(app_edge, AbstractSlicesConnect) and not
                app_edge.could_connect(
                    src_machine_vertex.vertex_slice,
                    dest_machine_vertex.vertex_slice)):
            return

        # TODO: this only works when the synaptic manager is reengineered to
        #       not assume the un-delayed edge still exists.

        # filter off delay values
        # post_splitter = dest_machine_vertex.app_vertex.splitter
        # if ((not isinstance(
        #         src_machine_vertex, DelayExtensionMachineVertex)) and
        #         isinstance(post_splitter, AbstractSpynnakerSplitterDelay)):
        #     min_delay = self._app_edge_min_delay[app_edge]
        #     if post_splitter.max_support_delay() < min_delay:
        #         return

        # build edge and add to machine graph
        machine_edge = common_edge_type(
            src_machine_vertex, dest_machine_vertex, app_edge=app_edge,
            label=self.MACHINE_EDGE_LABEL.format(app_edge.label))
        machine_graph.add_edge(
            machine_edge, app_outgoing_edge_partition.identifier)
