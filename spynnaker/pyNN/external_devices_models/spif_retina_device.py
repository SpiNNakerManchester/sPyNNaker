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
from pacman.model.graphs.application import ApplicationFPGAVertex
from pacman.model.graphs.common import Slice
from pacman.utilities.constants import BITS_IN_KEY
from pacman.model.graphs.application import FPGAConnection
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints,
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utility_models import MultiCastCommand
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.models.abstract_models import HasShapeKeyFields
import math
from enum import IntEnum

_REPEATS = 2
_DELAY_BETWEEN_REPEATS = 1

#: Base key to send packets to SpiNNaker FPGA (add register offset)
_LC_KEY = 0xFFFFFE00

#: Base key to send packets to SPIF (add register offset)
_RC_KEY = 0xFFFFFF00

#: The standard shift and mask for polarity from SPIF inputs
_POLARITY_MASK = 0x00008000
_POLARITY_SHIFT = 15

#: The standard shift and mask for the X coordinate from SPIF inputs
_X_MASK = 0x7FFF0000
_X_SHIFT = 16

#: The standard shift and mask for the Y coordinate from SPIF  inputs
_Y_MASK = 0x00007FFF
_Y_SHIFT = 0


class _SPIFRegister(IntEnum):
    MP_KEY = 1
    REPLY_KEY = 2
    IR_KEY_BASE = 16
    IR_MASK_BASE = 32
    IR_ROUTE_BASE = 48
    OUT_PERIPH_PKT_CNT = 64
    CONFIG_PKT_CNT = 65
    DROPPED_PKT_CNT = 66
    IN_PERIPH_PKT_CNT = 67
    DIAG_PKT_CNT = 68
    MP_FLD_MASK_BASE = 80
    MP_FLD_SHIFT_BASE = 96

    def cmd(self, payload=None, index=0):
        return MultiCastCommand(
            _RC_KEY + self.value + index, payload, time=None, repeat=_REPEATS,
            delay_between_repeats=_DELAY_BETWEEN_REPEATS)


def set_field_mask(index, mask):
    return _SPIFRegister.MP_FLD_MASK_BASE.cmd(mask, index)


def set_field_shift(index, shift):
    return _SPIFRegister.MP_FLD_SHIFT_BASE.cmd(shift, index)


def set_input_key(index, key):
    return _SPIFRegister.IR_KEY_BASE.cmd(key, index)


def set_input_mask(index, mask):
    return _SPIFRegister.IR_MASK_BASE.cmd(mask, index)


def set_input_route(index, route):
    return _SPIFRegister.IR_ROUTE_BASE.cmd(route, index)


class _SpiNNFPGARegister(IntEnum):
    P_KEY = 2
    P_MASK = 3
    LC_KEY = 12
    LC_MASK = 13
    RC_KEY = 14
    RC_MASK = 15
    STOP = 16
    START = 17

    def cmd(self, payload=None):
        return MultiCastCommand(
            _LC_KEY + self.value, payload, time=None, repeat=_REPEATS,
            delay_between_repeats=_DELAY_BETWEEN_REPEATS)


