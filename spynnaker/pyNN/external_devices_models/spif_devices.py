# Copyright (c) 2022 The University of Manchester
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
"""
Devices connected to the SpiNNaker peripheral interface (`SPIF`_).

.. _SPIF: https://github.com/SpiNNakerManchester/spif

"""

from enum import IntEnum
from typing import Callable, Optional

from spinn_utilities.overrides import overrides

from spinn_front_end_common.utility_models import MultiCastCommand

_REPEATS = 2
_DELAY_BETWEEN_REPEATS = 1

#: Base key to send packets to SpiNNaker FPGA (add register offset)
_LC_KEY = 0xFFFFFE00

#: Base key to send packets to SPIF (add register offset)
_RC_KEY = 0xFFFFFF00

#: The number of pipes
N_PIPES = 2

#: The number of fields supported for each pipe
N_FIELDS = 4

#: The number of filters supported for each pipe
N_FILTERS = 8

#: SPIF is always connected to FPGA 0
SPIF_FPGA_ID = 0

#: SPIF always outputs to FPGA link 15 on FPGA 0
SPIF_OUTPUT_FPGA_LINK = 15

#: SPIF always gets input from odd links on FPGA 0 (1, 3, 5, 7, 9, 11, 13, 15)
SPIF_INPUT_FPGA_LINKS = range(1, 16, 2)

#: The number of FPGA inputs per pipe
#:
#: .. note::
#:     The inputs are not actually separated in the hardware,
#:     but a logical separation per pipe is useful.
N_INPUTS = len(SPIF_INPUT_FPGA_LINKS)


class SPIFRegister(IntEnum):
    """
    The register offsets on a SPIF device.
    """
    #: The key to send messages back when requested
    REPLY_KEY = 2

    #: The input key register base (8 inputs per pipe)
    IR_KEY_BASE = 16

    #: The input mask register base (8 inputs per pipe)
    IR_MASK_BASE = 32

    #: The input route register base (8 inputs per pipe)
    IR_ROUTE_BASE = 48

    #: The output peripheral packet count register
    OUT_PERIPH_PKT_CNT = 64

    #: The configuration packet count register
    CONFIG_PKT_CNT = 65

    #: The dropped packet count register
    DROPPED_PKT_CNT = 66

    #: The input peripheral packet count register
    IN_PERIPH_PKT_CNT = 67

    #: The output mapper key base register (2 pipes)
    MP_KEY_BASE = 80

    #: The output mapper field mask base register (4 fields per pipe)
    MP_FLD_MASK_BASE = 96

    #: The output mapper field shift base register (4 fields per pipe)
    MP_FLD_SHIFT_BASE = 112

    #: The output mapper field limit base register (4 fields per pipe)
    MP_FLD_LIMIT_BASE = 128

    #: The filter value base register (8 filters per pipe)
    FL_VALUE_BASE = 144

    #: The filter mask base register (8 filters per pipe)
    FL_MASK_BASE = 176

    # The distiller key base register (6 distillers)
    DIST_KEY_BASE = 208

    # The distiller key mask register (6 distillers)
    DIST_MASK_BASE = 224

    # The distiller key shift register (6 distillers)
    DIST_SHIFT_BASE = 240

    def cmd(self, payload: Optional[int] = None,
            index: int = 0) -> MultiCastCommand:
        """
        Make a command to send to a SPIF device to set a register value.

        :param payload:
            The payload to use in the command, or `None` for no payload
        :param index:
            The index of the register to send to when there are multiple
            registers starting from a base
        :returns: Command created but not yet run
        """
        return MultiCastCommand(
            _RC_KEY + self.value + index, payload, time=None, repeat=_REPEATS,
            delay_between_repeats=_DELAY_BETWEEN_REPEATS)

    def delayed_command(
            self, get_payload: Callable[[int], int],
            index: int = 0) -> "_DelayedMultiCastCommand":
        """ Make a command to send to a SPIF device to set a register value,
            where the value itself is currently unknown

        :param get_payload:
            A function to call to get the payload later
        :param index:
            The index of the register to use when using a multi-indexed
            register (default is 0 which works for all registers)
        :returns: Command created but not yet run
        """
        return _DelayedMultiCastCommand(
            _RC_KEY + self.value + index, get_payload, repeat=_REPEATS,
            delay_between_repeats=_DELAY_BETWEEN_REPEATS, index=index)


