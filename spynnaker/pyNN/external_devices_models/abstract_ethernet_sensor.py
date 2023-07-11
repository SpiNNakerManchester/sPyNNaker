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
from typing import Any, Dict, TYPE_CHECKING
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
if TYPE_CHECKING:
    from spynnaker.pyNN.connections import SpynnakerLiveSpikesConnection
    from .abstract_ethernet_translator import AbstractEthernetTranslator


class AbstractEthernetSensor(object, metaclass=AbstractBase):
    """
    An Ethernet-connected device that can send events (spikes) to SpiNNaker
    via a Spike Injector.
    """
    __slots__ = ()

    @abstractmethod
    def get_n_neurons(self) -> int:
        """
        Get the number of neurons that will be sent out by the device.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def get_injector_parameters(self) -> Dict[str, Any]:
        """
        Get the parameters of the Spike Injector to use with this device.

        :rtype: dict(str,Any)
        """
        raise NotImplementedError

    @abstractmethod
    def get_injector_label(self) -> str:
        """
        Get the label to give to the Spike Injector.

        :rtype: str
        """
        raise NotImplementedError

    @abstractmethod
    def get_translator(self) -> AbstractEthernetTranslator:
        """
        Get a translator of multicast commands to Ethernet commands.

        :rtype: AbstractEthernetTranslator
        """
        raise NotImplementedError

    @abstractmethod
    def get_database_connection(self) -> SpynnakerLiveSpikesConnection:
        """
        Get a Database Connection instance that this device uses to inject
        packets.

        :rtype: SpynnakerLiveSpikesConnection
        """
        raise NotImplementedError
