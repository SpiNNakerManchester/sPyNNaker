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
from typing import List, Tuple
from spinn_utilities.log import FormatAdapter
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.progress_bar import ProgressBar
from spinnman.model.enums import ExecutableType, CPUState, UserRegister
from spinnman.model import ExecutableTargets
from pacman.model.placements import Placement
from spinn_front_end_common.utilities.system_control_logic import (
    run_system_application)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractNeuronExpandable, NEURON_EXPANDER_APLX)

logger = FormatAdapter(logging.getLogger(__name__))


def neuron_expander() -> None:
    """
    Run the neuron expander.

    .. note::
        Needs to be done after data has been loaded.
    """
    # Find the places where the neuron expander should run
    expander_cores, expanded_pop_vertices = _plan_expansion()

    with ProgressBar(expander_cores.total_processors,
                     "Expanding Neuron Data") as progress:
        expander_app_id = SpynnakerDataView.get_new_id()
        run_system_application(
            expander_cores, expander_app_id,
            get_config_bool("Reports", "write_expander_iobuf") or False,
            None, frozenset({CPUState.FINISHED}), False,
            "neuron_expander_on_{}_{}_{}.txt", progress_bar=progress,
            logger=logger)

    _fill_in_initial_data(expanded_pop_vertices)


def _plan_expansion() -> Tuple[
        ExecutableTargets, List[Tuple[AbstractNeuronExpandable, Placement]]]:
    """
    Plan the expansion of neurons and set up the regions using USER1.
    """
    neuron_bin = SpynnakerDataView.get_executable_path(NEURON_EXPANDER_APLX)
    txrx = SpynnakerDataView.get_transceiver()

    expander_cores = ExecutableTargets()
    expanded_pop_vertices: List[
        Tuple[AbstractNeuronExpandable, Placement]] = list()
    to_write: List[Tuple[int, int, int, UserRegister, int]] = []
    for placement in SpynnakerDataView.iterate_placemements():
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
                to_write.append((
                    *placement.location, UserRegister.USER_1,
                    vertex.neuron_generator_region))

    txrx.write_user_many(to_write, "preparing to expand neuron data")
    return expander_cores, expanded_pop_vertices


def _fill_in_initial_data(expanded_pop_vertices: List[
        Tuple[AbstractNeuronExpandable, Placement]]) -> None:
    """
    Once expander has run, fill in the connection data.

    :param expanded_pop_vertices: List of machine vertices to read data from
    """
    progress = ProgressBar(
        len(expanded_pop_vertices), "Getting initial values")
    for vertex, placement in progress.over(expanded_pop_vertices):
        vertex.read_generated_initial_values(placement)