def set_mapper_key(pipe: int, key: int) -> MultiCastCommand:
    """
    Get a command to set the output base key for packets from SPIF.  This
    will be added to the keys determined by the mapper output.

    :param pipe: The SPIF pipe to set the key of (0-1)
    :param key: The output key to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.MP_KEY_BASE.cmd(key, pipe)


def set_field_mask(pipe: int, index: int, mask: int) -> MultiCastCommand:
    """
    Get a command to set the mask of a mapper field on SPIF.  This masks
    off the bits of the field from the incoming UDP or USB packet values
    (which are 32-bits each).

    :param pipe: The SPIF pipe to set the mask of (0-1)
    :param index: The index of the field to set (0-3)
    :param mask: The mask to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.MP_FLD_MASK_BASE.cmd(mask, (pipe * N_FIELDS) + index)


def set_field_shift(pipe: int, index: int, shift: int) -> MultiCastCommand:
    """
    Get a command to set the shift of a mapper field on SPIF.  This shifts
    the masked bits of the field from the incoming UDP or USB packet values
    (which are 32-bits each).

    :param pipe: The SPIF pipe to set the shift of (0-1)
    :param index: The index of the field to set (0-3)
    :param shift:
        The shift value to set (0-31); positive = right, negative = left
    :returns: Command created but not yet run
    """
    return SPIFRegister.MP_FLD_SHIFT_BASE.cmd(
        shift, (pipe * N_FIELDS) + index)


def set_field_limit(pipe: int, index: int, limit: int) -> MultiCastCommand:
    """
    Get a command to set the limit of a mapper field on SPIF.  This sets
    a limit on the value of the field after shifting and masking.

    :param pipe: The SPIF pipe to set the limit of (0-1)
    :param index: The index of the field to set (0-3)
    :param limit: The maximum value of the field
    :returns: Command created but not yet run
    """
    return SPIFRegister.MP_FLD_LIMIT_BASE.cmd(
        limit, (pipe * N_FIELDS) + index)


def set_filter_value(pipe: int, index: int, value: int) -> MultiCastCommand:
    """
    Get a command to set the value of a filter of SPIF.  This will drop
    input events from the UDP or USB packets where filter value ==
    filter mask & event value.

    :param pipe: The SPIF pipe to set the filter of (0-1)
    :param index: The index of the filter to set (0-7)
    :param value: The filter value to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.FL_VALUE_BASE.cmd(
        value, (pipe * N_FILTERS) + index)


def set_filter_mask(pipe: int, index: int, mask: int) -> MultiCastCommand:
    """
    Get a command to set the mask of a filter of SPIF.  This will drop
    input events from the UDP or USB packets where filter value ==
    filter mask & event value.

    :param pipe: The SPIF pipe to set the filter of (0-1)
    :param index: The index of the filter to set (0-7)
    :param mask: The filter mask to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.FL_MASK_BASE.cmd(
        mask, (pipe * N_FILTERS) + index)


