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
from spynnaker.pyNN.external_devices_models import AbstractEthernetSensor
from .push_bot_translator import PushBotTranslator
from .push_bot_wifi_connection import get_pushbot_wifi_connection
from .push_bot_retina_connection import PushBotRetinaConnection
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotRetinaDevice)


class PushBotEthernetRetinaDevice(
        AbstractPushBotRetinaDevice, AbstractEthernetSensor):
    def __init__(
            self, protocol, resolution, pushbot_ip_address, pushbot_port=56000,
            injector_port=None, local_host=None, local_port=None,
            retina_injector_label="PushBotRetinaInjector"):
        """
        :param protocol:
        :type protocol: MunichIoEthernetProtocol
        :param resolution:
        :type resolution:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotRetinaResolution
        :param pushbot_ip_address:
        :param pushbot_port:
        :param injector_port:
        :param local_host:
        :param local_port:
        :param retina_injector_label:
        """
        # pylint: disable=too-many-arguments
        super().__init__(protocol, resolution)
        pushbot_wifi_connection = get_pushbot_wifi_connection(
            pushbot_ip_address, pushbot_port)
        self.__translator = PushBotTranslator(
            protocol, pushbot_wifi_connection)
        self.__injector_port = injector_port
        self.__retina_injector_label = retina_injector_label

        self.__database_connection = PushBotRetinaConnection(
            self.__retina_injector_label, pushbot_wifi_connection, resolution,
            local_host, local_port)

    @overrides(AbstractEthernetSensor.get_n_neurons)
    def get_n_neurons(self):
        return self._resolution.value.n_neurons

    @overrides(AbstractEthernetSensor.get_injector_parameters)
    def get_injector_parameters(self):
        return {"port": self.__injector_port}

    @overrides(AbstractEthernetSensor.get_injector_label)
    def get_injector_label(self):
        return self.__retina_injector_label

    @overrides(AbstractEthernetSensor.get_translator)
    def get_translator(self):
        return self.__translator

    @overrides(AbstractEthernetSensor.get_database_connection)
    def get_database_connection(self):
        """
        :rtype: PushBotRetinaConnection
        """
        return self.__database_connection
