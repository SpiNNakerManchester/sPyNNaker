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
from spinn_utilities.log import FormatAdapter
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.progress_bar import ProgressBar
from spinn_front_end_common.utilities.system_control_logic import \
    run_system_application
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.utilities.helpful_functions import (
    write_address_to_user1)
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractNeuronExpandable, NEURON_EXPANDER_APLX)

logger = FormatAdapter(logging.getLogger(__name__))


def neuron_expander():
    """ Run the neuron expander.

    .. note::
        Needs to be done after data has been loaded.
    """

    # Find the places where the neuron expander should run
    expander_cores, expanded_pop_vertices = _plan_expansion()

    progress = ProgressBar(expander_cores.total_processors,
                           "Expanding Neuron Data")
    expander_app_id = SpynnakerDataView.get_new_id()
    run_system_application(
        expander_cores, expander_app_id,
        get_config_bool("Reports", "write_expander_iobuf"),
        None, [CPUState.FINISHED], False,
        "neuron_expander_on_{}_{}_{}.txt", progress_bar=progress,
        logger=logger)
    progress.end()

    _fill_in_initial_data(expanded_pop_vertices)


def _plan_expansion():
    """ Plan the expansion of neurons and set up the regions using USER1

    :rtype: (ExecutableTargets, list(MachineVertex, Placement))
    """
    neuron_bin = SpynnakerDataView.get_executable_path(NEURON_EXPANDER_APLX)

    expander_cores = ExecutableTargets()
    expanded_pop_vertices = list()

    progress = ProgressBar(
        SpynnakerDataView.get_n_placements(),
        "Preparing to Expand Neuron Data")
    for placement in progress.over(SpynnakerDataView.iterate_placemements()):
        # Add all machine vertices of the population vertex to ones
        # that need synapse expansion
        vertex = placement.vertex
        if isinstance(vertex, AbstractNeuronExpandable):
            if vertex.gen_neurons_on_machine():
                expanded_pop_vertices.append((vertex, placement))
                expander_cores.add_processor(
                    neuron_bin, placement.x, placement.y, placement.p,
                    executable_type=ExecutableType.SYSTEM)
                # Write the region to USER1, as that is the best we can do
                write_address_to_user1(
                    placement.x, placement.y, placement.p,
                    vertex.neuron_generator_region)

    return expander_cores, expanded_pop_vertices


def _fill_in_initial_data(expanded_pop_vertices):
    """ Once expander has run, fill in the connection data

    :param list(MachineVertex, Placement) expanded_pop_vertices:
        List of machine vertices to read data from
    :param ~spinnman.transceiver.Transceiver transceiver:
        How to talk to the machine

    :rtype: None
    """
    progress = ProgressBar(
        len(expanded_pop_vertices), "Getting initial values")
    for vertex, placement in progress.over(expanded_pop_vertices):
        vertex.read_generated_initial_values(placement)
