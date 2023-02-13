# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spinn_utilities.progress_bar import ProgressBar


def finish_connection_holders():
    """ Finishes the connection holders after data has been generated within\
        them, allowing any waiting callbacks to be called.

    :param ~pacman.model.graphs.application.ApplicationGraph application_graph:
    """
    edges = SpynnakerDataView.get_edges()
    progress = ProgressBar(len(edges), "Finalising Retrieved Connections")
    for edge in progress.over(edges):
        if isinstance(edge, ProjectionApplicationEdge):
            for synapse_info in edge.synapse_information:
                synapse_info.finish_connection_holders()
