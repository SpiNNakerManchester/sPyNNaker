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
        state_variables[TS_NEXT_SEND] = 0
