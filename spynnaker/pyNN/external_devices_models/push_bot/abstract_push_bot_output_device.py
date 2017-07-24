from enum import Enum


class AbstractPushBotOutputDevice(Enum):

    def __new__(
            cls, value, protocol_property, min_value, max_value,
            time_between_send):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._protocol_property = protocol_property
        obj._min_value = min_value
        obj._max_value = max_value
        obj._time_between_send = time_between_send
        return obj

    @property
    def protocol_property(self):
        return self._protocol_property

    @property
    def min_value(self):
        return self._min_value

    @property
    def max_value(self):
        return self._max_value

    @property
    def time_between_send(self):
        return self._time_between_send
