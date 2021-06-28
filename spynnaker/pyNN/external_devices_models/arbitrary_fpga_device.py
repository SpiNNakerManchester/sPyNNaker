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

from pacman.model.graphs.application import ApplicationFPGAVertex
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from pacman.model.graphs.application import FPGAConnection


class ArbitraryFPGADevice(
        ApplicationFPGAVertex, ProvidesKeyToAtomMappingImpl):
    __slots__ = []

    def __init__(
            self, n_neurons, fpga_link_id, fpga_id, board_address=None,
            label=None):
        """
        :param int n_neurons: Number of neurons
        :param int fpga_link_id:
        :param int fpga_id:
        :param board_address:
        :type board_address: str or None
        :param label:
        :type label: str or None
        """
        # pylint: disable=too-many-arguments
        conn = FPGAConnection(fpga_id, fpga_link_id, board_address)
        super().__init__(n_neurons, [conn], conn, label)
