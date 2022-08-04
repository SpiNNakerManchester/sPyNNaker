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

DEVICE = "device"
TIME_UNTIL_SEND = "time_until_send"

UNITS = {
    DEVICE: "",
    TIME_UNTIL_SEND: ""
}


class ThresholdTypeMulticastDeviceControl(AbstractThresholdType):
    """ A threshold type that can send multicast keys with the value of\
        membrane voltage as the payload
    """
    __slots__ = ["__device"]

    def __init__(self, device):
        """
        :param list(AbstractMulticastControllableDevice) device:
        """
        super().__init__([
            DataType.UINT32,   # control_key
            DataType.UINT32,   # control_uses_payload
            DataType.S1615,    # min_value
            DataType.S1615,    # max_value
            DataType.UINT32,   # time steps between sending
            DataType.UINT32,   # time steps until next send
            DataType.UINT32])  # type to send
        self.__device = device

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[DEVICE] = self.__device

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[TIME_UNTIL_SEND] = 0

    @overrides(AbstractThresholdType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractThresholdType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractThresholdType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        # Add the rest of the data
        return [parameters[DEVICE].apply_operation(
                    lambda x: x.device_control_key),
                parameters[DEVICE].apply_operation(
                    lambda x: x.device_control_scaling_factor
                    if x.device_control_uses_payload else 0),
                parameters[DEVICE].apply_operation(
                    lambda x: x.device_control_min_value),
                parameters[DEVICE].apply_operation(
                    lambda x: x.device_control_max_value),
                parameters[DEVICE].apply_operation(
                    lambda x: x.device_control_timesteps_between_sending),

                # This is the "state" variable that keeps track of how many
                # timesteps to go before a send is done
                # Set to a different value for each item to avoid being in step
                [i for i in range(vertex_slice.n_atoms)],
                parameters[DEVICE].apply_operation(
                    lambda x: x.device_control_send_type.value)]

    @overrides(AbstractThresholdType.update_values)
    def update_values(self, values, parameters, state_variables):
        # Read the data
        (_key, _uses_payload, _min, _max, _between, time_until_send,
         _send_type) = values
        state_variables[TIME_UNTIL_SEND] = time_until_send
