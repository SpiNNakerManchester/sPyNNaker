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
        :returns: The number of neurons that will be sent out by the device.
        """
        raise NotImplementedError

    @abstractmethod
    def get_injector_parameters(self) -> Dict[str, Any]:
        """
        :returns:
           The parameters of the Spike Injector to use with this device.
        """
        raise NotImplementedError

    @abstractmethod
    def get_injector_label(self) -> str:
        """
        :returns: the label to give to the Spike Injector.
        """
        raise NotImplementedError

    @abstractmethod
    def get_translator(self) -> AbstractEthernetTranslator:
        """
        :returns: A translator of multicast commands to Ethernet commands.
        """
        raise NotImplementedError

    @abstractmethod
    def get_database_connection(self) -> SpynnakerLiveSpikesConnection:
        """
        :returns: A Database Connection instance that this device uses to
             inject packets.
        """
        raise NotImplementedError
