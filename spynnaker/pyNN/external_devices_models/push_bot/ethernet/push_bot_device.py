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
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.external_devices_models import (
    AbstractMulticastControllableDevice)


class PushBotEthernetDevice(
        AbstractMulticastControllableDevice, metaclass=AbstractBase):
    """ An arbitrary PushBot device
    """

    def __init__(
            self, protocol, device, uses_payload, time_between_send):
        """
        :param protocol: The protocol instance to get commands from
        :type protocol: MunichIoEthernetProtocol
        :param device: The Enum instance of the device to control
        :type device: AbstractPushBotOutputDevice
        :param uses_payload: True if the device uses a payload for control
        :type uses_payload: bool
        """
        self.__protocol = protocol
        self.__device = device
        self.__uses_payload = uses_payload
        self.__time_between_send = time_between_send
        if time_between_send is None:
            self.__time_between_send = device.time_between_send

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_key)
    def device_control_key(self):
        return self.__device.protocol_property.fget(self.__protocol)

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_partition_id)
    def device_control_partition_id(self):
        return "{}_PARTITION_ID".format(self.__device.name)

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_uses_payload)
    def device_control_uses_payload(self):
        return self.__uses_payload

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_min_value)
    def device_control_min_value(self):
        return self.__device.min_value

    @property
    @overrides(AbstractMulticastControllableDevice.device_control_max_value)
    def device_control_max_value(self):
        return self.__device.max_value

    @property
    @overrides(AbstractMulticastControllableDevice
               .device_control_timesteps_between_sending)
    def device_control_timesteps_between_sending(self):
        return self.__time_between_send

    @property
    @overrides(AbstractMulticastControllableDevice
               .device_control_send_type)
    def device_control_send_type(self):
        return self.__device.send_type

    @property
    def protocol(self):
        """ The protocol instance, for use in the subclass

        :rtype: MunichIoEthernetProtocol
        """
        return self.__protocol

    @abstractmethod
    def set_command_protocol(self, command_protocol):
        """ Set the protocol use to send setup and shutdown commands,\
            separately from the protocol used to control the device.

        :param command_protocol: The protocol to use for this device
        :type command_protocol:
            ~spynnaker.pyNN.protocols.MunichIoSpiNNakerLinkProtocol
        """
