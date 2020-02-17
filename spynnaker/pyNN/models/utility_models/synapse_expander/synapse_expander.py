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

import logging
import os
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.make_tools.replacer import Replacer
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine)
from six import iteritems

logger = logging.getLogger(__name__)

SYNAPSE_EXPANDER = "synapse_expander.aplx"
DELAY_EXPANDER = "delay_expander.aplx"


def synapse_expander(
        app_graph, graph_mapper, placements, transceiver,
        provenance_file_path, executable_finder):
    """ Run the synapse expander - needs to be done after data has been loaded
    """

    synapse_bin = executable_finder.get_executable_path(SYNAPSE_EXPANDER)
    delay_bin = executable_finder.get_executable_path(DELAY_EXPANDER)
    expandable = (AbstractPopulationVertex, DelayExtensionVertex)

    progress = ProgressBar(len(app_graph.vertices) + 2, "Expanding Synapses")

    # Find the places where the synapse expander and delay receivers should run
    expander_cores = ExecutableTargets()
    gen_on_machine_vertices = list()
    for vertex in progress.over(app_graph.vertices, finish_at_end=False):

        # Find population vertices
        if isinstance(vertex, expandable):
            # Add all machine vertices of the population vertex to ones
            # that need synapse expansion
            gen_on_machine = False
            for m_vertex in graph_mapper.get_machine_vertices(vertex):
                vertex_slice = graph_mapper.get_slice(m_vertex)
                if vertex.gen_on_machine(vertex_slice):
                    placement = placements.get_placement_of_vertex(m_vertex)
                    if isinstance(vertex, AbstractPopulationVertex):
                        binary = synapse_bin
                        gen_on_machine = True
                    else:
                        binary = delay_bin
                    expander_cores.add_processor(
                        binary, placement.x, placement.y, placement.p)
            if gen_on_machine:
                gen_on_machine_vertices.append(vertex)

    # Launch the delay receivers
    expander_app_id = transceiver.app_id_tracker.get_new_id()
    transceiver.execute_application(expander_cores, expander_app_id)
    progress.update()

    # Wait for everything to finish
    finished = False
    try:
        transceiver.wait_for_cores_to_be_in_state(
            expander_cores.all_core_subsets, expander_app_id,
            [CPUState.FINISHED])
        progress.update()
        finished = True
        _fill_in_connection_data(
            gen_on_machine_vertices, graph_mapper, placements, transceiver)
        _extract_iobuf(expander_cores, transceiver, provenance_file_path)
        progress.end()
    except Exception:  # pylint: disable=broad-except
        logger.exception("Synapse expander has failed")
        _handle_failure(
            expander_cores, transceiver, provenance_file_path)
    finally:
        transceiver.stop_application(expander_app_id)
        transceiver.app_id_tracker.free_id(expander_app_id)

        if not finished:
            raise SpynnakerException(
                "The synapse expander failed to complete")


def _extract_iobuf(expander_cores, transceiver, provenance_file_path,
                   display=False):
    """ Extract IOBuf from the cores
    """
    io_buffers = transceiver.get_iobuf(expander_cores.all_core_subsets)
    core_to_replacer = dict()
    for binary in expander_cores.binaries:
        replacer = Replacer(binary)
        for core_subset in expander_cores.get_cores_for_binary(binary):
            x = core_subset.x
            y = core_subset.y
            for p in core_subset.processor_ids:
                core_to_replacer[x, y, p] = replacer

    for io_buf in io_buffers:
        file_path = os.path.join(
            provenance_file_path, "expander_{}_{}_{}.txt".format(
                io_buf.x, io_buf.y, io_buf.p))
        replacer = core_to_replacer[io_buf.x, io_buf.y, io_buf.p]
        text = ""
        for line in io_buf.iobuf.split("\n"):
            text += replacer.replace(line) + "\n"
        with open(file_path, "w") as writer:
            writer.write(text)
        if display:
            print("{}:{}:{} {}".format(io_buf.x, io_buf.y, io_buf.p, text))


def _handle_failure(expander_cores, transceiver, provenance_file_path):
    """ Handle failure of the expander

    :param executable_targets:
    :param txrx:
    :param provenance_file_path:
    :rtype: None
    """
    core_subsets = expander_cores.all_core_subsets
    error_cores = transceiver.get_cores_not_in_state(
        core_subsets, [CPUState.RUNNING, CPUState.FINISHED])
    logger.error(transceiver.get_core_status_string(error_cores))
    _extract_iobuf(expander_cores, transceiver, provenance_file_path,
                   display=True)


def _fill_in_connection_data(
        gen_on_machine_vertices, graph_mapper, placements, transceiver):
    """ Once expander has run, fill in the connection data
    :param app_graph
    :param graph_mapper
    :rtype: None
    """
    ctl = globals_variables.get_simulator()
    use_extra_monitors = False

    for vertex in gen_on_machine_vertices:
        conn_holders = vertex.get_connection_holders()
        for (app_edge, synapse_info), conn_holder_list in iteritems(
                conn_holders):
            # Only do this if this synapse_info has been generated
            # on the machine using the expander
            connector = synapse_info.connector
            dynamics = synapse_info.synapse_dynamics
            connector_gen = isinstance(
                connector, AbstractGenerateConnectorOnMachine) and \
                connector.generate_on_machine(
                    synapse_info.weights, synapse_info.delays)
            synapse_gen = isinstance(
                dynamics, AbstractGenerateOnMachine)
            if connector_gen and synapse_gen:
                machine_edges = graph_mapper.get_machine_edges(app_edge)
                for machine_edge in machine_edges:
                    placement = placements.get_placement_of_vertex(
                        machine_edge.post_vertex)
                    conns = vertex.get_connections_from_machine(
                        transceiver, placement, machine_edge, graph_mapper,
                        ctl.routing_infos, synapse_info, ctl.machine_time_step,
                        use_extra_monitors)
                    for conn_holder in conn_holder_list:
                        conn_holder.add_connections(conns)
