from data_specification.enums import DataType
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.models.neuron.threshold_types import AbstractThresholdType
from enum import Enum


class _THRESHOLD_TYPE_MULTICAST(Enum):
    DEVICE_CONTROL_KEY = (1, DataType.UINT32)
    DEVICE_CONTROLS_USES_PAYLOAD = (2, DataType.UINT32)
    DEVICE_CONTROL_MIN_VALUE = (3, DataType.S1615)
    DEVICE_CONTROL_MAX_VALUE = (4, DataType.S1615)
    DEVICE_CONTROL_TIMESTEPS_BETWEEN_SENDING = (5, DataType.UINT32)
    DEVICE_STATE = (6, DataType.UINT32)

    def __new__(cls, value, data_type, doc=""):
        # pylint: disable=protected-access
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        obj.__doc__ = doc
        return obj

    @property
    def data_type(self):
        return self._data_type


class ThresholdTypeMulticastDeviceControl(AbstractThresholdType):
    """ A threshold type that can send multicast keys with the value of\
        membrane voltage as the payload
    """

    def __init__(self, devices):
        AbstractThresholdType.__init__(self)
        self._devices = devices

    def get_n_threshold_parameters(self):
        return 6

    def get_threshold_parameter_types(self):
        return [item.data_type for item in _THRESHOLD_TYPE_MULTICAST]

    def get_threshold_parameters(self):
        timings = [device.device_control_timesteps_between_sending
                   for device in self._devices]
        max_time = max(timings)
        time_between_send = int(max_time) / len(self._devices)

        return [
            NeuronParameter(
                [device.device_control_key for device in self._devices],
                _THRESHOLD_TYPE_MULTICAST.DEVICE_CONTROL_KEY.data_type),
            NeuronParameter(
                [1 if device.device_control_uses_payload else 0
                 for device in self._devices],
                _THRESHOLD_TYPE_MULTICAST.DEVICE_CONTROLS_USES_PAYLOAD
                .data_type),
            NeuronParameter(
                [device.device_control_min_value for device in self._devices],
                _THRESHOLD_TYPE_MULTICAST.DEVICE_CONTROL_MIN_VALUE.data_type),
            NeuronParameter(
                [device.device_control_max_value for device in self._devices],
                _THRESHOLD_TYPE_MULTICAST.DEVICE_CONTROL_MAX_VALUE.data_type),
            NeuronParameter(
                timings,
                _THRESHOLD_TYPE_MULTICAST
                .DEVICE_CONTROL_TIMESTEPS_BETWEEN_SENDING.data_type),

            # This is the "state" variable that keeps track of how many
            # timesteps to go before a send is done
            # Initially set this to a different number for each device, to
            # avoid them being in step with each other
            NeuronParameter(
                [i * time_between_send for i, _ in enumerate(self._devices)],
                _THRESHOLD_TYPE_MULTICAST.DEVICE_STATE.data_type)
        ]

    def get_n_cpu_cycles_per_neuron(self):
        return 10
