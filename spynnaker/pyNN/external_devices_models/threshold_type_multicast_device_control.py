# Copyright (c) 2017 The University of Manchester
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

from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.threshold_types import AbstractThresholdType
from spynnaker.pyNN.utilities.struct import Struct

DEVICE = "device"
KEY = "key"
SCALE = "scale"
MIN = "min"
MAX = "max"
TS_INTER_SEND = "ts_inter_send"
TS_NEXT_SEND = "ts_next_send"
TYPE = "type"


class ThresholdTypeMulticastDeviceControl(AbstractThresholdType):
    """ A threshold type that can send multicast keys with the value of\
        membrane voltage as the payload
    """
    __slots__ = ["__devices"]

    def __init__(self, devices):
        """
        :param list(AbstractMulticastControllableDevice) device:
        """
        super().__init__(
            [Struct([
                (DataType.UINT32, KEY),
                (DataType.UINT32, SCALE),
                (DataType.S1615, MIN),
                (DataType.S1615, MAX),
                (DataType.UINT32, TS_INTER_SEND),
                (DataType.UINT32, TS_NEXT_SEND),
                (DataType.UINT32, TYPE)])],
            {KEY: "", SCALE: "", MIN: "mV", MAX: "mV",
             TS_INTER_SEND: "time steps", TS_NEXT_SEND: "time steps",
             TYPE: ""})
        self.__devices = devices

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[KEY] = [
            d.device_control_key for d in self.__devices]
        parameters[SCALE] = [
            d.device_control_scaling_factor for d in self.__devices]
        parameters[MIN] = [
            d.device_control_min_value for d in self.__devices]
        parameters[MAX] = [
            d.device_control_max_value for d in self.__devices]
        parameters[TS_INTER_SEND] = [
            d.device_control_timesteps_between_sending for d in self.__devices]
        parameters[TYPE] = [
            d.device_control_send_type.value for d in self.__devices]

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[TS_NEXT_SEND] = [
            d.device_control_first_send_timestep for d in self.__devices]
