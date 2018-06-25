from spinn_utilities import overrides
from .abstract_threshold_type import AbstractThresholdType
from data_specification.enums import DataType

V_THRESH = "v_thresh"

UNITS = {V_THRESH: "mV"}


class ThresholdTypeStatic(AbstractThresholdType):
    """ A threshold that is a static value
    """
    __slots__ = ["_v_thresh"]

    def __init__(self, v_thresh):
        super(ThresholdTypeStatic, self).__init__([
            DataType.S1615])  # v_thresh
        self._v_thresh = v_thresh

    @overrides(AbstractThresholdType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # Just a comparison, but 2 just in case!
        return 2 * n_neurons

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
    def get_values(self, parameters, state_variables, vertex_slice):

        # Add the rest of the data
        return [parameters[V_THRESH]]

    @overrides(AbstractThresholdType.read_data)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_v_thresh,) = values

    @property
    def v_thresh(self):
        return self._v_thresh

    @v_thresh.setter
    def v_thresh(self, v_thresh):
        self._v_thresh = v_thresh
