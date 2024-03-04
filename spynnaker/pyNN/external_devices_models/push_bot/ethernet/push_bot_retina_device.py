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

from typing import Any, Dict

from spinn_utilities.overrides import overrides

from spynnaker.pyNN.external_devices_models import AbstractEthernetSensor
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotRetinaDevice)

from .push_bot_retina_connection import PushBotRetinaConnection
from .push_bot_translator import PushBotTranslator
from .push_bot_wifi_connection import get_pushbot_wifi_connection


class PushBotEthernetRetinaDevice(
        AbstractPushBotRetinaDevice, AbstractEthernetSensor):
    """
    A PushBot retina over Ethernet
    """
    def __init__(
            self, protocol, resolution, pushbot_ip_address, pushbot_port=56000,
            injector_port=None, local_host=None, local_port=None,
            retina_injector_label="PushBotRetinaInjector"):
        """
        :param MunichIoEthernetProtocol protocol:
        :param PushBotRetinaResolution resolution:
        :param str pushbot_ip_address:
        :param int pushbot_port:
        :param int injector_port:
        :param str local_host:
        :param int local_port:
        :param str retina_injector_label:
        """
        # pylint: disable=too-many-arguments
        super().__init__(protocol, None)
        pushbot_wifi_connection = get_pushbot_wifi_connection(
            pushbot_ip_address, pushbot_port)
        self.__translator = PushBotTranslator(
            protocol, pushbot_wifi_connection)
        self.__injector_port = injector_port
        self.__retina_injector_label = retina_injector_label

        self.__database_connection = PushBotRetinaConnection(
            self.__retina_injector_label, pushbot_wifi_connection, resolution,
            local_host, local_port)
        self.__n_neurons = resolution.value.n_neurons

    @overrides(AbstractEthernetSensor.get_n_neurons)
    def get_n_neurons(self) -> int:
        return self.__n_neurons

    @overrides(AbstractEthernetSensor.get_injector_parameters)
    def get_injector_parameters(self) -> Dict[str, Any]:
        return {"port": self.__injector_port}

    @overrides(AbstractEthernetSensor.get_injector_label)
    def get_injector_label(self) -> str:
        return self.__retina_injector_label

    @overrides(AbstractEthernetSensor.get_translator)
    def get_translator(self) -> PushBotTranslator:
        return self.__translator

    @overrides(AbstractEthernetSensor.get_database_connection)
    def get_database_connection(self) -> PushBotRetinaConnection:
        """
        :rtype: PushBotRetinaConnection
        """
        return self.__database_connection
