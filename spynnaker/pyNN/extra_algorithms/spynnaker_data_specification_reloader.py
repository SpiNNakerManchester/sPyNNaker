# Copyright (c) 2022 The University of Manchester
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
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.config_holder import get_config_bool
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.utilities.system_control_logic import (
    run_system_application)
from spinn_front_end_common.utilities.helpful_functions import (
    write_address_to_user1)
from spinn_front_end_common.abstract_models import AbstractHasAssociatedBinary
from spinn_front_end_common.interface.interface_functions\
    .dsg_region_reloader import (get_reload_data_dir, regenerate_data_spec)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, AbstractNeuronExpandable, SYNAPSE_EXPANDER_APLX,
    NEURON_EXPANDER_APLX)

logger = logging.getLogger(__name__)


def spynnaker_data_specification_reloader():
    data_dir = get_reload_data_dir()
    synapse_bin = SpynnakerDataView.get_executable_path(SYNAPSE_EXPANDER_APLX)
    neuron_bin = SpynnakerDataView.get_executable_path(NEURON_EXPANDER_APLX)

    progress = ProgressBar(
        SpynnakerDataView.get_n_placements(), "Reloading data")

    synapse_expander_cores = ExecutableTargets()
    synapse_expandables = list()
    neuron_expander_cores = ExecutableTargets()
    neuron_expandables = list()
    normal_cores = ExecutableTargets()
    placements_to_free = set()
    for pl in progress.over(SpynnakerDataView.iterate_placemements()):
        # Generate the data spec for the placement if needed
        if regenerate_data_spec(pl, data_dir):
            is_expanded = False
            if isinstance(pl.vertex, AbstractSynapseExpandable):
                if (pl.vertex.do_synapse_regeneration() and
                        pl.vertex.gen_on_machine()):
                    synapse_expandables.append(pl)
                    synapse_expander_cores.add_processor(
                        synapse_bin, pl.x, pl.y, pl.p, ExecutableType.SYSTEM)
                    is_expanded = True
            if isinstance(pl.vertex, AbstractNeuronExpandable):
                if (pl.vertex.do_neuron_regeneration() and
                        pl.vertex.gen_neurons_on_machine()):
                    neuron_expandables.append(pl)
                    neuron_expander_cores.add_processor(
                        neuron_bin, pl.x, pl.y, pl.p, ExecutableType.SYSTEM)
                    is_expanded = True
            if is_expanded:
                if isinstance(pl.vertex, AbstractHasAssociatedBinary):
                    vertex_bin = SpynnakerDataView.get_executable_path(
                        pl.vertex.get_binary_file_name())
                    normal_cores.add_processor(
                        vertex_bin, pl.x, pl.y, pl.p,
                        pl.vertex.get_binary_start_type())
                    placements_to_free.add(pl)

    # If we didn't do a reset, we can't re-run the expander
    if not SpynnakerDataView.is_soft_reset():
        return

    # Free recorded data on placements that will be restarted
    buffer_manager = SpynnakerDataView.get_buffer_manager()
    txrx = SpynnakerDataView.get_transceiver()
    app_id = SpynnakerDataView.get_app_id()
    for pl in placements_to_free:
        for region in pl.get_recorded_region_ids():
            addr = buffer_manager.get_recording_address(pl, region)
            if addr is not None:
                txrx.free_sdram(pl.x, pl.y, addr, app_id)

    expander_app_id = SpynnakerDataView.get_new_id()
    progress = ProgressBar(synapse_expander_cores.total_processors,
                           "Re-expanding Synapse Data")
    for pl in synapse_expandables:
        write_address_to_user1(
            pl.x, pl.y, pl.p, pl.vertex.connection_generator_region)
    run_system_application(
        synapse_expander_cores, expander_app_id,
        get_config_bool("Reports", "write_expander_iobuf"),
        None, [CPUState.FINISHED], False,
        "rerun_synapse_expander_on_{}_{}_{}.txt", progress_bar=progress,
        logger=logger)
    progress.end()
    for pl in synapse_expandables:
        pl.vertex.read_generated_connection_holders(pl)

    progress = ProgressBar(neuron_expander_cores.total_processors,
                           "Re-expanding Neuron Data")
    for pl in neuron_expandables:
        write_address_to_user1(
            pl.x, pl.y, pl.p, pl.vertex.neuron_generator_region)
    run_system_application(
        neuron_expander_cores, expander_app_id,
        get_config_bool("Reports", "write_expander_iobuf"),
        None, [CPUState.FINISHED], False,
        "rerun_neuron_expander_on_{}_{}_{}.txt", progress_bar=progress,
        logger=logger)
    progress.end()
    for pl in neuron_expandables:
        pl.vertex.read_generated_initial_values(pl)

    # Reload the binaries we wrote over
    txrx = SpynnakerDataView.get_transceiver()
    app_id = SpynnakerDataView.get_app_id()
    txrx.execute_application(normal_cores, app_id)
