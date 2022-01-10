# Copyright (c) 2017-2020 The University of Manchester
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
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spinn_utilities.progress_bar import ProgressBar


def finish_connection_holders():
    """ Finishes the connection holders after data has been generated within\
        them, allowing any waiting callbacks to be called.

    :param ~pacman.model.graphs.application.ApplicationGraph application_graph:
    """
    edges = SpynnakerDataView.get_runtime_graph().edges
    progress = ProgressBar(len(edges), "Finalising Retrieved Connections")
    for edge in progress.over(edges):
        if isinstance(edge, ProjectionApplicationEdge):
            for synapse_info in edge.synapse_information:
                synapse_info.finish_connection_holders()
