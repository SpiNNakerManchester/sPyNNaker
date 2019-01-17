from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence


class WeightDependenceAdditive(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    __slots__ = [
        "_w_max",
        "_w_min"]

    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0):
        super(WeightDependenceAdditive, self).__init__()
        self._w_min = w_min
        self._w_max = w_max

    @property
    def w_min(self):
        return self._w_min

    @property
    def w_max(self):
        return self._w_max

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightDependenceAdditive):
            return False
        return (
            (self._w_min == weight_dependence.w_min) and
            (self._w_max == weight_dependence.w_max) and
            (self._a_plus == weight_dependence.A_plus) and
            (self._a_minus == weight_dependence.A_minus))

    @property
    def vertex_executable_suffix(self):
        return "additive"

    @overrides(AbstractWeightDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms != 1:
            raise NotImplementedError(
                "Additive weight dependence only supports one term")
        return (4 * 4) * n_synapse_types

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

            # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN
            #                /standardmodels/synapses.html
            # Pre-multiply A+ and A- by Wmax
            spec.write_value(
                data=int(round(self._a_plus * self._w_max * w)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self._a_minus * self._w_max * w)),
                data_type=DataType.INT32)

    @property
    def weight_maximum(self):
        return self._w_max

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['w_min', 'w_max', 'A_plus', 'A_minus']
