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
from pacman.model.graphs.application import ApplicationFPGAVertex
from pacman.utilities.constants import BITS_IN_KEY
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints)
from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyAndMaskConstraint)
from pacman.model.graphs.application import FPGAConnection
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
import math


class SPIFRetinaDevice(
        ApplicationFPGAVertex, AbstractProvidesOutgoingPartitionConstraints):
    """ A retina device connected to SpiNNaker using a SPIF board.
    """

    #: SPIF outputs to 8 FPGA output links, so we split into (2 x 4), meaning
    #: a mask of (1 x 3)
    Y_MASK = 1

    #: See Y_MASK for description
    X_MASK = 3

    #: The number of X values per row
    X_PER_ROW = 4

    #: There is 1 bit for polarity in the key
    N_POLARITY_BITS = 1

    def __init__(self, base_key, width, height, sub_width, sub_height):
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
        """
        if sub_width < self.X_MASK or sub_height < self.Y_MASK:
            raise ConfigurationException(
                "The sub-squares must be >=4 x >= 2"
                f" ({sub_width} x {sub_height} specified)")

        if (not self.__is_power_of_2(sub_width) or
                not self.__is_power_of_2(sub_height)):
            raise ConfigurationException(
                f"sub_width ({sub_width}) and sub_height ({sub_height}) must"
                " each be a power of 2")
        n_sub_squares = self.__n_sub_squares(
            width, height, sub_width, sub_height)
        super().__init__(
            width * height, self.__incoming_fpgas, self.__outgoing_fpga,
            n_machine_vertices_per_link=n_sub_squares)

        # The mask is going to be made up of:
        # | K | P | Y_I | Y_0 | Y_F | X_I | X_0 | X_F |
        # K = base key
        # P = polarity (0 as not cared about)
        # Y_I = y index of sub-square
        # Y_0 = 0s for values not cared about in Y
        # Y_F = FPGA y index
        # X_I = x index of sub-square
        # X_0 = 0s for values not cared about in X
        # X_F = FPGA x index
        # Now - go calculate:
        x_bits = get_n_bits(width)
        y_bits = get_n_bits(height)

        self.__n_squares_per_row = int(math.ceil(width / sub_width))
        n_squares_per_col = int(math.ceil(height / sub_height))
        sub_x_bits = get_n_bits(self.__n_squares_per_row)
        sub_y_bits = get_n_bits(n_squares_per_col)
        sub_x_mask = (1 << sub_x_bits) - 1
        sub_y_mask = (1 << sub_y_bits) - 1

        key_shift = y_bits + x_bits + self.N_POLARITY_BITS
        n_key_bits = BITS_IN_KEY - key_shift
        key_mask = (1 << n_key_bits) - 1

        self.__fpga_y_shift = x_bits
        self.__x_index_shift = x_bits - sub_x_bits
        self.__y_index_shift = x_bits + (y_bits - sub_y_bits)
        self.__fpga_mask = (
            (key_mask << key_shift) +
            (sub_y_mask << self.__y_index_shift) +
            (self.Y_MASK << self.__fpga_y_shift) +
            (sub_x_mask << self.__x_index_shift) +
            self.X_MASK)
        self.__key_bits = base_key << key_shift

        # A dictionary of seen machine vertex to index
        self.__machine_vertex_index = dict()

        # A map of the next machine vertex index to use for each FPGA link
        self.__fpga_next_index = [0 for _ in range(8)]

    def __n_sub_squares(self, width, height, sub_width, sub_height):
        """ Get the number of sub-squares in an image

        :param int width: The width of the image
        :param int height: The height of the image
        :param int sub_width: The width of the sub-square
        :param int sub_height: The height of the sub-square
        :rtype: int
        """
        return (int(math.ceil(width / sub_width)) *
                int(math.ceil(height / sub_height)))

    def __is_power_of_2(self, v):
        """ Determine if a value is a power of 2

        :param int v: The value to test
        :rtype: bool
        """
        return 2 ** int(math.log2(v)) == v

    @property
    def __incoming_fpgas(self):
        """ Get the incoming FPGA connections

        :rtype: list(FPGAConnection)
        """
        # We use every other odd link
        return [FPGAConnection(0, i, None) for i in range(1, 16, 2)]

    @property
    def __outgoing_fpga(self):
        """ Get the outgoing FPGA connection

        :rtype: None
        """
        return None

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        pre = partition.pre_vertex

        # We use every other odd link, so we can work out the "index" of the
        # link in the list as follows, and we can then split the index into
        # x and y components
        fpga_index = (pre.fpga_link_id - 1) // 2
        fpga_x_index = fpga_index % self.X_PER_ROW
        fpga_y_index = fpga_index // self.X_PER_ROW

        # Work out the machine vertex index
        v_index = self.__machine_vertex_index.get(pre, None)
        if v_index is None:
            v_index = self.__fpga_next_index[fpga_index]
            self.__machine_vertex_index[pre] = v_index
            self.__fpga_next_index[fpga_index] += 1
        v_x_index = v_index % self.__n_squares_per_row
        v_y_index = v_index // self.__n_squares_per_row

        # Finally we build the key from the components
        fpga_key = (
            self.__key_bits +
            (v_y_index << self.__y_index_shift) +
            (fpga_y_index << self.__fpga_y_shift) +
            (v_x_index << self.__x_index_shift) +
            fpga_x_index)
        return [FixedKeyAndMaskConstraint([
            BaseKeyAndMask(fpga_key, self.__fpga_mask)])]
