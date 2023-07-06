# Copyright (c) 2017 The University of Manchester
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
import logging
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinnman.model.enums import ExecutableType
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.utilities.system_control_logic import (
    run_system_application)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, SYNAPSE_EXPANDER_APLX)

logger = FormatAdapter(logging.getLogger(__name__))


def synapse_expander():
    """
    Run the synapse expander.

    .. note::
        Needs to be done after data has been loaded.
    """
    # Find the places where the synapse expander and delay receivers should run
    expander_cores, expanded_placements, timeout = _plan_expansion()

    if expander_cores.total_processors:
        with ProgressBar(expander_cores.total_processors,
                         "Expanding Synapses") as progress:
            expander_app_id = SpynnakerDataView.get_new_id()
            run_system_application(
                expander_cores, expander_app_id,
                get_config_bool("Reports", "write_expander_iobuf"),
                None, [CPUState.FINISHED], False,
                "synapse_expander_on_{}_{}_{}.txt",
                progress_bar=progress, logger=logger, timeout=timeout)

    # Once expander has run, fill in the connection data.
    if expanded_placements:
        with ProgressBar(len(expanded_placements),
                         "Reading generated connections") as progress:
            for placement in progress.over(expanded_placements):
                placement.vertex.read_generated_connection_holders(placement)


def _plan_expansion():
    """
    Plan the expansion of synapses and set up the regions using USER1.

    :return: The places to load the synapse expander and delay expander
        executables, the target machine vertices to read synapses back from,
        and an estimated timeout for how long the expansion should be let run.
    :rtype: tuple(~.ExecutableTargets, list(~.Placement), float)
    """
    synapse_bin = SpynnakerDataView.get_executable_path(SYNAPSE_EXPANDER_APLX)
    expander_cores = ExecutableTargets()
    expanded_placements = list()
    txrx = SpynnakerDataView.get_transceiver()

    max_data = 0
    max_bit_field = 0
    progress = ProgressBar(
        SpynnakerDataView.get_n_placements(), "Preparing to Expand Synapses")
    for placement in progress.over(SpynnakerDataView.iterate_placemements()):
        # Add all machine vertices of the population vertex to ones
        # that need synapse expansion
        vertex = placement.vertex
        if isinstance(vertex, AbstractSynapseExpandable):
            if vertex.gen_on_machine():
                expander_cores.add_processor(
                    synapse_bin, placement.x, placement.y, placement.p,
                    executable_type=ExecutableType.SYSTEM)
                expanded_placements.append(placement)
                # Write the region to USER1, as that is the best we can do
                txrx.write_user(placement.x, placement.y, placement.p, 1,
                                vertex.connection_generator_region)
                max_data = max(max_data, vertex.max_gen_data)
                max_bit_field = max(max_bit_field, vertex.bit_field_size)

    # Allow 1 seconds per ~1000 synapses, with minimum of 2 seconds
    timeout = max(2.0, max_data / 1000.0)
    # Also allow 1s per 1000 bytes of bitfields
    timeout += max(2.0, max_bit_field / 1000.0)
    return expander_cores, expanded_placements, timeout
