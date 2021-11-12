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
from pacman.model.graphs.application import Application2DFPGAVertex
from pacman.model.graphs.application import FPGAConnection
from pacman.model.routing_info import BaseKeyAndMask
from pacman.utilities.constants import BITS_IN_KEY
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints,
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utility_models import MultiCastCommand
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.abstract_models import HasShapeKeyFields
from enum import IntEnum

_REPEATS = 2
_DELAY_BETWEEN_REPEATS = 1

#: Base key to send packets to SpiNNaker FPGA (add register offset)
_LC_KEY = 0xFFFFFE00

#: Base key to send packets to SPIF (add register offset)
_RC_KEY = 0xFFFFFF00

#: The number of pipes
_N_PIPES = 2

#: The number of fields supported for each pipe
_N_FIELDS = 2

#: The number of filters supported for each pipe
_N_FILTERS = 8


class _SPIFRegister(IntEnum):
    REPLY_KEY = 2
    IR_KEY_BASE = 16
    IR_MASK_BASE = 32
    IR_ROUTE_BASE = 48
    OUT_PERIPH_PKT_CNT = 64
    CONFIG_PKT_CNT = 65
    DROPPED_PKT_CNT = 66
    IN_PERIPH_PKT_CNT = 67
    MP_KEY_BASE = 80
    MP_FLD_MASK_BASE = 96
    MP_FLD_SHIFT_BASE = 112
    MP_FLD_LIMIT_BASE = 128
    FL_VALUE_BASE = 144
    FL_MASK_BASE = 176

    def cmd(self, payload=None, index=0):
        return MultiCastCommand(
            _RC_KEY + self.value + index, payload, time=None, repeat=_REPEATS,
            delay_between_repeats=_DELAY_BETWEEN_REPEATS)


def set_mapper_key(pipe, key):
    return _SPIFRegister.MP_KEY_BASE.cmd(key, pipe)


def set_field_mask(pipe, index, mask):
    return _SPIFRegister.MP_FLD_MASK_BASE.cmd(mask, (pipe * _N_FIELDS) + index)


def set_field_shift(pipe, index, shift):
    return _SPIFRegister.MP_FLD_SHIFT_BASE.cmd(
        shift, (pipe * _N_FIELDS) + index)


def set_field_limit(pipe, index, limit):
    return _SPIFRegister.MP_FLD_LIMIT_BASE.cmd(
        limit, (pipe * _N_FIELDS) + index)


def set_filter_value(pipe, index, value):
    return _SPIFRegister.FL_VALUE_BASE.cmd(
        value, (pipe * _N_FILTERS) + index)


