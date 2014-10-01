from data_specification.enums.data_type import DataType

class AdditiveWeightDependence(object):
    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01):
        self.w_min = w_min
        self.w_max = w_max
        self.A_plus = A_plus
        self.A_minus = A_minus
    
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, AdditiveWeightDependence)):
            return False
        return ((self.w_min == other.w_min)
                and (self.w_max == other.w_max)
                and (self.A_plus == other.A_plus) 
                and (self.A_minus == other.A_minus))

    def get_params_size_bytes(self):
        return (4 * 4)
    
    def get_vertex_executable_suffix(self):
        return "additive"
        
    def write_plastic_params(self, spec, machineTimeStep, weight_scale):
        # In the synaptic row IO, write weights as integers
        spec.write_value(data=int(round(self.w_min * weight_scale)), data_type=DataType.INT32)
        spec.write_value(data=int(round(self.w_max * weight_scale)), data_type=DataType.INT32)

        # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN/standardmodels/synapses.html
        # Pre-multiply A+ and A- by Wmax
        spec.write_value(data=int(round(self.A_plus * self.w_max * weight_scale)), data_type=DataType.INT32)
        spec.write_value(data=int(round(self.A_minus * self.w_max * weight_scale)), data_type=DataType.INT32)
