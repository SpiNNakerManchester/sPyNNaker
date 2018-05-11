from spinn_front_end_common.interface.interface_functions\
     import ChipIOBufExtractor
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.utility_models import DelayExtensionVertex
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
import logging
from spynnaker.pyNN.exceptions import SpynnakerException
from spinn_utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)

SYNAPSE_EXPANDER = "synapse_expander.aplx"
DELAY_RECEIVER = "delay_extension_receiver.aplx"


def synapse_expander(
        app_graph, graph_mapper, placements, transceiver,
        provenance_file_path):

    progress = ProgressBar(len(app_graph.vertices) + 4, "Expanding Synapses")

    # Find the places where the synapse expander and delay receivers should run
    synapse_expander_cores = ExecutableTargets()
    delay_receiver_cores = ExecutableTargets()
    for vertex in progress.over(app_graph.vertices, finish_at_end=False):

        # Find population vertices
        if isinstance(vertex, AbstractPopulationVertex):
            if vertex.gen_on_machine:

                # Add all machine vertices of the population vertex to ones
                # that need synapse expansion
                for m_vertex in graph_mapper.get_machine_vertices(vertex):
                    placement = placements.get_placement_of_vertex(m_vertex)
                    synapse_expander_cores.add_processor(
                        SYNAPSE_EXPANDER, placement.x, placement.y,
                        placement.p)

                # Go through the edges arriving at the vertex and add a
                # delay receiver where a delay extension sits
                for edge in app_graph.get_edges_ending_at_vertex(vertex):
                    if isinstance(edge.pre_vertex, DelayExtensionVertex):
                        for m_vertex in graph_mapper.get_machine_vertices(
                                edge.pre_vertex):
                            placement = placements.get_placement_of_vertex(
                                m_vertex)
                            delay_receiver_cores.add_processor(
                                DELAY_RECEIVER, placement.x, placement.y,
                                placement.p)

    # Launch the delay receivers
    delay_app_id = transceiver.app_id_tracker.get_new_id()
    transceiver.execute_application(delay_receiver_cores, delay_app_id)
    progress.update()

    # Launch the synapse expanders
    synapse_app_id = transceiver.app_id_tracker.get_new_id()
    transceiver.execute_application(synapse_expander_cores, synapse_app_id)
    progress.update()

    # Wait for everything to finish
    finished = False
    try:
        transceiver.wait_for_cores_to_be_in_state(
            synapse_expander_cores.all_core_subsets, synapse_app_id,
            [CPUState.FINISHED])
        progress.update()
        transceiver.wait_for_cores_to_be_in_state(
            delay_receiver_cores.all_core_subsets, delay_app_id,
            [CPUState.FINISHED])
        finished = True
        progress.update()
        progress.end()
    finally:
        # get the debug data
        if not finished:
            _handle_failure(
                synapse_expander_cores, delay_receiver_cores,
                transceiver, provenance_file_path)

        transceiver.stop_application(synapse_app_id)
        transceiver.app_id_tracker.free_id(synapse_app_id)
        transceiver.stop_application(delay_app_id)
        transceiver.app_id_tracker.free_id(delay_app_id)

        if not finished:
            raise SpynnakerException(
                "The synapse expander failed to complete")


def _handle_failure(
        synapse_expander_cores, delay_receiver_cores,
        transceiver, provenance_file_path):
    """
    :param executable_targets:
    :param txrx:
    :param provenance_file_path:
    :rtype: None
    """
    logger.info("Synapse expander has failed")
    iobuf_extractor = ChipIOBufExtractor()
    for executable_targets in (synapse_expander_cores, delay_receiver_cores):
        io_errors, io_warnings = iobuf_extractor(
            transceiver, executable_targets.all_core_subsets,
            provenance_file_path)
        for warning in io_warnings:
            logger.warning(warning)
        for error in io_errors:
            logger.error(error)
