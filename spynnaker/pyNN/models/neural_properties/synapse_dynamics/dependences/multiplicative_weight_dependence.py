from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_weight_dependency import AbstractWeightDependency


class MultiplicativeWeightDependence(AbstractWeightDependency):

    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01):
        AbstractWeightDependency.__init__(self, w_min=w_min, w_max=w_max,
                                          A_plus=A_plus, A_minus=A_minus)

    def is_weight_dependance_rule_part(self):
        return True

    def __eq__(self, other):
        if (other is None) or (not isinstance(other,
                                              MultiplicativeWeightDependence)):
            return False
        return ((self.w_min == other.w_min)
                and (self.w_max == other.w_max)
                and (self.A_plus == other.A_plus)
                and (self.A_minus == other.A_minus))

    def get_params_size_bytes(self, num_synapse_types, num_terms):
        if num_terms != 1:
            raise NotImplementedError(
                "Multiplicative weight dependence only supports single terms")

        return (4 * 4) * num_synapse_types

    def write_plastic_params(self, spec, machineTimeStep, weight_scales,
                             global_weight_scale, num_terms):
        if num_terms != 1:
            raise NotImplementedError(
                "Multiplicative weight dependence only supports single terms")

        # Loop through each synapse type's weight scale
        for w in weight_scales:
            spec.write_value(
                data=int(round(self.w_min * w * global_weight_scale)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self.w_max * w * global_weight_scale)),
                data_type=DataType.INT32)

            spec.write_value(
                data=int(round(self.A_plus * w * global_weight_scale)),
                data_type=DataType.INT32)
            spec.write_value(
                data=int(round(self.A_minus * w * global_weight_scale)),
                data_type=DataType.INT32)

    @property
    def vertex_executable_suffix(self):
        return "multiplicative"