def set_input_key(pipe: int, index: int, key: int) -> MultiCastCommand:
    """
    Get a command to set the key of the FPGA input of SPIF.  This tells
    SPIF how to route the incoming packets after they have been assembled
    by the mapper; when incoming key & input mask == input_key, the packet
    will be routed to input_route.

    :param pipe: The SPIF pipe to set the input of (0-1)
    :param index: The index of the input to set (0-7)
    :param key: The key to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.IR_KEY_BASE.cmd(key, (pipe * N_INPUTS) + index)


def set_input_mask(pipe: int, index: int, mask: int) -> MultiCastCommand:
    """
    Get a command to set the mask of the FPGA input of SPIF.  This tells
    SPIF how to route the incoming packets after they have been assembled
    by the mapper; when incoming key & input mask == input_key, the packet
    will be routed to input_route.

    :param pipe: The SPIF pipe to set the input of (0-1)
    :param index: The index of the input to set (0-7)
    :param mask: The mask to set
    :returns: Command created but not yet run

    """
    return SPIFRegister.IR_MASK_BASE.cmd(mask, (pipe * N_INPUTS) + index)


def set_input_route(pipe: int, index: int, route: int) -> MultiCastCommand:
    """
    Get a command to set the route of the FPGA input of SPIF.  This tells
    SPIF how to route the incoming packets after they have been assembled
    by the mapper; when incoming key & input mask == input_key, the packet
    will be routed to input_route.

    .. note::
        route 0 refers to FPGA link 15, 1 to 13 and so on in twos.

    :param pipe: The SPIF pipe to set the input of (0-1)
    :param index: The index of the input to set (0-7)
    :param route: The route to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.IR_ROUTE_BASE.cmd(route, (pipe * N_INPUTS) + index)


def set_distiller_key(index: int, key: int) -> MultiCastCommand:
    """ Get a command to set the key of the distiller of the output via SPIF.
        This tells SPIF which bits to put at the top of the 32-bit output for
        each spike received on the given distiller channel, defined by the
        peripheral routes in the SpiNNaker FPGA.

    :param index: The index of the channel to set (0-5)
    :param key: The key to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.DIST_KEY_BASE.cmd(key, index)


def set_distiller_mask(index: int, mask: int) -> MultiCastCommand:
    """ Get a command to set the mask of the distiller of the output via SPIF.
        This tells SPIF which bits to use from the key in the 32-bit output for
        each spike received on the given distiller channel, defined by the
        peripheral routes in the SpiNNaker FPGA.

    :param index: The index of the channel to set (0-5)
    :param mask: The mask to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.DIST_MASK_BASE.cmd(mask, index)


def set_distiller_mask_delayed(
        index: int, mask_func: Callable[[int], int]) -> MultiCastCommand:
    """ Get a command to set the mask of the distiller of the output via SPIF.
        This tells SPIF which bits to use from the key in the 32-bit output for
        each spike received on the given distiller channel, defined by the
        peripheral routes in the SpiNNaker FPGA.

    :param index: The index of the channel to set (0-5)
    :param mask_func:
        The function to call to set the mask - takes index as argument
    :returns: Command created but not yet run
    """
    return SPIFRegister.DIST_MASK_BASE.delayed_command(mask_func, index)


def set_distiller_shift(index: int, shift: int) -> MultiCastCommand:
    """ Get a command to set the shift of the distiller of the output via SPIF.
        This tells SPIF how much to shift the key after masking but before
        applying the distiller key.

    :param index: The index of the channel to set (0-5)
    :param shift: The shift to set
    :returns: Command created but not yet run
    """
    return SPIFRegister.DIST_SHIFT_BASE.cmd(shift, index)


class _DelayedMultiCastCommand(MultiCastCommand):
    """
    A command where the getting of the payload is delayed.
    """
    __slots__ = ("__get_payload", "__index")

    def __init__(self, key: int, get_payload: Callable[[int], int],
                 repeat: int, delay_between_repeats: int, index: int):
        """
        :param key: The key to send
        :param get_payload:
            A function to call that returns a payload.
            May be called multiple times; should produce the same value each
            time.
        :param repeat: The number of times to repeat the command
        :param delay_between_repeats: The delay between the repeats
        :param index: The index to pass to get_payload when called
        """
        super().__init__(
            key, repeat=repeat, delay_between_repeats=delay_between_repeats)
        self.__get_payload = get_payload
        self.__index = index

    @property
    @overrides(MultiCastCommand.payload)
    def payload(self) -> int:
        return self.__get_payload(self.__index)

    @property
    @overrides(MultiCastCommand.is_payload)
    def is_payload(self) -> bool:
        return True


