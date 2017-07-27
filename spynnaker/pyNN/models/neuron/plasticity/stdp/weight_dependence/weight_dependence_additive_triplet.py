from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence\
    import AbstractHasAPlusAMinus
from spynnaker.pyNN.models.neuron.plasticity.stdp.weight_dependence\
    import AbstractWeightDependence


class WeightDependenceAdditiveTriplet(
        AbstractWeightDependence, AbstractHasAPlusAMinus):

    default_parameters = {'w_min': 0.0, 'w_max': 1.0, 'A3_plus': 0.01,
                          'A3_minus': 0.01}

    # noinspection PyPep8Naming
    def __init__(
            self, w_min=default_parameters['w_min'],
            w_max=default_parameters['w_max'],
            A3_plus=default_parameters['A3_plus'],
            A3_minus=default_parameters['A3_minus']):

        AbstractWeightDependence.__init__(self)
        AbstractHasAPlusAMinus.__init__(self)
        self._w_min = w_min
        self._w_max = w_max
        self._a3_plus = A3_plus
        self._a3_minus = A3_minus

    @property
    def w_min(self):
        return self._w_min

    @property
    def w_max(self):
        return self._w_max

    @property
    def A3_plus(self):
        return self._a3_plus

    @property
    def A3_minus(self):
        return self._a3_minus

    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightDependenceAdditiveTriplet):
            return False
        return (
            (self._w_min == weight_dependence.w_min) and
            (self._w_max == weight_dependence.w_max) and
            (self._a_plus == weight_dependence.A_plus) and
            (self._a_minus == weight_dependence.A_minus) and
            (self._a3_plus == weight_dependence.A3_plus) and
            (self._a3_minus == weight_dependence.A3_minus))

    @property
    def vertex_executable_suffix(self):
        return "additive"

    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms == 2:
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
            #                /standardmodels/synapses.html
            # Pre-multiply A+ and A- by Wmax
            spec.write_value(
                data=int(round(self._a_plus * self._w_max * w)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self._a_minus * self._w_max * w)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self._a3_plus * self._w_max * w)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self._a3_minus * self._w_max * w)),
                data_type=DataType.INT32)

    @property
    def weight_maximum(self):
        return self._w_max