def set_filter_mask(pipe, index, mask):
    return _SPIFRegister.FL_MASK_BASE.cmd(
        mask, (pipe * _N_FILTERS) + index)


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
        Application2DFPGAVertex, AbstractProvidesOutgoingPartitionConstraints,
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

    #: The number of devices in existence, to work out the key
    __n_devices = 0

    __slots__ = [
        "__spif_mask",
        "__index_by_slice",
        "__base_key",
        "__pipe",
        "__input_y_mask",
        "__input_y_shift",
        "__input_x_mask",
        "__input_x_shift"]

    def __init__(self, pipe, width, height, sub_width, sub_height,
                 base_key=None, input_x_shift=16, input_y_shift=0,
                 board_address=None, chip_coords=None):
        """

        :param int pipe: Which pipe on SPIF the retina is connected to
        :param int width: The width of the retina in pixels
        :param int height: The height of the retina in pixels
        :param int sub_width:
            The width of rectangles to split the retina into for efficiency of
            sending
        :param int sub_height:
            The height of rectangles to split the retina into for efficiency of
            sending
        :param base_key:
            The key that is common over the whole vertex,
            or None to use the pipe number as the key
        :type base_key: int or None
        :param int input_x_shift:
            The shift to get the x coordinate from the input keys sent to SPIF
        :param int input_y_shift:
            The shift to get the y coordinate from the input keys sent to SPIF
        :param board_address:
            The IP address of the board to which the FPGA is connected, or None
            to use the default board or chip_coords.  Note chip_coords will be
            used first if both are specified, with board_address then being
            used if the coordinates don't connect to an FPGA.
        :type board_address: str or None
        :param chip_coords:
            The coordinates of the chip to which the FPGA is connected, or
            None to use the default board or board_address.   Note chip_coords
            will be used first if board_address is also specified, with
            board_address then being used if the coordinates don't connect to
            an FPGA.
        :type chip_coords: tuple(int, int) or None
        """
        # Do some checks
        if sub_width < self.X_MASK or sub_height < self.Y_MASK:
            raise ConfigurationException(
                "The sub-squares must be >=4 x >= 2"
                f" ({sub_width} x {sub_height} specified)")
        if pipe >= _N_PIPES:
            raise ConfigurationException(
                f"Pipe {pipe} is bigger than maximum allowed {_N_PIPES}")

        # Call the super
        super().__init__(
            width, height, sub_width, sub_height,
            self.__incoming_fpgas(board_address, chip_coords),
            self.__outgoing_fpga(board_address, chip_coords))

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
        x_bits = self._x_bits
        y_bits = self._y_bits

        # Mask to apply to route packets at input
        n_key_bits = BITS_IN_KEY - self._key_shift
        key_mask = (1 << n_key_bits) - 1
        self.__spif_mask = (
            (key_mask << self._key_shift) +
            (self.Y_MASK << self._source_y_shift) +
            (self.X_MASK << self._source_x_shift))

        # A dictionary to get vertex index from FPGA and slice
        self.__index_by_slice = dict()

        self.__pipe = pipe
        self.__base_key = base_key
        if self.__base_key is None:
            self.__base_key = self.__n_devices
        self.__n_devices += 1

        # Generate the shifts and masks to convert the SPIF Ethernet inputs to
        # PYX format
        self.__input_x_mask = ((1 << x_bits) - 1) << input_x_shift
        self.__input_x_shift = self.__unsigned(
            input_x_shift)
        self.__input_y_mask = ((1 << y_bits) - 1) << input_y_shift
        self.__input_y_shift = self.__unsigned(
            input_y_shift - x_bits)

    def __unsigned(self, n):
        return n & 0xFFFFFFFF

    def __incoming_fpgas(self, board_address, chip_coords):
        """ Get the incoming FPGA connections

        :rtype: list(FPGAConnection)
        """
        # We use every other odd link
        return [FPGAConnection(0, i, board_address, chip_coords)
                for i in range(1, 16, 2)]

    def __outgoing_fpga(self, board_address, chip_coords):
        """ Get the outgoing FPGA connection

        :rtype: FGPA_Connection
        """
        return FPGAConnection(0, 15, board_address, chip_coords)

    def __fpga_indices(self, fpga_link_id):
        # We use every other odd link, so we can work out the "index" of the
        # link in the list as follows, and we can then split the index into
        # x and y components
        fpga_index = (fpga_link_id - 1) // 2
        fpga_x_index = fpga_index % self.X_PER_ROW
        fpga_y_index = fpga_index // self.X_PER_ROW
        return fpga_x_index, fpga_y_index

    @overrides(Application2DFPGAVertex.get_incoming_slice_for_link)
    def get_incoming_slice_for_link(self, link, index):
        vertex_slice = super(
            SPIFRetinaDevice, self).get_incoming_slice_for_link(link, index)
        self.__index_by_slice[link.fpga_link_id, vertex_slice] = index
        return vertex_slice

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        machine_vertex = partition.pre_vertex
        fpga_link_id = machine_vertex.fpga_link_id
        vertex_slice = machine_vertex.vertex_slice
        index = self.__index_by_slice[fpga_link_id, vertex_slice]
        key_and_mask = self._get_key_and_mask(self.__base_key, index)

        fpga_x, fpga_y = self.__fpga_indices(fpga_link_id)

        # Finally we build the key from the components
        fpga_key = key_and_mask.key + (
            (fpga_y << self._source_y_shift) +
            (fpga_x << self._source_x_shift))
        fpga_mask = key_and_mask.mask | self.__spif_mask
        return [FixedKeyAndMaskConstraint(
            [BaseKeyAndMask(fpga_key, fpga_mask)])]

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

        # Configure the creation of packets from fields to keys using the
        # "standard" input to SPIF (X | P | Y) and convert to (Y | X)
        commands.extend([
            set_field_mask(self.__pipe, 0, self.__input_x_mask),
            set_field_shift(self.__pipe, 0, self.__input_x_shift),
            set_field_limit(self.__pipe, 0,
                            self._width << self._source_x_shift),
            set_field_mask(self.__pipe, 1, self.__input_y_mask),
            set_field_shift(self.__pipe, 1, self.__input_y_shift),
            set_field_limit(self.__pipe, 1,
                            self._height << self._source_y_shift),
            # These are unused but set them to be sure
            set_field_mask(self.__pipe, 2, 0),
            set_field_shift(self.__pipe, 2, 0),
            set_field_limit(self.__pipe, 2, 0),
            set_field_mask(self.__pipe, 3, 0),
            set_field_shift(self.__pipe, 3, 0),
            set_field_limit(self.__pipe, 3, 0)
        ])

        # Don't filter
        commands.extend([
            set_filter_mask(self.__pipe, i, 0) for i in range(_N_FILTERS)
        ])
        commands.extend([
            set_filter_value(self.__pipe, i, 1) for i in range(_N_FILTERS)
        ])

        # Configure the output routing key
        commands.append(set_mapper_key(
            self.__pipe, self.__base_key << self._key_shift))

        # Configure the links to send packets to the 8 FPGAs using the
        # lower bits
        commands.extend(set_input_key(i, self.__spif_key(15 - (i * 2)))
                        for i in range(self.__pipe, self.__pipe + 8))
        commands.extend(set_input_mask(i, self.__spif_mask)
                        for i in range(self.__pipe, self.__pipe + 8))
        commands.extend(set_input_route(i + (self.__pipe * 8), i)
                        for i in range(8))

        # Send the start signal
        commands.append(_SpiNNFPGARegister.START.cmd())

        return commands

    def __spif_key(self, index):
        x, y = self.__fpga_indices(index)
        return ((self.__base_key << self._key_shift) +
                (x << self._source_x_shift) +
                (y << self._source_y_shift))

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
    def get_shape_key_fields(self, vertex_slice):
        return self._key_fields