class SpiNNFPGARegister(IntEnum):
    """
    The register offsets on the SpiNNaker FPGAs for devices.
    """

    #: The base key which identifies packets to send out to the peripheral
    # (deprecated - use XP_KEY_0)
    P_KEY = 2

    #: The mask which identifies packets to send out to the peripheral
    # (deprecated - use XP_MASK_0)
    P_MASK = 3

    #: The base key which identifies packets to write to the FPGA registers
    LC_KEY = 12

    #: The mask which identifies packets to write to the FPGA registers
    LC_MASK = 13

    #: The base key which identifies packets to write to the peripheral
    #: registers
    RC_KEY = 14

    #: The mask which identifies packets to write to the peripheral registers
    RC_MASK = 15

    #: The register to write to to stop the sending of data from the peripheral
    #: to SpiNNaker
    STOP = 16

    #: The register to write to to start the sending of data from the
    #: peripheral to SpiNNaker
    START = 17

    #: The base of the keys that can be sent out of SpiNNaker (up to 6)
    XP_KEY_BASE = 32

    #: The base of the masks that can be sent out of SpiNNake (up to 6)
    XP_MASK_BASE = 48

    def cmd(self, payload: Optional[int] = None,
            index: int = 0) -> MultiCastCommand:
        """
        Make a command to send to the FPGA to set a register value.

        :param payload:
            The payload to use in the command, or `None` for no payload
        :param index:
            The index of the register to send to when there are multiple
            registers starting from a base
        :returns: Command created but not yet run
        """
        return MultiCastCommand(
            _LC_KEY + self.value + index, payload, time=None, repeat=_REPEATS,
            delay_between_repeats=_DELAY_BETWEEN_REPEATS)

    def delayed_command(
            self, get_payload: Callable[[int], int],
            index: int = 0) -> _DelayedMultiCastCommand:
        """
        Make a command to send to the FPGA to set a register value,
        where the value itself is currently unknown.

        :param get_payload:
            A function to call to get the payload later, passing in the index
        :param index:
            The index of the register to send to when there are multiple
            registers starting from a base
        :returns: Command created but not yet run
        """
        return _DelayedMultiCastCommand(
            _LC_KEY + self.value + index, get_payload, repeat=_REPEATS,
            delay_between_repeats=_DELAY_BETWEEN_REPEATS, index=index)


def set_xp_key(index: int, key: int) -> MultiCastCommand:
    """ Get a command to set the key of the output via the FPGA.
        This tells the FPGA to route this key to the external device.

    :param index: The index of the channel to set (0-5)
    :param key: The key to set
    :returns: Command created but not yet run
    """
    return SpiNNFPGARegister.XP_KEY_BASE.cmd(key, index)


def set_xp_key_delayed(
        index: int,
        key_func: Callable[[int], int]) -> _DelayedMultiCastCommand:
    """ Get a command to set the key of the output via the FPGA later.
        This tells the FPGA to route this key to the external device.

    :param index: The index of the channel to set (0-5)
    :param key_func: The function to call to get the key
    :returns: Command created but not yet run
    """
    return SpiNNFPGARegister.XP_KEY_BASE.delayed_command(key_func, index)


def set_xp_mask(index: int, mask: int) -> MultiCastCommand:
    """ Get a command to set the mask the output via the FPGA.
        This tells the FPGA to route keys after using this mask to the external
        device.

    :param index: The index of the channel to set (0-5)
    :param mask: The mask to set
    :returns: Command created but not yet run
    """
    return SpiNNFPGARegister.XP_MASK_BASE.cmd(mask, index)


def set_xp_mask_delayed(
        index: int,
        mask_func: Callable[[int], int]) -> _DelayedMultiCastCommand:
    """ Get a command to set the mask of the output via the FPGA later.
        This tells the FPGA to route keys after using this mask to the external
        device.

    :param index: The index of the channel to set (0-5)
    :param mask_func: The function to call to get the mask
    :returns: Command created but not yet run
    """
    return SpiNNFPGARegister.XP_MASK_BASE.delayed_command(mask_func, index)
