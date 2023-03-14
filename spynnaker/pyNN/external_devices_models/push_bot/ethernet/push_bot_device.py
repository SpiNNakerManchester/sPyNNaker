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

from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.external_devices_models import (
    AbstractMulticastControllableDevice)

# The default timestep to use for first send.  Avoids clashes with other
# control commands.
_DEFAULT_FIRST_SEND_TIMESTEP = 100


class PushBotEthernetDevice(
        AbstractMulticastControllableDevice, metaclass=AbstractBase):
    """ An arbitrary PushBot device
    """

    def __init__(
            self, protocol, device, uses_payload, time_between_send,
            first_send_timestep=_DEFAULT_FIRST_SEND_TIMESTEP):
        """
        :param MunichIoEthernetProtocol protocol:
            The protocol instance to get commands from
        :param AbstractPushBotOutputDevicedevice:
            The Enum instance of the device to control
        :param bool uses_payload:
            True if the device uses a payload for control
        :param int time_between_send: The timesteps between sending
        :param int first_send_timestep: The first timestep to send
        """
        self.__protocol = protocol
        self.__device = device
        self.__uses_payload = uses_payload
        self.__time_between_send = time_between_send
        if time_between_send is None:
            self.__time_between_send = device.time_between_send
        self.__first_send_timestep = first_send_timestep

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
    @overrides(AbstractMulticastControllableDevice
               .device_control_first_send_timestep)
    def device_control_first_send_timestep(self):
        return self.__first_send_timestep

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
