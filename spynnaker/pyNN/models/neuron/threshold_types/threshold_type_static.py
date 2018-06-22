from spinn_utilities.overrides import overrides
from .abstract_threshold_type import AbstractThresholdType

from data_specification.enums import DataType
from spynnaker.pyNN.utilities import utility_calls

V_THRESH = "v_thresh"

UNITS = {V_THRESH: "mV"}


class ThresholdTypeStatic(AbstractThresholdType):
    """ A threshold that is a static value
    """
    __slots__ = ["_v_thresh"]

    def __init__(self, v_thresh):
        self._v_thresh = v_thresh

    @overrides(AbstractThresholdType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # Just a comparison, but 2 just in case!
        return 2 * n_neurons

    @overrides(AbstractThresholdType.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        # 1 parameter per neuron (4 bytes each)
        return (1 * 4 * n_neurons)

    @overrides(AbstractThresholdType.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        # 1 parameter per neuron (4 bytes each)
        return (1 * 4 * n_neurons)

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters.set_value(V_THRESH, self._v_thresh)

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

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
            (parameters[V_THRESH], DataType.S1615)
        ]
        return utility_calls.get_parameter_data(items, vertex_slice)

    @overrides(AbstractThresholdType.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):

        # Read the data
        types = [DataType.S1615 * 1]
        offset, (_v_thresh) = \
            utility_calls.read_parameter_data(
                types, data, offset, vertex_slice.n_atoms)

        return offset

    @property
    def v_thresh(self):
        return self._v_thresh

    @v_thresh.setter
    def v_thresh(self, v_thresh):
        self._v_thresh = v_thresh
