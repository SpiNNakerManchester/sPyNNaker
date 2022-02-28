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
from spinn_utilities.progress_bar import ProgressBar
from spinn_front_end_common.utilities.system_control_logic import \
    run_system_application
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.models.abstract_models import (
    AbstractNeuronExpandable, NEURON_EXPANDER_APLX)
from spinn_front_end_common.utilities.helpful_functions import (
    write_address_to_user1)

logger = FormatAdapter(logging.getLogger(__name__))


def neuron_expander(
        placements, transceiver, executable_finder, extract_iobuf):
    """ Run the neuron expander.

    .. note::
        Needs to be done after data has been loaded.

    :param ~pacman.model.placements.Placements placements:
        Where all vertices are on the machine.
    :param ~spinnman.transceiver.Transceiver transceiver:
        How to talk to the machine.
    :param executable_finder:
        How to find the synapse expander binaries.
    :param bool extract_iobuf: flag for extracting iobuf
    :type executable_finder:
        ~spinn_utilities.executable_finder.ExecutableFinder
    """
    neuron_bin = executable_finder.get_executable_path(NEURON_EXPANDER_APLX)

    # Find the places where the neuron expander should run
    expander_cores = _plan_expansion(placements, neuron_bin, transceiver)

    progress = ProgressBar(expander_cores.total_processors,
                           "Expanding Neuron Data")
    expander_app_id = transceiver.app_id_tracker.get_new_id()
    run_system_application(
        expander_cores, expander_app_id, transceiver, executable_finder,
        extract_iobuf, None, [CPUState.FINISHED], False,
        "neuron_expander_on_{}_{}_{}.txt", progress_bar=progress,
        logger=logger)
    progress.end()


def _plan_expansion(placements, synapse_expander_bin, transceiver):
    """ Plan the expansion of synapses and set up the regions using USER1

    :param ~pacman.model.placements.Placements: The placements of the vertices
    :param str synapse_expander_bin: The binary name of the synapse expander
    :param ~spinnman.transceiver.Transceiver transceiver:
        How to talk to the machine
    :return: The places to load the synapse expander and delay expander
        executables, and the target machine vertices to read synapses back from
    :rtype: (ExecutableTargets, list(MachineVertex, Placement))
    """
    expander_cores = ExecutableTargets()

    progress = ProgressBar(len(placements), "Preparing to Expand Synapses")
    for placement in progress.over(placements):
        # Add all machine vertices of the population vertex to ones
        # that need synapse expansion
        vertex = placement.vertex
        if isinstance(vertex, AbstractNeuronExpandable):
            if vertex.gen_neurons_on_machine():
                expander_cores.add_processor(
                    synapse_expander_bin,
                    placement.x, placement.y, placement.p,
                    executable_type=ExecutableType.SYSTEM)
                # Write the region to USER1, as that is the best we can do
                write_address_to_user1(
                    transceiver, placement.x, placement.y, placement.p,
                    vertex.neuron_generator_region)

    return expander_cores
