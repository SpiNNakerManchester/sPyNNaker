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
import math
from typing import Iterable, List, Tuple
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import (
    ApplicationFPGAVertex, FPGAConnection)
from pacman.model.graphs.common.slice import Slice
from pacman.model.graphs.machine import MachineFPGAVertex, MachineVertex
from pacman.model.routing_info import BaseKeyAndMask, RoutingInfo
from pacman.utilities.constants import BITS_IN_KEY
from pacman.utilities.utility_calls import get_n_bits
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utility_models import MultiCastCommand
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from .spif_devices import (
    SPIF_FPGA_ID, SPIF_OUTPUT_FPGA_LINK, SPIF_INPUT_FPGA_LINKS,
    N_PIPES, N_FIELDS, N_FILTERS, SpiNNFPGARegister, SPIFRegister,
    set_field_mask, set_field_shift, set_field_limit,
    set_filter_mask, set_filter_value, set_mapper_key,
    set_input_key, set_input_mask, set_input_route)


class SPIFInputDevice(
        ApplicationFPGAVertex, PopulationApplicationVertex,
        AbstractSendMeMulticastCommandsVertex):
    """ A 1D input device connected to SpiNNaker using a SPIF board.
    """

    #: SPIF outputs to 8 FPGA output links, so we split all input into 8
    INPUT_MASK = 7

    #: The number of devices in existence, to work out the key
    __n_devices = 0

    __slots__ = [
        "__spif_mask",
        "__index_by_slice",
        "__base_key",
        "__pipe",
        "__key_mask",
        "__m_vertex_mask",
        "__neuron_bits",
        "__index_bits",
        "__index_shift",
        "__input_mask",
        "__input_shift"]

    def __init__(self, pipe, n_neurons, n_neurons_per_partition,
                 base_key=None, board_address=None, chip_coords=None):
        """

        :param int pipe: Which pipe on SPIF the retina is connected to
        :param int n_neurons: The number of neurons in the device
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
        if n_neurons_per_partition < self.INPUT_MASK:
            raise ConfigurationException(
                "The number of neurons per partition must not be <"
                f" {self.INPUT_MASK} ({n_neurons_per_partition} specified)")
        if not self.__is_power_of_2(n_neurons_per_partition):
            raise ConfigurationException(
                f"n_neurons_per_partition ({n_neurons_per_partition}) "
                "must be a power of 2")
        if pipe >= N_PIPES:
            raise ConfigurationException(
                f"Pipe {pipe} is bigger than maximum allowed {N_PIPES}")

        n_machine_vertices = int(
            math.ceil(n_neurons / n_neurons_per_partition))

        # Call the super
        super().__init__(
            n_atoms=n_neurons,
            n_machine_vertices_per_link=n_machine_vertices,
            incoming_fpga_connections=self.__incoming_fpgas(
                board_address, chip_coords),
            outgoing_fpga_connection=self.__outgoing_fpga(
                board_address, chip_coords))

        # The mask is going to be made up of:
        # | K | N_I | N_0 | N_F |
        # K = base key
        # N_I = index of sub-partition
        # N_0 = 0s for neuron IDs not cared about
        # N_F = FPGA index
        # Now - go calculate:
        self.__neuron_bits = get_n_bits(n_neurons)
        self.__index_bits = get_n_bits(n_machine_vertices)
        self.__index_shift = get_n_bits(n_neurons_per_partition)

        # Mask to apply to route packets at input
        n_key_bits = BITS_IN_KEY - self.__neuron_bits
        self.__key_mask = ((1 << n_key_bits) - 1) << self.__neuron_bits
        self.__spif_mask = self.__key_mask + self.INPUT_MASK
        sub_mask = (1 << self.__index_bits) - 1
        self.__m_vertex_mask = (
            self.__key_mask + (sub_mask << self.__index_shift))

        # A dictionary to get vertex index from FPGA and slice
        self.__index_by_slice = dict()

        self.__pipe = pipe
        self.__base_key = base_key
        if self.__base_key is None:
            self.__base_key = SPIFInputDevice.__n_devices
        self.__base_key = self.__base_key << self.__neuron_bits
        SPIFInputDevice.__n_devices += 1

        # Generate the shifts and masks to convert the SPIF Ethernet inputs to
        # output format
        self.__input_mask = (1 << self.__neuron_bits) - 1
        self.__input_shift = 0

    def __is_power_of_2(self, v):
        """ Determine if a value is a power of 2

        :param int v: The value to test
        :rtype: bool
        """
        return (v & (v - 1) == 0) and (v != 0)

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

    def __fpga_index(self, fpga_link_id):
        # We use every other odd link, so we can work out the "index" of the
        # link in the list as follows
        return (fpga_link_id - 1) // 2

    @overrides(ApplicationFPGAVertex.get_incoming_slice_for_link)
    def get_incoming_slice_for_link(
            self, link: FPGAConnection, index: int) -> Slice:
        # pylint: disable=missing-function-docstring
        vertex_slice = super().get_incoming_slice_for_link(link, index)
        self.__index_by_slice[link.fpga_link_id, vertex_slice] = index
        return vertex_slice

    @overrides(ApplicationFPGAVertex.get_machine_fixed_key_and_mask)
    def get_machine_fixed_key_and_mask(self, machine_vertex: MachineVertex,
                                       partition_id: str) -> BaseKeyAndMask:
        # pylint: disable=missing-function-docstring
        assert isinstance(machine_vertex, MachineFPGAVertex)
        fpga_link_id = machine_vertex.fpga_link_id
        vertex_slice = machine_vertex.vertex_slice
        index = self.__index_by_slice[fpga_link_id, vertex_slice]
        key = self.__base_key | (index << self.__index_shift)

        fpga = self.__fpga_index(fpga_link_id)

        # Build the key from the components
        fpga_key = key + fpga
        fpga_mask = self.__m_vertex_mask | self.__spif_mask
        return BaseKeyAndMask(fpga_key, fpga_mask)

    @overrides(ApplicationFPGAVertex.get_fixed_key_and_mask)
    def get_fixed_key_and_mask(self, partition_id: str) -> BaseKeyAndMask:
        # pylint: disable=missing-function-docstring
        return BaseKeyAndMask(self.__base_key, self.__key_mask)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self) -> Iterable[MultiCastCommand]:
        # pylint: disable=missing-function-docstring
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
            set_field_mask(self.__pipe, 0, self.__input_mask),
            set_field_shift(self.__pipe, 0, self.__input_shift),
            set_field_limit(self.__pipe, 0, self.n_atoms)])

        # These are unused but set them to be sure
        for i in range(1, N_FIELDS):
            commands.extend([
                set_field_mask(self.__pipe, i, 0),
                set_field_shift(self.__pipe, i, 0),
                set_field_limit(self.__pipe, i, 0)])

        # Don't filter
        commands.extend([
            set_filter_mask(self.__pipe, i, 0) for i in range(N_FILTERS)
        ])
        commands.extend([
            set_filter_value(self.__pipe, i, 1) for i in range(N_FILTERS)
        ])

        # Configure the output routing key
        commands.append(set_mapper_key(self.__pipe, self.__base_key))

        # Configure the links to send packets to the 8 FPGAs using the
        # lower bits; the input key is against the reversed links list because
        # the input numbering on SPIF is upside-down to the FPGA numbering, and
        # we put out the fixed key and mask in the FPGA link order, so we need
        # to match that with what SPIF will output.
        commands.extend(
            set_input_key(self.__pipe, i, self.__spif_key(f))
            for i, f in enumerate(reversed(SPIF_INPUT_FPGA_LINKS)))
        commands.extend(
            set_input_mask(self.__pipe, i, self.__spif_mask)
            for i in range(len(SPIF_INPUT_FPGA_LINKS)))
        commands.extend(
            set_input_route(self.__pipe, i, i)
            for i in range(len(SPIF_INPUT_FPGA_LINKS)))

        # Send the start signal
        commands.append(SpiNNFPGARegister.START.cmd())

        return commands

    def __spif_key(self, fpga_link_id):
        fpga = self.__fpga_index(fpga_link_id)
        return self.__base_key + fpga

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self) -> Iterable[MultiCastCommand]:
        # pylint: disable=missing-function-docstring
        # Send the stop signal
        return [SpiNNFPGARegister.STOP.cmd()]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self) -> List[MultiCastCommand]:
        # pylint: disable=missing-function-docstring
        return []

    @overrides(PopulationApplicationVertex.get_atom_key_map)
    def get_atom_key_map(
            self, pre_vertex: MachineVertex, partition_id: str,
            routing_info: RoutingInfo) -> Iterable[Tuple[int, int]]:
        # Work out which machine vertex
        start = pre_vertex.vertex_slice.lo_atom
        key_and_mask = self.get_machine_fixed_key_and_mask(
            pre_vertex, partition_id)
        end = pre_vertex.vertex_slice.hi_atom + 1
        n_key = key_and_mask.key & self.INPUT_MASK
        start += n_key
        neuron_id = pre_vertex.vertex_slice.lo_atom + n_key
        for n in range(start, end, self.INPUT_MASK + 1):
            key = key_and_mask.key | n
            yield (neuron_id, key)
            neuron_id += self.INPUT_MASK + 1
