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

from __future__ import annotations
from typing import List, Iterable, TYPE_CHECKING
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
if TYPE_CHECKING:
    from .abstract_ethernet_translator import AbstractEthernetTranslator
    from .abstract_multicast_controllable_device import (
        AbstractMulticastControllableDevice)


class AbstractEthernetController(object, metaclass=AbstractBase):
    """
    A controller that can send multicast packets which can be received
    over Ethernet and translated to control an external device.
    """
    __slots__ = ()

    @abstractmethod
    def get_message_translator(self) -> AbstractEthernetTranslator:
        """
        Get the translator of messages.

        :rtype: AbstractEthernetTranslator
        """
        raise NotImplementedError

    @abstractmethod
    def get_external_devices(self) -> Iterable[
            AbstractMulticastControllableDevice]:
        """
        Get the external devices that are to be controlled by the controller.

        :rtype: iterable(AbstractMulticastControllableDevice)
        """
        raise NotImplementedError

    @abstractmethod
    def get_outgoing_partition_ids(self) -> List[str]:
        """
        Get the partition IDs of messages coming out of the controller.

        :rtype: list(str)
        """
        raise NotImplementedError
