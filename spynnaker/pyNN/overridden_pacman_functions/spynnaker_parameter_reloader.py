from spynnaker.pyNN.models.abstract_models.abstract_population_settable import \
    AbstractPopulationSettable
from spinnman.model.core_subset import CoreSubset
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.cpu_state import CPUState
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.utilities import constants

from spinnman.messages.scp.scp_signal import SCPSignal
from spinnman.messages.sdp.sdp_flag import SDPFlag
from spinnman.messages.sdp.sdp_header import SDPHeader
from spinnman.messages.sdp.sdp_message import SDPMessage

from pacman.utilities.utility_objs.progress_bar import ProgressBar

import logging
import struct

logger = logging.getLogger(__name__)

class SpyNNakerParameterReloader(object):
    """
    SpyNNakerParameterReloader: Reload parameters for each vertex as needed.
    """

    def __call__(
        self, partitionable_graph, graph_mapper, placements, txrx, no_sync_changes):

        subsets = dict()

        progress = ProgressBar( len(partitionable_graph.vertices),
            "Checking all population for changed parameters.")

        num_changed_subvertices = 0

        # Cause all changed vertices to write the new parameters to SDRAM
        for vertex in partitionable_graph.vertices:
            if isinstance(vertex, AbstractPopulationSettable) and \
                vertex.parameters_have_changed():
                for subvertex in graph_mapper.get_subvertices_from_vertex(vertex):
                    placement = placements.get_placement_of_subvertex(subvertex)
                    vertex.update_parameters(txrx, graph_mapper.get_subvertex_slice(subvertex),
                        placement)
                    xy = (placement.x, placement.y)
                    if xy in subsets:
                        subsets[xy].add_processor(placement.p)
                    else:
                        subsets[xy] = CoreSubset(placement.x, placement.y, [placement.p])
                    num_changed_subvertices += 1

                vertex.mark_parameters_unchanged()
            progress.update()

        progress.end()

        if num_changed_subvertices == 0:
            return
        else:
            logger.info("Updating the parameters on {} cores.".format(num_changed_subvertices))

        core_subsets = CoreSubsets(subsets.values())

        # Send the signal to all affected cores to reload parameters from SDRAM
        unsuccessful_cores =  \
            helpful_functions.get_cores_not_in_state(core_subsets, CPUState.CPU_STATE_14, txrx)

        while len(unsuccessful_cores) > 0:
            for (x, y, p) in unsuccessful_cores:
                data = struct.pack(
                    "<I",
                    constants.SDP_RUNNING_MESSAGE_CODES.SDP_RELOAD_PARAMS.value)

                txrx.send_sdp_message(SDPMessage(
                    sdp_header=SDPHeader(
                        flags=SDPFlag.REPLY_NOT_EXPECTED,
                        destination_port=(
                            constants.SDP_PORTS.RUNNING_COMMAND_SDP_PORT.value),
                        destination_cpu=p,
                        destination_chip_x=x,
                        destination_chip_y=y), data=data))
            unsuccessful_cores =  \
                helpful_functions.get_cores_not_in_state(core_subsets, CPUState.CPU_STATE_14, txrx)

        # Get all cpus back to the expected sync state
        if no_sync_changes % 2 == 0:
            sync_state = CPUState.SYNC0
        else:
            sync_state = CPUState.SYNC1

        unsuccessful_cores =  \
            helpful_functions.get_cores_not_in_state(core_subsets, sync_state, txrx)

        while len(unsuccessful_cores) > 0:
            for (x, y, p) in unsuccessful_cores:
                data = struct.pack(
                    "<II",
                    constants.SDP_RUNNING_MESSAGE_CODES.SDP_SWITCH_STATE.value,
                    sync_state.value)
                txrx.send_sdp_message(SDPMessage(SDPHeader(
                    flags=SDPFlag.REPLY_NOT_EXPECTED,
                    destination_cpu=p,
                    destination_chip_x=x,
                    destination_port=
                    constants.SDP_PORTS.RUNNING_COMMAND_SDP_PORT.value,
                    destination_chip_y=y), data=data))

            unsuccessful_cores =  \
                helpful_functions.get_cores_not_in_state(core_subsets, sync_state, txrx)
