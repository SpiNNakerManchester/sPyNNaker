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
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spinn_front_end_common.utilities.system_control_logic import \
    run_system_application
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, SYNAPSE_EXPANDER_APLX)
from spinn_front_end_common.utilities.helpful_functions import (
    write_address_to_user1)

logger = FormatAdapter(logging.getLogger(__name__))


def synapse_expander():
    """ Run the synapse expander.

    .. note::
        Needs to be done after data has been loaded.

    """

    # Find the places where the synapse expander and delay receivers should run
    expander_cores, expanded_pop_vertices, max_data, max_bf = _plan_expansion()

    # Allow 1 seconds per ~1000 synapses, with minimum of 2 seconds
    timeout = max(2.0, max_data / 1000.0)
    # Also allow 1s per 1000 bytes of bitfields
    timeout += max(2.0, max_bf / 1000.0)

    progress = ProgressBar(expander_cores.total_processors,
                           "Expanding Synapses")
    expander_app_id = SpynnakerDataView.get_new_id()
    run_system_application(
        expander_cores, expander_app_id,
        get_config_bool("Reports", "write_expander_iobuf"),
        None, [CPUState.FINISHED], False,
        "synapse_expander_on_{}_{}_{}.txt", progress_bar=progress,
        logger=logger, timeout=timeout)
    progress.end()
    _fill_in_connection_data(expanded_pop_vertices)


def _plan_expansion():
    """ Plan the expansion of synapses and set up the regions using USER1

    :return: The places to load the synapse expander and delay expander
        executables, and the target machine vertices to read synapses back from
    :rtype: (ExecutableTargets, list(MachineVertex, Placement))
    """
    synapse_bin = SpynnakerDataView.get_executable_path(SYNAPSE_EXPANDER_APLX)
    expander_cores = ExecutableTargets()
    expanded_pop_vertices = list()

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
                expanded_pop_vertices.append((vertex, placement))
                # Write the region to USER1, as that is the best we can do
                write_address_to_user1(
                    placement.x, placement.y, placement.p,
                    vertex.connection_generator_region)
                max_data = max(max_data, vertex.max_gen_data)
                max_bit_field = max(max_bit_field, vertex.bit_field_size)

    return expander_cores, expanded_pop_vertices, max_data, max_bit_field


def _fill_in_connection_data(expanded_pop_vertices):
    """ Once expander has run, fill in the connection data

    :param list(MachineVertex, Placement) expanded_pop_vertices:
        List of machine vertices to read data from

    :rtype: None
    """
    for vertex, placement in expanded_pop_vertices:
        vertex.read_generated_connection_holders(placement)
