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

from enum import Enum
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class SendType(Enum):
    """
    The data type to be sent in the payload of the multicast packet.
    """
    #: Signed integer
    SEND_TYPE_INT = 0
    #: Unsigned integer
    SEND_TYPE_UINT = 1
    #: Signed accum (s15.16)
    SEND_TYPE_ACCUM = 2
    #: Unsigned accum (u16.16)
    SEND_TYPE_UACCUM = 3
    #: Signed fract (s0.31)
    SEND_TYPE_FRACT = 4
    #: Unsigned fract (u0.32)
    SEND_TYPE_UFRACT = 5


class AbstractMulticastControllableDevice(object, metaclass=AbstractBase):
    """
    A device that can be controlled by sending multicast packets to it,
    either directly, or via Ethernet using an AbstractEthernetTranslator.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def device_control_partition_id(self):
        """
        A partition ID to give to an outgoing edge partition that will
        control this device.

        :rtype: str
        """

    @property
    @abstractmethod
    def device_control_key(self):
        """
        The key that must be sent to the device to control it.

        :rtype: int
        """

    @property
    @abstractmethod
    def device_control_uses_payload(self):
        """
        Whether the control of the device accepts an arbitrary valued
        payload, the value of which will change the devices behaviour.

        :rtype: bool
        """

    @property
    @abstractmethod
    def device_control_min_value(self):
        """
        The minimum value to send to the device.

        :rtype: float
        """

    @property
    @abstractmethod
    def device_control_max_value(self):
        """
        The maximum value to send to the device.

        :rtype: float
        """

    @property
    @abstractmethod
    def device_control_timesteps_between_sending(self):
        """
        The number of timesteps between sending commands to the device.
        This defines the "sampling interval" for the device.

        :rtype: int
        """

    @property
    @abstractmethod
    def device_control_send_type(self):
        """
        The type of data to be sent.

        :rtype: SendType
        """

    @property
    def device_control_scaling_factor(self):  # pragma: no cover
        """
        The scaling factor used to send the payload to this device.

        :rtype: int
        """
        return 1

    @property
    def device_control_first_send_timestep(self):
        """
        The first timestep that the device should send in (0 by default).

        :rtype: int
        """
        return 0