class SPIFRetinaDevice(
        ApplicationFPGAVertex, AbstractProvidesOutgoingPartitionConstraints,
        AbstractSendMeMulticastCommandsVertex, HasShapeKeyFields):
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

    __slots__ = [
        "__width",
        "__height",
        "__sub_width",
        "__sub_height",
        "__n_atoms_per_subsquare",
        "__n_squares_per_col",
        "__n_squares_per_row",
        "__key_bits",
        "__fpga_mask",
        "__spif_mask",
        "__fpga_x_shift",
        "__fpga_y_shift",
        "__x_index_shift",
        "__y_index_shift",
        "__index_by_slice",
        "__base_key",
        "__x_bits",
        "__y_bits",
        "__source_x_shift",
        "__source_x_mask",
        "__source_y_shift",
        "__source_y_mask"]

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
        # Do some checks
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

        # Call the super
        super().__init__(
            width * height, self.__incoming_fpgas, self.__outgoing_fpga,
            n_machine_vertices_per_link=n_sub_squares)

        # Store information needed later
        self.__width = width
        self.__height = height
        self.__sub_width = sub_width
        self.__sub_height = sub_height
        self.__n_atoms_per_subsquare = sub_width * sub_height

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
        self.__n_squares_per_col = int(math.ceil(height / sub_height))
        sub_x_bits = get_n_bits(self.__n_squares_per_row)
        sub_y_bits = get_n_bits(self.__n_squares_per_col)
        sub_x_mask = (1 << sub_x_bits) - 1
        sub_y_mask = (1 << sub_y_bits) - 1

        key_shift = y_bits + x_bits + self.N_POLARITY_BITS
        n_key_bits = BITS_IN_KEY - key_shift
        key_mask = (1 << n_key_bits) - 1

        # Format of incoming keys is |X|P|Y|
        self.__fpga_y_shift = 0
        self.__fpga_x_shift = y_bits + 1
        self.__x_index_shift = self.__fpga_x_shift + (x_bits - sub_x_bits)
        self.__y_index_shift = self.__fpga_y_shift + (y_bits - sub_y_bits)
        self.__spif_mask = (
            (self.Y_MASK << self.__fpga_y_shift) +
            (self.X_MASK << self.__fpga_x_shift))
        self.__fpga_mask = (
            (key_mask << key_shift) +
            (sub_y_mask << self.__y_index_shift) +
            (sub_x_mask << self.__x_index_shift) +
            self.__spif_mask)
        self.__key_bits = base_key << key_shift

        # A dictionary to get vertex index from FPGA and slice
        self.__index_by_slice = dict()

        self.__base_key = base_key
        self.__x_bits = x_bits
        self.__y_bits = y_bits

        # Generate the |X|P|Y| shifts and masks for x and y
        self.__source_x_shift = y_bits + 1
        self.__source_x_mask = ((1 << x_bits) - 1) << (y_bits + 1)
        self.__source_y_shift = 0
        self.__source_y_mask = (1 << y_bits) - 1

    @property
    @overrides(ApplicationFPGAVertex.atoms_shape)
    def atoms_shape(self):
        return (self.__width, self.__height)

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

        :rtype: FGPA_Connection
        """
        return FPGAConnection(0, 15, None)

    def __fpga_indices(self, fpga_link_id):
        # We use every other odd link, so we can work out the "index" of the
        # link in the list as follows, and we can then split the index into
        # x and y components
        fpga_index = (fpga_link_id - 1) // 2
        fpga_x_index = fpga_index % self.X_PER_ROW
        fpga_y_index = fpga_index // self.X_PER_ROW
        return fpga_x_index, fpga_y_index

    def __sub_square(self, index):
        # Work out the x and y components of the index
        x_index = index % self.__n_squares_per_row
        y_index = index // self.__n_squares_per_row

        # Return the information
        return x_index, y_index

    @overrides(ApplicationFPGAVertex.get_incoming_slice_for_link)
    def get_incoming_slice_for_link(self, link, index):
        x_index, y_index = self.__sub_square(index)
        lo_atom_x = x_index * self.__sub_width
        lo_atom_y = y_index * self.__sub_height
        lo_atom = index * self.__n_atoms_per_subsquare
        hi_atom = (lo_atom + self.__n_atoms_per_subsquare) - 1
        vertex_slice = Slice(
            lo_atom, hi_atom, (self.__sub_width, self.__sub_height),
            (lo_atom_x, lo_atom_y))
        self.__index_by_slice[link.fpga_link_id, vertex_slice] = index
        return vertex_slice

    @overrides(ApplicationFPGAVertex.get_outgoing_slice)
    def get_outgoing_slice(self):
        return Slice(0, 100)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        machine_vertex = partition.pre_vertex
        fpga_link_id = machine_vertex.fpga_link_id
        vertex_slice = machine_vertex.vertex_slice
        index = self.__index_by_slice[fpga_link_id, vertex_slice]
        fpga_x, fpga_y = self.__fpga_indices(fpga_link_id)
        x_index, y_index = self.__sub_square(index)

        # Finally we build the key from the components
        fpga_key = (
            self.__key_bits +
            (y_index << self.__y_index_shift) +
            (fpga_y << self.__fpga_y_shift) +
            (x_index << self.__x_index_shift) +
            (fpga_x << self.__fpga_x_shift))
        return [FixedKeyAndMaskConstraint([
            BaseKeyAndMask(fpga_key, self.__fpga_mask)])]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        # Make sure everything has stopped
        commands = [_SpiNNFPGARegister.STOP.cmd()]

        # Clear the counters
        commands.append(_SPIFRegister.OUT_PERIPH_PKT_CNT.cmd(0))
        commands.append(_SPIFRegister.CONFIG_PKT_CNT.cmd(0))
        commands.append(_SPIFRegister.DROPPED_PKT_CNT.cmd(0))
        commands.append(_SPIFRegister.IN_PERIPH_PKT_CNT.cmd(0))
        commands.append(_SPIFRegister.DIAG_PKT_CNT.cmd(0))

        # Configure the creation of packets from fields to keys using the
        # "standard" input to SPIF, compressing the space down as much as
        # possible (the standard input uses the full 32-bits of space).
        # Note that the output will still be X | P | Y so this has to be
        # handled in the target
        commands.extend([
            set_field_mask(0, _POLARITY_MASK),
            set_field_shift(0, _POLARITY_SHIFT - self.__y_bits),
            set_field_mask(1, _X_MASK),
            set_field_shift(1, _X_SHIFT - (self.__y_bits + 1)),
            set_field_mask(2, _Y_MASK),
            set_field_shift(2, _Y_SHIFT),
            # These are unused but set them to be sure
            set_field_mask(3, 0),
            set_field_shift(3, 0)
        ])

        # Configure the output routing key
        commands.append(_SPIFRegister.MP_KEY.cmd(self.__base_key))

        # Configure the links to send packets to the 8 FPGAs using the
        # lower bits
        commands.extend(set_input_key(i, self.__spif_key(15 - (i * 2)))
                        for i in range(8))
        commands.extend(set_input_mask(i, self.__spif_mask)
                        for i in range(8))
        commands.extend(set_input_route(i, i) for i in range(8))

        # Set the other entries to 0
        commands.extend(set_input_key(i, 0) for i in range(8, 16))
        commands.extend(set_input_mask(i, 0) for i in range(8, 16))
        commands.extend(set_input_route(i, 0) for i in range(8, 16))

        # Send the start signal
        commands.append(_SpiNNFPGARegister.START.cmd())

        return commands

    def __spif_key(self, index):
        x, y = self.__fpga_indices(index)
        return (x << self.__fpga_x_shift) + (y << self.__fpga_y_shift)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        # Send the stop signal
        return [_SpiNNFPGARegister.STOP.cmd()]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []

    @overrides(HasShapeKeyFields.get_shape_key_fields)
    def get_shape_key_fields(self, machine_vertex):
        return ((0, self.__source_x_mask, self.__source_x_shift),
                (0, self.__source_y_mask, self.__source_y_shift))
