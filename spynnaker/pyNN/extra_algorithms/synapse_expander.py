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
import functools
import logging

from spinn_front_end_common.utilities.system_control_logic import \
    run_system_application
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_utilities.progress_bar import ProgressBar
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex

logger = logging.getLogger(__name__)

SYNAPSE_EXPANDER = "synapse_expander.aplx"
DELAY_EXPANDER = "delay_expander.aplx"


def synapse_expander(
        app_graph, placements, transceiver, provenance_file_path,
        executable_finder, extract_iobuf):
    """ Run the synapse expander.

    .. note::
        Needs to be done after data has been loaded.

    :param ~pacman.model.graphs.application.ApplicationGraph app_graph:
        The graph containing the vertices that might need expanding.
    :param ~pacman.model.placements.Placements placements:
        Where all vertices are on the machine.
    :param ~spinnman.transceiver.Transceiver transceiver:
        How to talk to the machine.
    :param str provenance_file_path: Where provenance data should be written.
    :param executable_finder:
        How to find the synapse expander binaries.
    :param extract_iobuf: bool flag for extracting iobuf
    :type executable_finder:
        ~spinn_utilities.executable_finder.ExecutableFinder
    """

    synapse_bin = executable_finder.get_executable_path(SYNAPSE_EXPANDER)
    delay_bin = executable_finder.get_executable_path(DELAY_EXPANDER)

    progress = ProgressBar(len(app_graph.vertices) + 2, "Expanding Synapses")

    # Find the places where the synapse expander and delay receivers should run
    expander_cores, expanded_pop_vertices = _plan_expansion(
        app_graph, placements, synapse_bin, delay_bin, progress)

    expander_app_id = transceiver.app_id_tracker.get_new_id()
    run_system_application(
        expander_cores, expander_app_id, transceiver, provenance_file_path,
        executable_finder, extract_iobuf, functools.partial(
            _fill_in_connection_data, placements=placements,
            expanded_pop_vertices=expanded_pop_vertices),
        [CPUState.FINISHED], False, "synapse_expander_on_{}_{}_{}.txt")


def _plan_expansion(app_graph, placements, synapse_expander_bin,
                    delay_expander_bin, progress):
    expander_cores = ExecutableTargets()
    expanded_pop_vertices = list()

    for vertex in progress.over(app_graph.vertices, finish_at_end=False):
        # Add all machine vertices of the population vertex to ones
        # that need synapse expansion
        if isinstance(vertex, AbstractPopulationVertex):
            for m_vertex in vertex.machine_vertices:
                if vertex.gen_on_machine(m_vertex.vertex_slice):
                    placement = placements.get_placement_of_vertex(m_vertex)
                    expander_cores.add_processor(
                        synapse_expander_bin,
                        placement.x, placement.y, placement.p)
                expanded_pop_vertices.append((vertex, m_vertex, placement))
        elif isinstance(vertex, DelayExtensionVertex):
            for m_vertex in vertex.machine_vertices:
                if vertex.gen_on_machine(m_vertex.vertex_slice):
                    placement = placements.get_placement_of_vertex(m_vertex)
                    expander_cores.add_processor(
                        delay_expander_bin,
                        placement.x, placement.y, placement.p,
                        executable_type=ExecutableType.SYSTEM)

    return expander_cores, expanded_pop_vertices


def _fill_in_connection_data(expanded_pop_vertices, transceiver):
    """ Once expander has run, fill in the connection data

    :rtype: None
    """
    for vertex, m_vertex, placement in expanded_pop_vertices:
        vertex.read_generated_connection_holders(
            transceiver, placement, m_vertex.vertex_slice)
