# Copyright (c) 2016 The University of Manchester
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

from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.neuron import ConnectionHolder
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge


class SpYNNakerConnectionHolderGenerator(object):
    """
    Sets up connection holders for reports to use.
    """

    def __call__(self, application_graph):
        """
        :param application_graph: application graph
        :type application_graph:
            ~pacman.model.graphs.application.ApplicationGraph
        :return:
            the set of connection holders for after data specification
            generation
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
        """
        :param ProjectionApplicationEdge edge:
        :param dict data_holders:
        """
        # build connection holders
        connection_holder = ConnectionHolder(
            None, True, edge.pre_vertex.n_atoms, edge.post_vertex.n_atoms)

        for synapse_information in edge.synapse_information:
            synapse_information.add_pre_run_connection_holder(
                connection_holder)
            # store for the report generations
            data_holders[edge, synapse_information] = connection_holder
