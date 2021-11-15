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

from enum import Enum
from spinn_utilities.abstract_base import AbstractBase, abstractproperty


class SendType(Enum):
    """ The data type to be sent in the payload of the multicast packet
    """
    SEND_TYPE_INT = 0
    SEND_TYPE_UINT = 1
    SEND_TYPE_ACCUM = 2
    SEND_TYPE_UACCUM = 3
    SEND_TYPE_FRACT = 4
    SEND_TYPE_UFRACT = 5


class AbstractMulticastControllableDevice(object, metaclass=AbstractBase):
    """ A device that can be controlled by sending multicast packets to it,\
        either directly, or via Ethernet using an AbstractEthernetTranslator
    """
    __slots__ = []

    @abstractproperty
    def device_control_partition_id(self):
        """ A partition ID to give to an outgoing edge partition that will\
            control this device

        :rtype: str
        """

    @abstractproperty
    def device_control_key(self):
        """ The key that must be sent to the device to control it

        :rtype: int
        """

    @abstractproperty
    def device_control_uses_payload(self):
        """ True if the control of the device accepts an arbitrary valued\
            payload, the value of which will change the devices behaviour

        :rtype: bool
        """

    @abstractproperty
    def device_control_min_value(self):
        """ The minimum value to send to the device

        :rtype: float
        """

    @abstractproperty
    def device_control_max_value(self):
        """ The maximum value to send to the device

        :rtype: float
        """

    @abstractproperty
    def device_control_timesteps_between_sending(self):
        """ The number of timesteps between sending commands to the device.\
            This defines the "sampling interval" for the device.

        :rtype: int
        """

    @abstractproperty
    def device_control_send_type(self):
        """ The type of data to be sent.

        :rtype: SendType
        """

    @property
    def device_control_scaling_factor(self):  # pragma: no cover
        """ The scaling factor used to send the payload to this device.

        :rtype: int
        """
        return 1
