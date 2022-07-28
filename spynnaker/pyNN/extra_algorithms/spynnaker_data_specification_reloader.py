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
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.config_holder import get_config_bool
from spinn_machine.sdram import SDRAM
from data_specification.data_specification_generator import (
    DataSpecificationGenerator)
from data_specification import DataSpecificationExecutor
from data_specification.constants import MAX_MEM_REGIONS
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.abstract_models import (
    AbstractRewritesDataSpecification)
from spinn_front_end_common.interface.ds import DsSqlliteDatabase
from spinn_front_end_common.utilities.utility_calls import (
    get_report_writer, get_region_base_address_offset)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.utilities.system_control_logic import (
    run_system_application)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, AbstractNeuronExpandable, SYNAPSE_EXPANDER_APLX,
    NEURON_EXPANDER_APLX)
import io
import numpy
import logging

logger = logging.getLogger(__name__)


def spynnaker_data_specification_reloader():

    targets = DsSqlliteDatabase()
    targets.clear_ds()

    synapse_bin = SpynnakerDataView.get_executable_path(SYNAPSE_EXPANDER_APLX)
    neuron_bin = SpynnakerDataView.get_executable_path(NEURON_EXPANDER_APLX)

    progress = ProgressBar(
        SpynnakerDataView.get_n_placements(), "Reloading data")

    expander_cores = ExecutableTargets()
    synapse_expandables = list()
    neuron_expandables = list()
    for pl in progress.over(SpynnakerDataView.iterate_placemements()):
        # Generate the data spec for the placement if needed
        if _regenerate_data_spec_for_vertices(pl, targets):
            if isinstance(pl.vertex, AbstractSynapseExpandable):
                if pl.vertex.gen_on_machine():
                    synapse_expandables.append(pl)
                    expander_cores.add_processor(
                        synapse_bin, pl.x, pl.y, pl.p, ExecutableType.SYSTEM)
            if isinstance(pl.vertex, AbstractNeuronExpandable):
                if pl.vertex.gen_neurons_on_machine():
                    neuron_expandables.append(pl)
                    expander_cores.add_procesor(
                        neuron_bin, pl.x, pl.y, pl.p, ExecutableType.SYSTEM)

    progress = ProgressBar(expander_cores.total_processors,
                           "Re-expanding Synapse and Neuron Data")
    expander_app_id = SpynnakerDataView.get_new_id()
    run_system_application(
        expander_cores, expander_app_id,
        get_config_bool("Reports", "write_expander_iobuf"),
        None, [CPUState.FINISHED], False,
        "rerun_expander_on_{}_{}_{}.txt", progress_bar=progress,
        logger=logger)
    progress.end()

    for pl in synapse_expandables:
        pl.vertex.read_generated_connection_holders(pl)
    for pl in neuron_expandables:
        pl.vertex.read_generated_initial_values(pl)


def _regenerate_data_spec_for_vertices(pl, targets):
    """
    :param ~.Placement placement:
    """
    vertex = pl.vertex

    # If the vertex doesn't regenerate, skip
    if not isinstance(vertex, AbstractRewritesDataSpecification):
        return False

    # If the vertex doesn't require regeneration, skip
    if not vertex.reload_required():
        return False

    with targets.create_data_spec(pl.x, pl.y, pl.p) as data_writer:
        report_writer = get_report_writer(pl.x, pl.y, pl.p)
        spec = DataSpecificationGenerator(data_writer, report_writer)
        vertex.regenerate_data_specification(spec, pl)

    with io.BytesIO(targets.get_ds(pl.x, pl.y, pl.p)) as spec_reader:
        data_spec_executor = DataSpecificationExecutor(
            spec_reader, SDRAM.max_sdram_found)
        data_spec_executor.execute()

    # Read the region table for the placement
    txrx = SpynnakerDataView.get_transceiver()
    regions_base_address = txrx.get_cpu_information_from_core(
        pl.x, pl.y, pl.p).user[0]
    start_region = get_region_base_address_offset(regions_base_address, 0)
    table_size = get_region_base_address_offset(
        regions_base_address, MAX_MEM_REGIONS) - start_region
    ptr_table = numpy.frombuffer(txrx.read_memory(
        pl.x, pl.y, start_region, table_size),
        dtype=DataSpecificationExecutor.TABLE_TYPE)

    # Write the regions to the machine
    for i, region in enumerate(data_spec_executor.dsef.mem_regions):
        if region is not None and not region.unfilled:
            txrx.write_memory(
                pl.x, pl.y, ptr_table[i]["pointer"],
                region.region_data[:region.max_write_pointer])
    vertex.set_reload_required(False)
    return True
