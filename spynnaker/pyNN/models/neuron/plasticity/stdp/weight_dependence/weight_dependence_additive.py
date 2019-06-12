from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence


class WeightDependenceAdditive(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    __slots__ = [
        "__w_max",
        "__w_min"]

    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0):
        super(WeightDependenceAdditive, self).__init__()
        self.__w_min = w_min
        self.__w_max = w_max

    @property
    def w_min(self):
        return self.__w_min

    @property
    def w_max(self):
        return self.__w_max

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightDependenceAdditive):
            return False
        return (
            (self.__w_min == weight_dependence.w_min) and
            (self.__w_max == weight_dependence.w_max) and
            (self.A_plus == weight_dependence.A_plus) and
            (self.A_minus == weight_dependence.A_minus))

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
                data=int(round(self.__w_min * w)), data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self.__w_max * w)), data_type=DataType.INT32)

            # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN
            #                /standardmodels/synapses.html
            # Pre-multiply A+ and A- by Wmax
            spec.write_value(
                data=int(round(self.A_plus * self.__w_max * w)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self.A_minus * self.__w_max * w)),
                data_type=DataType.INT32)

    @property
    def weight_maximum(self):
        return self.__w_max

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['w_min', 'w_max', 'A_plus', 'A_minus']
