from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence


class WeightDependenceERBPad(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    __slots__ = [
        "_w_max",
        "_w_min",
        "_do_reg",
        "_reg_rate"
        ]

    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0, reg_rate=0.0):
        super(WeightDependenceERBPad, self).__init__()
        self._w_min = w_min
        self._w_max = w_max
        self._reg_rate = reg_rate

    @property
    def w_min(self):
        return self._w_min

    @property
    def w_max(self):
        return self._w_max

    @property
    def reg_rate(self):
        return self._reg_rate

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightDependenceERBPad):
            return False
        return (
            (self._w_min == weight_dependence.w_min) and
            (self._w_max == weight_dependence.w_max) and
            (self.A_plus == weight_dependence.A_plus) and
            (self.A_minus == weight_dependence.A_minus))

    @property
    def vertex_executable_suffix(self):
        return "weight"

    @overrides(AbstractWeightDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms != 1:
            raise NotImplementedError(
                "erbp weight dependence only supports one term")
        return (4 * 5) * n_synapse_types

    @overrides(AbstractWeightDependence.write_parameters)
    def write_parameters(
            self, spec, machine_time_step, weight_scales, n_weight_terms):
        # Loop through each synapse type's weight scale
        for w in weight_scales:

            # Scale the weights
            spec.write_value(
                data=int(round(self._w_min * w)), data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self._w_max * w)), data_type=DataType.INT32)

            # Pre-multiply A+ and A- by Wmax
            spec.write_value(
                data=int(round(self.A_plus * (1 << 15))), # * self._w_max ),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self.A_minus * (1 << 15))), # * self._w_max ,
                data_type=DataType.INT32)

            spec.write_value(self._reg_rate, data_type=DataType.S1615)

    @property
    def weight_maximum(self):
        return self._w_max

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['w_min', 'w_max', 'A_plus', 'A_minus']
