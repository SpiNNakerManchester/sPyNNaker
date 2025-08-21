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

from decimal import Decimal
from enum import Enum
from spynnaker.pyNN.external_devices_models\
    .abstract_multicast_controllable_device import (
        SendType)


class AbstractPushBotOutputDevice(Enum):
    """
    Superclass of all output device descriptors.
    """

    def __init__(
            self, value: int, protocol_property: property, min_value: int,
            max_value: Decimal, time_between_send: int,
            send_type: SendType = SendType.SEND_TYPE_INT):
        """
        :param value: Enum ID
        :param protocol_property: The protocol property of the output device
        :param min_value: smallest value allowed
        :param max_value: largest value allowed
        :param time_between_send: Time between sends
        :param send_type: The type of data to be sent.
        """
        self._value_ = value
        self._protocol_property = protocol_property
        self._min_value = min_value
        self._max_value = max_value
        self._time_between_send = time_between_send
        self._send_type = send_type

    @property
    def protocol_property(self) -> property:
        """
        The protocol property of the output device
        """
        return self._protocol_property

    @property
    def min_value(self) -> int:
        """
        The minimum value of the output device
        """
        return self._min_value

    @property
    def max_value(self) -> Decimal:
        """
        Max Value
        """
        return self._max_value

    @property
    def time_between_send(self) -> int:
        """
        Time between sends
        """
        return self._time_between_send

    @property
    def send_type(self) -> SendType:
        """
        The type of data to be sent.
        """
        return self._send_type
