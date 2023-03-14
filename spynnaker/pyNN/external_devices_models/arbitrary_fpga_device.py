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

from pacman.model.graphs.application import (
    ApplicationFPGAVertex, FPGAConnection)
from spynnaker.pyNN.models.common import PopulationApplicationVertex


class ArbitraryFPGADevice(ApplicationFPGAVertex, PopulationApplicationVertex):
    __slots__ = []

    def __init__(
            self, n_neurons, fpga_link_id, fpga_id, board_address=None,
            chip_coords=None, label=None):
        """
        :param int n_neurons: Number of neurons
        :param int fpga_link_id:
        :param int fpga_id:
        :param board_address:
        :type board_address: str or None
        :param chip_coords:
        :type chip_coords: tuple(int, int) or None
        :param label:
        :type label: str or None
        """
        # pylint: disable=too-many-arguments
        conn = FPGAConnection(
            fpga_id, fpga_link_id, board_address, chip_coords)
        super().__init__(n_neurons, [conn], conn, label)
