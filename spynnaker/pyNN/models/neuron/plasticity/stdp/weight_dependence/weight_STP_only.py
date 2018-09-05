from spinn_utilities.overrides import overrides
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence


class WeightSTPOnly(
        AbstractWeightDependence, AbstractHasAPlusAMinus):

    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0):
        AbstractWeightDependence.__init__(self)
        AbstractHasAPlusAMinus.__init__(self)
        self._w_min = w_min
        self._w_max = w_max

    @property
    def w_min(self):
        return self._w_min

    @property
    def w_max(self):
        return self._w_max

    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightSTPOnly):
            return False
        return (
            (self._w_min == weight_dependence.w_min) and
            (self._w_max == weight_dependence.w_max) and
            (self._a_plus == weight_dependence.A_plus) and
            (self._a_minus == weight_dependence.A_minus))

    @property
    def vertex_executable_suffix(self):
        return "only"

    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms == 1:
            return 0
        else:
            raise NotImplementedError(
                "STP only supports one weight term")

    def write_parameters(
            self, spec, machine_time_step, weight_scales, n_weight_terms):
        # no parameters to write
        pass

    @property
    def weight_maximum(self):
        return self._w_max

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['w_min', 'w_max', 'A_plus', 'A_minus']
