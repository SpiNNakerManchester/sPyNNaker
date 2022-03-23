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

from spinn_front_end_common.interface.interface_functions import (
    graph_data_specification_writer)
from spynnaker.pyNN.models.utility_models.delays import (
    DelayExtensionMachineVertex)


def spynnaker_data_specification_writer(
        placements, hostname, machine, app_id, data_n_timesteps):
    """
    Executes data specification generation for sPyNNaker

    :param ~pacman.model.placements.Placements placements:
        placements of machine graph to cores
    :param str hostname: SpiNNaker machine name
    :param ~spinn_machine.Machine machine:
        the python representation of the SpiNNaker machine
    :param int data_n_timesteps:
        The number of timesteps for which data space will been reserved
    :return: DSG targets (map of placement tuple and filename)
    :rtype:
        tuple(~spinn_front_end_common.interface.ds.DataSpecificationTargets,
        dict(tuple(int,int,int), int))
    :raises ~spinn_front_end_common.exceptions.ConfigurationException:
        If the DSG asks to use more SDRAM than is available.
    """
    # pylint: disable=too-many-arguments, signature-differs

    delay_extensions = list()
    placement_order = list()
    for placement in placements.placements:
        if isinstance(placement.vertex, DelayExtensionMachineVertex):
            delay_extensions.append(placement)
        else:
            placement_order.append(placement)
    placement_order.extend(delay_extensions)

    return graph_data_specification_writer(
        placements, hostname, machine, app_id, data_n_timesteps,
        placement_order)
