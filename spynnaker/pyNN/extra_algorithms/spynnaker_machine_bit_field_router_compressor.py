# Copyright (c) 2019-2020 The University of Manchester
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
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.log import FormatAdapter
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.interface.interface_functions.\
    machine_bit_field_router_compressor import (
        machine_bit_field_ordered_covering_compressor,
        machine_bit_field_pair_router_compressor)
from spinn_front_end_common.utilities.helpful_functions import (
    write_address_to_user1)
from spinn_front_end_common.utilities.system_control_logic import (
    run_system_application)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, SYNAPSE_EXPANDER_APLX)

logger = FormatAdapter(logging.getLogger(__name__))


_RERUN_IOBUF_NAME_PATTERN = "rerun_of_synaptic_expander_on_{}_{}_{}.txt"


def _locate_expander_rerun_targets(bitfield_targets):
    """ removes host based cores for synaptic matrix regeneration

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
        write_address_to_user1(
            placement.x, placement.y, placement.p,
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
    """ reruns the synaptic expander

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
    """ entrance for routing table compression with bit field

    """
    compressor_executable_targets = \
        machine_bit_field_ordered_covering_compressor()

    # adjust cores to exclude the ones which did not give sdram.
    expander_chip_cores = _locate_expander_rerun_targets(
        compressor_executable_targets)

    # just rerun the synaptic expander for safety purposes
    _rerun_synaptic_cores(expander_chip_cores, True)


def spynnaker_machine_bitField_pair_router_compressor():
    """ entrance for routing table compression with bit field

    """
    compressor_executable_targets = \
        machine_bit_field_pair_router_compressor()

    # adjust cores to exclude the ones which did not give sdram.
    expander_chip_cores = _locate_expander_rerun_targets(
        compressor_executable_targets)

    # just rerun the synaptic expander for safety purposes
    _rerun_synaptic_cores(expander_chip_cores, True)
