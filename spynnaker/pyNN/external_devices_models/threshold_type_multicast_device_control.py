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
TIME_UNTIL_SEND = "time_until_send"
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
    __slots__ = ["__device"]

    def __init__(self, device):
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
            {DEVICE: "", TIME_UNTIL_SEND: ""})
        self.__device = device

    @overrides(AbstractThresholdType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 10 * n_neurons

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[DEVICE] = self.__device

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[TIME_UNTIL_SEND] = 0

    @overrides(AbstractThresholdType.get_precomputed_values)
    def get_precomputed_values(self, parameters, state_variables, ts):
        return {
            KEY: parameters[DEVICE].apply_operation(
                lambda x: x.device_control_key),
            SCALE: parameters[DEVICE].apply_operation(
                lambda x: x.device_control_scaling_factor
                if x.device_control_uses_payload else 0),
            MIN: parameters[DEVICE].apply_operation(
                lambda x: x.device_control_min_value),
            MAX: parameters[DEVICE].apply_operation(
                lambda x: x.device_control_max_value),
            TS_INTER_SEND: parameters[DEVICE].apply_operation(
                lambda x: x.device_control_timesteps_between_sending),
            TS_NEXT_SEND: [0],
            TYPE: parameters[DEVICE].apply_operation(
                lambda x: x.device_control_send_type.value)
        }
