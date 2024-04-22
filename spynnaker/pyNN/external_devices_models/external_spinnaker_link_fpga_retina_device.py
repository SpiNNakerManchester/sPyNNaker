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
from typing import Iterable, List, Optional
from spinn_utilities.overrides import overrides
from pacman.model.routing_info import BaseKeyAndMask
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utility_models import MultiCastCommand
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.common import PopulationApplicationVertex


def get_y_from_fpga_retina(key: int, mode: int) -> Optional[int]:
    """
    :param int key:
    :param int mode:
    :rtype: int or None
    """
    if mode == 128:
        return key & 0x7f
    elif mode == 64:
        return key & 0x3f
    elif mode == 32:
        return key & 0x1f
    elif mode == 16:
        return key & 0xf
    return None


def get_x_from_fpga_retina(key: int, mode: int) -> Optional[int]:
    """
    :param int key:
    :param int mode:
    :rtype: int or None
    """
    if mode == 128:
        return (key >> 7) & 0x7f
    elif mode == 64:
        return (key >> 6) & 0x3f
    elif mode == 32:
        return (key >> 5) & 0x1f
    elif mode == 16:
        return (key >> 4) & 0xf
    return None


def get_spike_value_from_fpga_retina(key: int, mode: int) -> Optional[int]:
    """
    :param int key:
    :param int mode:
    :rtype: int or None
    """
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
        ApplicationSpiNNakerLinkVertex, PopulationApplicationVertex,
        AbstractSendMeMulticastCommandsVertex):
    """
    A retina connected by FPGA
    """
    __slots__ = (
        "__fixed_key",
        "__fixed_mask")

    MODE_128 = "128"
    MODE_64 = "64"
    MODE_32 = "32"
    MODE_16 = "16"
    UP_POLARITY = "UP"
    DOWN_POLARITY = "DOWN"
    MERGED_POLARITY = "MERGED"

    def __init__(
            self, mode: str, retina_key: int, spinnaker_link_id: int,
            polarity: str, label: Optional[str] = None,
            board_address: Optional[str] = None):
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

    @overrides(ApplicationSpiNNakerLinkVertex.get_fixed_key_and_mask)
    def get_fixed_key_and_mask(self, partition_id: str) -> BaseKeyAndMask:
        return BaseKeyAndMask(self.__fixed_key, self.__fixed_mask)

    def _get_mask(self, mode: str) -> int:
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
    def get_n_neurons(mode: str, polarity: str) -> int:
        """
        :param str mode: ``128`` or ``64`` or ``32`` or ``16``
        :param str parity: ``UP`` or ``DOWN`` or ``MERGED``
        :rtype: int
        """
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
    def start_resume_commands(self) -> Iterable[MultiCastCommand]:
        yield MultiCastCommand(
            key=0x0000FFFF, payload=1, repeat=5, delay_between_repeats=100)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self) -> Iterable[MultiCastCommand]:
        yield MultiCastCommand(
            key=0x0000FFFE, payload=0, repeat=5, delay_between_repeats=100)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self) -> List[MultiCastCommand]:
        return []
