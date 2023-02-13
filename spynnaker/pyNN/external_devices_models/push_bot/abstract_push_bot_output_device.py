# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
