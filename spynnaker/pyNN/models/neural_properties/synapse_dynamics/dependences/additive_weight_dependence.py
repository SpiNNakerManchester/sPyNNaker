from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_weight_dependency import AbstractWeightDependency


class AdditiveWeightDependence(AbstractWeightDependency):

    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01,
                 A3_plus=None, A3_minus=None):
        AbstractWeightDependency.__init__(self, w_min=w_min, w_max=w_max,
                                          A_plus=A_plus, A_minus=A_minus,
                                          A3_plus=A3_plus, A3_minus=A3_minus)

    def is_weight_dependance_rule_part(self):
        return True

    def __eq__(self, other):
        if (other is None) or (not isinstance(other,
                                              AdditiveWeightDependence)):
            return False
        return ((self._w_min == other.w_min)
                and (self._w_max == other.w_max)
                and (self._A_plus == other.A_plus)
                and (self._A_minus == other.A_minus)
                and (self._A3_plus == other.A3_plus)
                and (self._A3_minus == other.A3_minus))

    def get_params_size_bytes(self, num_synapse_types, num_terms):
        if num_terms == 1:
            return (4 * 4) * num_synapse_types
        elif num_terms == 2:
            return (6 * 4) * num_synapse_types
        else:
            raise NotImplementedError(
                "Additive weight dependence only supports one or two terms")

    def write_plastic_params(self, spec, machine_time_step, weight_scales,
                             global_weight_scale, num_terms):
        # Loop through each synapse type's weight scale
        for w in weight_scales:
            # In the synaptic row IO, write weights as integers
            spec.write_value(
                data=int(round(self._w_min * w * global_weight_scale)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self._w_max * w * global_weight_scale)),
                data_type=DataType.INT32)

            # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN
            #                   /standardmodels/synapses.html
            # Pre-multiply A+ and A- by Wmax
            spec.write_value(
                data=int(round(self._A_plus * self._w_max * w
                               * global_weight_scale)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self._A_minus * self._w_max * w
                               * global_weight_scale)),
                data_type=DataType.INT32)

            # If triplet term is required, write A3+ and A3-, also multiplied
            # by Wmax
            if num_terms == 2:
                spec.write_value(
                    data=int(round(self._A3_plus * self._w_max * w
                                   * global_weight_scale)),
                    data_type=DataType.INT32)
                spec.write_value(
                    data=int(round(self._A3_minus * self._w_max * w
                                   * global_weight_scale)),
                    data_type=DataType.INT32)
            elif num_terms != 1:
                raise NotImplementedError("Additive weight dependence only"
                                          " supports one or two terms")

    @property
    def vertex_executable_suffix(self):
        return "additive"
