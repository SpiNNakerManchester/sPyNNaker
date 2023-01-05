# Copyright (c) 2021-2022 The University of Manchester
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
import math
from spinn_utilities.overrides import overrides
from spinn_machine import MulticastRoutingEntry
from pacman.model.graphs.application import (
    Application2DFPGAVertex, FPGAConnection)
from pacman.model.routing_info import BaseKeyAndMask, AppVertexRoutingInfo
from pacman.model.routing_info.mergable_app_vertex_routing_info import (
    n_sequential_entries, all_entries_defaultable)
from pacman.utilities.constants import BITS_IN_KEY
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.models.abstract_models import HasShapeKeyFields
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from .spif_devices import (
    SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK, SPIF_INPUT_FPGA_LINKS,
    N_PIPES, N_FILTERS, SpiNNFPGARegister, SPIFRegister,
    set_field_mask, set_field_shift, set_field_limit,
    set_filter_mask, set_filter_value, set_mapper_key,
    set_input_key, set_input_mask, set_input_route)


class SPIFRetinaDevice(
        Application2DFPGAVertex, PopulationApplicationVertex,
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
        if pipe >= N_PIPES:
            raise ConfigurationException(
                f"Pipe {pipe} is bigger than maximum allowed {N_PIPES}")

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
            self.__base_key = SPIFRetinaDevice.__n_devices
        SPIFRetinaDevice.__n_devices += 1

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
        return [FPGAConnection(SPIF_FPGA_ID, i, board_address, chip_coords)
                for i in SPIF_INPUT_FPGA_LINKS]

    def __outgoing_fpga(self, board_address, chip_coords):
        """ Get the outgoing FPGA connection (for commands)

        :rtype: FGPA_Connection
        """
        return FPGAConnection(
            SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK, board_address, chip_coords)

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

    @overrides(Application2DFPGAVertex.get_machine_fixed_key_and_mask)
    def get_machine_fixed_key_and_mask(self, machine_vertex, partition_id):
        fpga_link_id = machine_vertex.fpga_link_id
        vertex_slice = machine_vertex.vertex_slice
        index = self.__index_by_slice[fpga_link_id, vertex_slice]
        key_and_mask = self._get_key_and_mask(self.__base_key, index)

        fpga_x, fpga_y = self.__fpga_indices(fpga_link_id)

        # Build the key from the components
        fpga_key = key_and_mask.key + (
            (fpga_y << self._source_y_shift) +
            (fpga_x << self._source_x_shift))
        fpga_mask = key_and_mask.mask | self.__spif_mask
        return BaseKeyAndMask(fpga_key, fpga_mask)

    @overrides(Application2DFPGAVertex.get_fixed_key_and_mask)
    def get_fixed_key_and_mask(self, partition_id):
        n_key_bits = BITS_IN_KEY - self._key_shift
        key_mask = ((1 << n_key_bits) - 1) << self._key_shift
        return BaseKeyAndMask(self.__base_key << self._key_shift, key_mask)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        # Make sure everything has stopped
        commands = [SpiNNFPGARegister.STOP.cmd()]

        # Clear the counters
        commands.append(SPIFRegister.OUT_PERIPH_PKT_CNT.cmd(0))
        commands.append(SPIFRegister.CONFIG_PKT_CNT.cmd(0))
        commands.append(SPIFRegister.DROPPED_PKT_CNT.cmd(0))
        commands.append(SPIFRegister.IN_PERIPH_PKT_CNT.cmd(0))

        # Configure the creation of packets from fields to keys using the
        # "standard" input to SPIF (X | P | Y) and convert to (Y | X)
        commands.extend([
            set_field_mask(self.__pipe, 0, self.__input_x_mask),
            set_field_shift(self.__pipe, 0, self.__input_x_shift),
            set_field_limit(self.__pipe, 0,
                            (self._width - 1) << self._source_x_shift),
            set_field_mask(self.__pipe, 1, self.__input_y_mask),
            set_field_shift(self.__pipe, 1, self.__input_y_shift),
            set_field_limit(self.__pipe, 1,
                            (self._height - 1) << self._source_y_shift),
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
            set_filter_mask(self.__pipe, i, 0) for i in range(N_FILTERS)
        ])
        commands.extend([
            set_filter_value(self.__pipe, i, 1) for i in range(N_FILTERS)
        ])

        # Configure the output routing key
        commands.append(set_mapper_key(
            self.__pipe, self.__base_key << self._key_shift))

        # Configure the links to send packets to the 8 FPGAs using the
        # lower bits
        commands.extend(
            set_input_key(self.__pipe, i, self.__spif_key(15 - (i * 2)))
            for i in range(8))
        commands.extend(
            set_input_mask(self.__pipe, i, self.__spif_mask)
            for i in range(8))
        commands.extend(
            set_input_route(self.__pipe, i, i)
            for i in range(8))

        # Send the start signal
        commands.append(SpiNNFPGARegister.START.cmd())

        return commands

    def __spif_key(self, fpga_link_id):
        x, y = self.__fpga_indices(fpga_link_id)
        return ((self.__base_key << self._key_shift) +
                (x << self._source_x_shift) +
                (y << self._source_y_shift))

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        # Send the stop signal
        return [SpiNNFPGARegister.STOP.cmd()]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []

    @overrides(HasShapeKeyFields.get_shape_key_fields)
    def get_shape_key_fields(self, vertex_slice):
        return self._key_fields

    def get_routing_info(
            self, key_and_mask, partition_id, machine_mask, n_bits_atoms):
        return _SPIFMergableRoutingInfo(
            key_and_mask, partition_id, self, machine_mask, n_bits_atoms,
            self.X_MASK << self._source_x_shift, self._source_x_shift,
            self.Y_MASK << self._source_y_shift, self._source_y_shift,
            self.X_PER_ROW)


class _SPIFMergableRoutingInfo(AppVertexRoutingInfo):
    """ Simple merging of retina entries using the source FPGA x and y masks
        for machine vertices with the same vertex slice.
    """

    __slots__ = [
        # The mask to get the FPGA x bits
        "__x_mask",
        # The shift to get the FPGA x bits
        "__x_shift",
        # The mask to get the FGPA y bits
        "__y_mask",
        # The shift to get the FGPA y bits
        "__y_shift",
        # The number of FPGA x values per row
        "__x_per_row",
        # The number of bits for the number of x values per row
        "__x_per_row_bits"
        ]

    def __init__(
            self, keys_and_masks, partition_id, app_vertex, machine_mask,
            n_bits_atoms, x_mask, x_shift, y_mask, y_shift, x_per_row):
        super(_SPIFMergableRoutingInfo, self).__init__(
            keys_and_masks, partition_id, app_vertex, machine_mask,
            n_bits_atoms)
        self.__x_mask = x_mask
        self.__y_mask = y_mask
        self.__x_shift = x_shift
        self.__y_shift = y_shift
        self.__x_per_row = x_per_row
        self.__x_per_row_bits = get_n_bits(x_per_row)

    @overrides(AppVertexRoutingInfo.get_entries)
    def get_entries(self, part_id, entries, routing_info):
        if len(entries) == 1:
            yield from super(_SPIFMergableRoutingInfo, self).get_entries(
                part_id, entries, routing_info)
            return

        # Try to merge all things from the same area
        i = 0
        while i < len(entries):
            m_vertex, entry_to_match = entries[i]
            r_info_to_match = routing_info.get_routing_info_from_pre_vertex(
                m_vertex, part_id)
            matching_entries = list([(entry_to_match, r_info_to_match)])
            while i + 1 < len(entries):
                next_m_vertex, next_entry = entries[i + 1]
                if not _matches(m_vertex, entry_to_match, next_m_vertex,
                                next_entry):
                    break
                next_r_info = routing_info.get_routing_info_from_pre_vertex(
                    next_m_vertex, part_id)
                matching_entries.append((next_entry, next_r_info))
                i += 1
            yield from self.__merge_entries(matching_entries)
            i += 1

    def __merge_entries(self, entries):
        i = 0
        n_entries = len(entries)
        while i < n_entries:
            entry, r_info = entries[i]
            index = self.__get_index(r_info)
            next_n_entries = n_sequential_entries(index, n_entries)
            if next_n_entries <= (n_entries - i):
                mask = self.__group_mask(r_info, next_n_entries)
                defaultable = all_entries_defaultable(
                    entries, i, next_n_entries)
                yield MulticastRoutingEntry(
                    r_info.key, mask, defaultable=defaultable,
                    spinnaker_route=entry.spinnaker_route)
                i += next_n_entries

            # Otherwise, we have to break down into powers of two
            else:
                entries_to_go = n_entries - i
                while entries_to_go > 0:
                    next_entries = 2 ** int(math.log2(entries_to_go))
                    entry, r_info = entries[i]
                    mask = self.__group_mask(r_info, next_entries)
                    defaultable = all_entries_defaultable(
                        entries, i, next_entries)
                    yield MulticastRoutingEntry(
                        r_info.key, mask, defaultable=defaultable,
                        spinnaker_route=entry.spinnaker_route)
                    entries_to_go -= next_entries
                    i += next_entries

    def __get_index(self, r_info):
        key = r_info.key
        x = (key & self.__x_mask) >> self.__x_shift
        y = (key & self.__y_mask) >> self.__y_shift
        return (y << self.__x_per_row_bits) | x

    def __group_mask(self, r_info, n_entries):
        if n_entries == 1:
            return r_info.mask

        # Split n_entries into x and y parts.  We can use divmod, but if
        # there are 0 x entries, we can mask all the x-parts instead, so we
        # move one of the y entries to x_per_row x entries.
        n_y, n_x = divmod(n_entries - 1, self.__x_per_row)
        if n_x == 0:
            n_y -= 1
            n_x += self.__x_per_row

        # Work out how the bits to zero in the mask
        y_bits = ((2 ** get_n_bits(n_y)) - 1) << self.__y_shift
        x_bits = ((2 ** get_n_bits(n_x)) - 1) << self.__x_shift

        # Zero the bits
        mask = r_info.mask
        mask &= ~y_bits
        mask &= ~x_bits
        return mask


def _matches(m_vertex, entry, next_m_vertex, next_entry):
    return (next_m_vertex.vertex_slice == m_vertex.vertex_slice and
            entry.spinnaker_route == next_entry.spinnaker_route)
