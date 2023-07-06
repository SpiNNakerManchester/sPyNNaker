# Copyright (c) 2019 The University of Manchester
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
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState, ExecutableType
from spinn_front_end_common.interface.interface_functions.\
    machine_bit_field_router_compressor import (
        machine_bit_field_ordered_covering_compressor,
        machine_bit_field_pair_router_compressor)
from spinn_front_end_common.utilities.system_control_logic import (
    run_system_application)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, SYNAPSE_EXPANDER_APLX)

logger = FormatAdapter(logging.getLogger(__name__))


_RERUN_IOBUF_NAME_PATTERN = "rerun_of_synaptic_expander_on_{}_{}_{}.txt"


def _locate_expander_rerun_targets(bitfield_targets):
    """
    Removes host based cores for synaptic matrix regeneration.

    :param ~.ExecutableTargets bitfield_targets: the cores that were used
    :return: new targets for synaptic expander
    :rtype: ~.ExecutableTargets
    """
    # locate expander executable path
    expander_executable_path = SpynnakerDataView.get_executable_path(
        SYNAPSE_EXPANDER_APLX)

    # if any ones are going to be ran on host, ignore them from the new
    # core setup
    new_cores = ExecutableTargets()
    for placement in __machine_expandables(bitfield_targets.all_core_subsets):
        new_cores.add_processor(
            expander_executable_path,
            placement.x, placement.y, placement.p,
            executable_type=ExecutableType.SYSTEM)
        # Write the region to USER1, as that is the best we can do
        txrx = SpynnakerDataView.get_transceiver()
        txrx.write_user(placement.x, placement.y, placement.p, 1,
                        placement.vertex.connection_generator_region)
    return new_cores


def __machine_expandables(cores):
    """
    :param ~.CoreSubsets cores:
    :rtype: iterable(~.Placement)
    """
    for place in SpynnakerDataView.iterate_placemements():
        vertex = place.vertex
        if (cores.is_core(place.x, place.y, place.p)
                # Can we fix it by rerunning?
                and isinstance(vertex, AbstractSynapseExpandable)
                and vertex.gen_on_machine()):
            yield place


def _rerun_synaptic_cores(
        synaptic_expander_rerun_cores, needs_sync_barrier):
    """
    Reruns the synaptic expander.

    :param ~.ExecutableTargets synaptic_expander_rerun_cores:
        the cores to rerun the synaptic matrix generator for
    :param bool needs_sync_barrier:
    """
    if synaptic_expander_rerun_cores.total_processors:
        logger.info("rerunning synaptic expander")
        expander_app_id = SpynnakerDataView.get_new_id()
        run_system_application(
            synaptic_expander_rerun_cores, expander_app_id,
            get_config_bool("Reports", "write_expander_iobuf"),
            None, [CPUState.FINISHED], needs_sync_barrier,
            _RERUN_IOBUF_NAME_PATTERN)


def spynnaker_machine_bitfield_ordered_covering_compressor():
    """
    Perform routing table compression using ordered coverings with bit fields.
    """
    compressor_executable_targets = \
        machine_bit_field_ordered_covering_compressor()

    # adjust cores to exclude the ones which did not give sdram.
    expander_chip_cores = _locate_expander_rerun_targets(
        compressor_executable_targets)

    # just rerun the synaptic expander for safety purposes
    _rerun_synaptic_cores(expander_chip_cores, True)


def spynnaker_machine_bitField_pair_router_compressor():
    """
    Perform routing table compression using pairs with bit fields.
    """
    compressor_executable_targets = \
        machine_bit_field_pair_router_compressor()

    # adjust cores to exclude the ones which did not give sdram.
    expander_chip_cores = _locate_expander_rerun_targets(
        compressor_executable_targets)

    # just rerun the synaptic expander for safety purposes
    _rerun_synaptic_cores(expander_chip_cores, True)
