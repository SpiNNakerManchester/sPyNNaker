from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.threshold_types import AbstractThresholdType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import utility_calls

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
    __slots__ = ["_device"]

    def __init__(self, device):
        self._device = device

    @overrides(AbstractThresholdType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 10 * n_neurons

    @overrides(AbstractThresholdType.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # 6 parameter per device (4 bytes each)
        return (6 * 4 * n_neurons)

    @overrides(AbstractThresholdType.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # 6 parameter per device (4 bytes each)
        return (6 * 4 * n_neurons)

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[DEVICE].set_value(self._device)

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[TIME_UNTIL_SEND].set_value(0)

    @overrides(AbstractThresholdType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractThresholdType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractThresholdType.get_data)
    def get_data(self, parameters, state_variables, vertex_slice):

        # Add the rest of the data
        items = [
            (parameters[DEVICE].apply_operation(
                lambda x: x.control_key), DataType.UINT32),
            (parameters[DEVICE].apply_operation(
                lambda x: x.device_control_uses_payload), DataType.UINT32),
            (parameters[DEVICE].apply_operation(
                lambda x: x.device_control_min_value), DataType.S1615),
            (parameters[DEVICE].apply_operation(
                lambda x: x.device_control_max_value), DataType.S1615),
            (parameters[DEVICE].apply_operation(
                lambda x: x.device_control_timesteps_between_sending),
                DataType.UINT32),

            # This is the "state" variable that keeps track of how many
            # timesteps to go before a send is done
            # Initially set this to a different number for each device, to
            # avoid them being in step with each other
            ([i for i in range(vertex_slice.n_atoms)], DataType.UINT32)
        ]
        return utility_calls.get_parameter_data(items, vertex_slice)

    @overrides(AbstractThresholdType.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data
        types = [DataType.UINT32, DataType.UINT32, DataType.S1615,
                 DataType.S1615, DataType.UINT32, DataType.UINT32]
        offset, (_key, _uses_payload, _min, _max, _between, time_until_send) =\
            utility_calls.read_parameter_data(
                types, data, offset, vertex_slice.n_atoms)

        utility_calls.copy_values(
            time_until_send, state_variables[TIME_UNTIL_SEND], vertex_slice)

        return offset
