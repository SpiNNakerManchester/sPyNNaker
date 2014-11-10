from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_weight_dependency import AbstractWeightDependency


class AdditiveWeightDependence(AbstractWeightDependency):

    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01):
        AbstractWeightDependency.__init__(self, w_min=w_min, w_max=w_max,
                                          A_plus=A_plus, A_minus=A_minus)

    def is_weight_dependance_rule_part(self):
        return True
    
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, AdditiveWeightDependence)):
            return False
        return ((self._w_min == other.w_min)
                and (self._w_max == other.w_max)
                and (self._A_plus == other.A_plus)
                and (self._A_minus == other.A_minus))

    def get_params_size_bytes(self):
        return 4 * 4

    def get_vertex_executable_suffix(self):
        return "additive"
        
    def write_plastic_params(self, spec, machine_time_step, weight_scale):
        # In the synaptic row IO, write weights as integers
        spec.write_value(data=int(round(self._w_min * weight_scale)),
                         data_type=DataType.INT32)
        spec.write_value(data=int(round(self._w_max * weight_scale)),
                         data_type=DataType.INT32)

        # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN/standardmodels/synapses.html
        # Pre-multiply A+ and A- by Wmax
        spec.write_value(data=int(
                         round(self._A_plus * self._w_max * weight_scale)),
                         data_type=DataType.INT32)
        spec.write_value(data=int(
                         round(self._A_minus * self._w_max * weight_scale)),
                         data_type=DataType.INT32)
