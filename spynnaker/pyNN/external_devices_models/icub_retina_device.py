# Copyright (c) 2021 The University of Manchester
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
from math import ceil, log2
from typing import Dict, Optional
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import Application2DSpiNNakerLinkVertex
from pacman.model.graphs.common import Slice
from pacman.model.routing_info.base_key_and_mask import BaseKeyAndMask
from pacman.utilities.constants import BITS_IN_KEY
from pacman.utilities.utility_calls import is_power_of_2


class ICUBRetinaDevice(Application2DSpiNNakerLinkVertex):
    """
    An ICUB retina device connected to SpiNNaker using a SpiNNakerLink.
    """

    __slots__ = (
        "__index_by_slice",
        "__base_key")

    def __init__(self, base_key: int = 0, width: int = 304, height: int = 240,
                 sub_width: int = 16, sub_height: int = 16,
                 spinnaker_link_id: int = 0,
                 board_address: Optional[str] = None):
        """
        :param int base_key: The key that is common over the whole vertex
        :param int width: The width of the retina in pixels
        :param int height: The height of the retina in pixels
        :param int sub_width:
            The width of rectangles to split the retina into for efficiency of
            sending
        :param int sub_height:
            The height of rectangles to split the retina into for efficiency of
            sending
        :param int spinnaker_link_id:
            The ID of the SpiNNaker link that the device is connected to
        :param board_address:
            The board to which the device is connected,
            or `None` for the first board
        :type board_address: str or None
        """
        # Fake the width if not a power of 2, as we need this for the sake
        # of passing on to other 2D vertices
        if not is_power_of_2(width):
            width = 2 ** int(ceil(log2(width)))

        # Call the super
        super().__init__(
            width, height, sub_width, sub_height, spinnaker_link_id,
            board_address, incoming=True, outgoing=True)

        # A dictionary to get vertex index from FPGA and slice
        self.__index_by_slice: Dict[Slice, int] = dict()
        self.__base_key = base_key

    @overrides(Application2DSpiNNakerLinkVertex.get_incoming_slice)
    def get_incoming_slice(self, index: int) -> Slice:
        vertex_slice = super().get_incoming_slice(index)
        self.__index_by_slice[vertex_slice] = index
        return vertex_slice

    @overrides(Application2DSpiNNakerLinkVertex.get_machine_fixed_key_and_mask)
    def get_machine_fixed_key_and_mask(self, machine_vertex, partition_id):
        vertex_slice = machine_vertex.vertex_slice
        index = self.__index_by_slice[vertex_slice]
        return self._get_key_and_mask(self.__base_key, index)

    @overrides(Application2DSpiNNakerLinkVertex.get_fixed_key_and_mask)
    def get_fixed_key_and_mask(self, partition_id) -> BaseKeyAndMask:
        n_key_bits = BITS_IN_KEY - self._key_shift
        key_mask = ((1 << n_key_bits) - 1) << self._key_shift
        return BaseKeyAndMask(self.__base_key << self._key_shift, key_mask)

    @property
    def _source_x_mask(self) -> int:
        return ((1 << self._x_bits) - 1) << 1

    @property
    def _source_x_shift(self) -> int:
        return 1

    @property
    def _source_y_mask(self) -> int:
        return ((1 << self._y_bits) - 1) << 12

    @property
    def _source_y_shift(self) -> int:
        return 12

    @property
    def _key_shift(self) -> int:
        return 20
