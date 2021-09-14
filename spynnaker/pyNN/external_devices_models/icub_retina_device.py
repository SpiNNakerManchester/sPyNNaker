# Copyright (c) 2021 The University of Manchester
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
from spinn_utilities.overrides import overrides
from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyAndMaskConstraint)
from pacman.model.graphs.application import Application2DSpiNNakerLinkVertex
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints)
from spynnaker.pyNN.models.abstract_models import HasShapeKeyFields


class ICUBRetinaDevice(
        Application2DSpiNNakerLinkVertex,
        AbstractProvidesOutgoingPartitionConstraints,
        HasShapeKeyFields):
    """ An ICUB retina device connected to SpiNNaker using a SpiNNakerLink
    """

    __slots__ = [
        "__index_by_slice",
        "__base_key"]

    def __init__(self, base_key=0, width=304, height=240, sub_width=16,
                 sub_height=16, spinnaker_link_id=0, board_address=None):
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
            or None for the first board
        :type board_address: str or None
        """
        # Call the super
        super().__init__(
            width, height, sub_width, sub_height, spinnaker_link_id,
            board_address, incoming=True, outgoing=True)

        # A dictionary to get vertex index from FPGA and slice
        self.__index_by_slice = dict()
        self.__base_key = base_key

    @overrides(Application2DSpiNNakerLinkVertex.get_incoming_slice)
    def get_incoming_slice(self, index):
        vertex_slice = super(
            ICUBRetinaDevice, self).get_incoming_slice(index)
        self.__index_by_slice[vertex_slice] = index
        return vertex_slice

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        machine_vertex = partition.pre_vertex
        vertex_slice = machine_vertex.vertex_slice
        index = self.__index_by_slice[vertex_slice]
        return [FixedKeyAndMaskConstraint([
            self._get_key_and_mask(self.__base_key, index)])]

    @overrides(HasShapeKeyFields.get_shape_key_fields)
    def get_shape_key_fields(self, vertex_slice):
        return self._key_fields
