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
from pacman.model.graphs.application import (
    ApplicationFPGAVertex, FPGAConnection)
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from .spif_devices import SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK


class SPIFOutputDevice(
        ApplicationFPGAVertex, PopulationApplicationVertex,
        AbstractSendMeMulticastCommandsVertex):
    """ Output (only) to a SPIF device
    """

    def __init__(self, n_atoms, board_address=None, chip_coords=None,
                 label=None):
        super(SPIFOutputDevice, self).__init__(
            n_atoms,
            outgoing_fpga_connection=FPGAConnection(
                SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK, board_address,
                chip_coords),
            label=label)
