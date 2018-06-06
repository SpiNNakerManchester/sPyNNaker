from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.utility_models import DelayExtensionVertex
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
import logging
from spynnaker.pyNN.exceptions import SpynnakerException
from spinn_utilities.progress_bar import ProgressBar

logger = logging.getLogger(__name__)

SYNAPSE_EXPANDER = "synapse_expander.aplx"
DELAY_EXPANDER = "delay_expander.aplx"


def synapse_expander(
        app_graph, graph_mapper, placements, transceiver,
        provenance_file_path, executable_finder):

    synapse_expander = executable_finder.get_executable_path(SYNAPSE_EXPANDER)
    delay_expander = executable_finder.get_executable_path(DELAY_EXPANDER)

    progress = ProgressBar(len(app_graph.vertices) + 2, "Expanding Synapses")

    # Find the places where the synapse expander and delay receivers should run
    expander_cores = ExecutableTargets()
    for vertex in progress.over(app_graph.vertices, finish_at_end=False):

        # Find population vertices
        if isinstance(
                vertex, (AbstractPopulationVertex, DelayExtensionVertex)):

            # Add all machine vertices of the population vertex to ones
            # that need synapse expansion
            for m_vertex in graph_mapper.get_machine_vertices(vertex):
                vertex_slice = graph_mapper.get_slice(m_vertex)
                if vertex.gen_on_machine(vertex_slice):
                    placement = placements.get_placement_of_vertex(m_vertex)
                    if isinstance(vertex, AbstractPopulationVertex):
                        binary = synapse_expander
                    else:
                        binary = delay_expander
                    expander_cores.add_processor(
                        binary, placement.x, placement.y, placement.p)

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
        progress.end()
    except Exception:
        logger.exception("Synapse expander has failed")
        _handle_failure(
            expander_cores, transceiver, provenance_file_path)
    finally:
        transceiver.stop_application(expander_app_id)
        transceiver.app_id_tracker.free_id(expander_app_id)

        if not finished:
            raise SpynnakerException(
                "The synapse expander failed to complete")


def _handle_failure(expander_cores, transceiver, provenance_file_path):
    """
    :param executable_targets:
    :param txrx:
    :param provenance_file_path:
    :rtype: None
    """
    core_subsets = expander_cores.all_core_subsets
    error_cores = transceiver.get_cores_not_in_state(
        core_subsets, [CPUState.RUNNING, CPUState.FINISHED])
    logger.error(transceiver.get_core_status_string(error_cores))
    io_buffers = transceiver.get_iobuf(core_subsets)
    for io_buf in io_buffers:
        logger.error("\n" + str(io_buf))
