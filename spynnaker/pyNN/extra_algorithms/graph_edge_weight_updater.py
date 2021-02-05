# Copyright (c) 2017-2019 The University of Manchester
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

from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.abstract_models import AbstractWeightUpdatable


class GraphEdgeWeightUpdater(object):
    """ Updates the weights of all edges.
    """

    def __call__(self, machine_graph):
        """
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            the machine_graph whose edges are to be updated
        """

        # create progress bar
        progress = ProgressBar(
            machine_graph.n_outgoing_edge_partitions,
            "Updating edge weights")

        # start checking edges to decide which ones need pruning....
        for partition in progress.over(machine_graph.outgoing_edge_partitions):
            for edge in partition.edges:
                if isinstance(edge, AbstractWeightUpdatable):
                    edge.update_weight()

        # return nothing
        return machine_graph
