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
from spynnaker.pyNN.models.neuron import ConnectionHolder
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge


class SpYNNakerConnectionHolderGenerator(object):
    """ Sets up connection holders for reports to use.
    """

    def __call__(self, application_graph):
        """
        :param ~pacman.model.graphs.application.ApplicationGraph \
                application_graph:
            app graph
        :return: the set of connection holders for after DSG generation
        :rtype: dict(tuple(ProjectionApplicationEdge, SynapseInformation),
            ConnectionHolder)
        """
        progress = ProgressBar(
            application_graph.n_outgoing_edge_partitions,
            "Generating connection holders for reporting connection data.")

        data_holders = dict()
        for partition in progress.over(
                application_graph.outgoing_edge_partitions):
            for edge in partition.edges:
                # add pre run generators so that reports can extract without
                # going to machine.
                if isinstance(edge, ProjectionApplicationEdge):
                    # build connection holders
                    self._generate_holder_for_edge(edge, data_holders)

        # return the two holders
        return data_holders

    @staticmethod
    def _generate_holder_for_edge(edge, data_holders):
        # build connection holders
        connection_holder = ConnectionHolder(
            None, True, edge.pre_vertex.n_atoms, edge.post_vertex.n_atoms)

        for synapse_information in edge.synapse_information:
            synapse_information.add_pre_run_connection_holder(
                connection_holder)
            # store for the report generations
            data_holders[edge, synapse_information] = connection_holder
