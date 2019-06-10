from six import with_metaclass
from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.external_devices_models import (
    AbstractMulticastControllableDevice)


class PushBotEthernetDevice(with_metaclass(
        AbstractBase, AbstractMulticastControllableDevice)):
    """ An arbitrary PushBot device
    """

    def __init__(
            self, protocol, device, uses_payload, time_between_send):
        """
        :param protocol: The protocol instance to get commands from
        :param device: The Enum instance of the device to control
        :param uses_payload: True if the device uses a payload for control
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
        """
        return self.__protocol

    @abstractmethod
    def set_command_protocol(self, command_protocol):
        """ Set the protocol use to send setup and shutdown commands,\
            separately from the protocol used to control the device
        """
