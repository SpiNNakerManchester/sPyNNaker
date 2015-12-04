from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence\
    .abstract_weight_dependence import AbstractWeightDependence


class WeightDependenceAdditive(AbstractWeightDependence):

    # noinspection PyPep8Naming
    def __init__(
            self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01,
            A3_plus=None, A3_minus=None):
        AbstractWeightDependence.__init__(self)
        self._w_min = w_min
        self._w_max = w_max
        self._A_plus = A_plus
        self._A_minus = A_minus
        self._A3_plus = A3_plus
        self._A3_minus = A3_minus

    @property
    def w_min(self):
        return self._w_min

    @property
    def w_max(self):
        return self._w_max

    @property
    def A_plus(self):
        return self._A_plus

    @property
    def A_minus(self):
        return self._A_minus

    @property
    def A3_plus(self):
        return self._A3_plus

    @property
    def A3_minus(self):
        return self._A3_minus

    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightDependenceAdditive):
            return False
        return (
            (self._w_min == weight_dependence._w_min) and
            (self._w_max == weight_dependence._w_max) and
            (self._A_plus == weight_dependence._A_plus) and
            (self._A_minus == weight_dependence._A_minus) and
            (self._A3_plus == weight_dependence._A3_plus) and
            (self._A3_minus == weight_dependence._A3_minus))

    @property
    def vertex_executable_suffix(self):
        return "additive"

    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms == 1:
            return (4 * 4) * n_synapse_types
        elif n_weight_terms == 2:
            return (6 * 4) * n_synapse_types
        else:
            raise NotImplementedError(
                "Additive weight dependence only supports one or two terms")

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
            #                   /standardmodels/synapses.html
            # Pre-multiply A+ and A- by Wmax
            spec.write_value(
                data=int(round(self._A_plus * self._w_max * w)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self._A_minus * self._w_max * w)),
                data_type=DataType.INT32)

            # If triplet term is required, write A3+ and A3-, also multiplied
            # by Wmax
            if n_weight_terms == 2:
                spec.write_value(
                    data=int(round(self._A3_plus * self._w_max * w)),
                    data_type=DataType.INT32)
                spec.write_value(
                    data=int(round(self._A3_minus * self._w_max * w)),
                    data_type=DataType.INT32)
            elif n_weight_terms != 1:
                raise NotImplementedError(
                    "Additive weight dependence only supports one or two"
                    " terms")

    @property
    def weight_maximum(self):
        return self._w_max
