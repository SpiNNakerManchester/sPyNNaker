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

from spinn_utilities.overrides import overrides
from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyAndMaskConstraint)
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utility_models import MultiCastCommand
from spynnaker.pyNN.exceptions import SpynnakerException


def get_y_from_fpga_retina(key, mode):
    if mode == 128:
        return key & 0x7f
    elif mode == 64:
        return key & 0x3f
    elif mode == 32:
        return key & 0x1f
    elif mode == 16:
        return key & 0xf
    return None


def get_x_from_fpga_retina(key, mode):
    if mode == 128:
        return (key >> 7) & 0x7f
    elif mode == 64:
        return (key >> 6) & 0x3f
    elif mode == 32:
        return (key >> 5) & 0x1f
    elif mode == 16:
        return (key >> 4) & 0xf
    return None


def get_spike_value_from_fpga_retina(key, mode):
    if mode == 128:
        return (key >> 14) & 0x1
    elif mode == 64:
        return (key >> 14) & 0x1
    elif mode == 32:
        return (key >> 14) & 0x1
    elif mode == 16:
        return (key >> 14) & 0x1
    return None


class ExternalFPGARetinaDevice(
        ApplicationSpiNNakerLinkVertex, AbstractSendMeMulticastCommandsVertex):
    __slots__ = [
        "__fixed_key",
        "__fixed_mask"]

    MODE_128 = "128"
    MODE_64 = "64"
    MODE_32 = "32"
    MODE_16 = "16"
    UP_POLARITY = "UP"
    DOWN_POLARITY = "DOWN"
    MERGED_POLARITY = "MERGED"

    def __init__(
            self, mode, retina_key, spinnaker_link_id, polarity,
            label=None, board_address=None):
        """
        :param str mode: The retina "mode"
        :param int retina_key: The value of the top 16-bits of the key
        :param int spinnaker_link_id:
            The SpiNNaker link to which the retina is connected
        :param str polarity: The "polarity" of the retina data
        :param str label:
        :param str board_address:
        """
        # pylint: disable=too-many-arguments
        fixed_n_neurons = self.get_n_neurons(mode, polarity)
        super().__init__(
            n_atoms=fixed_n_neurons, spinnaker_link_id=spinnaker_link_id,
            label=label, board_address=board_address, incoming=True,
            outgoing=True)

        self.__fixed_key = (retina_key & 0xFFFF) << 16
        self.__fixed_mask = 0xFFFF8000
        if polarity == self.UP_POLARITY:
            self.__fixed_key |= 0x4000

        self.__fixed_mask = self._get_mask(mode)

        self.add_constraint(FixedKeyAndMaskConstraint([
            BaseKeyAndMask(self.__fixed_key, self.__fixed_mask)]))

    def _get_mask(self, mode):
        if mode == ExternalFPGARetinaDevice.MODE_128:
            return 0xFFFFC000
        elif mode == ExternalFPGARetinaDevice.MODE_64:
            return 0xFFFFF000
        elif mode == ExternalFPGARetinaDevice.MODE_32:
            return 0xFFFFFC00
        elif mode == ExternalFPGARetinaDevice.MODE_16:
            return 0xFFFFFF00
        raise SpynnakerException(
            "the FPGA retina does not recognise this mode")

    @staticmethod
    def get_n_neurons(mode, polarity):
        if mode == ExternalFPGARetinaDevice.MODE_128:
            if (polarity == ExternalFPGARetinaDevice.UP_POLARITY or
                    polarity == ExternalFPGARetinaDevice.DOWN_POLARITY):
                return 128 * 128
            return 128 * 128 * 2
        elif mode == ExternalFPGARetinaDevice.MODE_64:
            if (polarity == ExternalFPGARetinaDevice.UP_POLARITY or
                    polarity == ExternalFPGARetinaDevice.DOWN_POLARITY):
                return 64 * 64
            return 64 * 64 * 2
        elif mode == ExternalFPGARetinaDevice.MODE_32:
            if (polarity == ExternalFPGARetinaDevice.UP_POLARITY or
                    polarity == ExternalFPGARetinaDevice.DOWN_POLARITY):
                return 32 * 32
            return 32 * 32 * 2
        elif mode == ExternalFPGARetinaDevice.MODE_16:
            if (polarity == ExternalFPGARetinaDevice.UP_POLARITY or
                    polarity == ExternalFPGARetinaDevice.DOWN_POLARITY):
                return 16 * 16
            return 16 * 16 * 2
        raise SpynnakerException(
            "the FPGA retina does not recognise this mode")

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        return [MultiCastCommand(
            key=0x0000FFFF, payload=1, repeat=5, delay_between_repeats=100)]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        return [MultiCastCommand(
            key=0x0000FFFE, payload=0, repeat=5, delay_between_repeats=100)]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
