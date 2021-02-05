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
from spynnaker.pyNN.external_devices_models\
    .abstract_multicast_controllable_device import (
        SendType)


class AbstractPushBotOutputDevice(Enum):
    """ Superclass of all output device descriptors
    """

    def __new__(
            cls, value, protocol_property, min_value, max_value,
            time_between_send, send_type=SendType.SEND_TYPE_INT):
        # pylint: disable=too-many-arguments, protected-access
        obj = object.__new__(cls)
        obj._value_ = value
        obj._protocol_property = protocol_property
        obj._min_value = min_value
        obj._max_value = max_value
        obj._time_between_send = time_between_send
        obj._send_type = send_type
        return obj

    @property
    def protocol_property(self):
        """
        :rtype: property
        """
        return self._protocol_property

    @property
    def min_value(self):
        return self._min_value

    @property
    def max_value(self):
        return self._max_value

    @property
    def time_between_send(self):
        """
        :rtype: int
        """
        return self._time_between_send

    @property
    def send_type(self):
        """
        :rtype: SendType
        """
        return self._send_type
