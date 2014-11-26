from data_specification.enums.data_type import DataType

class MultiplicativeWeightDependence(object):
    
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01):
        self.w_min = w_min
        self.w_max = w_max
        self.A_plus = A_plus
        self.A_minus = A_minus
    
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, MultiplicativeWeightDependence)):
            return False
        return ((self.w_min == other.w_min)
                and (self.w_max == other.w_max)
                and (self.A_plus == other.A_plus) 
                and (self.A_minus == other.A_minus))

    def get_params_size_bytes(self, num_synapse_types, num_terms):
        if num_terms != 1:
            raise NotImplementedError("Multiplicative weight dependence only supports single terms")
        
        return (4 * 4) * num_synapse_types
    
    def write_plastic_params(self, spec, machineTimeStep, weight_scales, num_terms):
        if num_terms != 1:
            raise NotImplementedError("Multiplicative weight dependence only supports single terms")
        
        # Loop through each synapse type's weight scale
        for w in weight_scales:
            spec.write_value(data=int(round(self.w_min * w)), data_type=DataType.INT32)
            spec.write_value(data=int(round(self.w_max * w)), data_type=DataType.INT32)

            spec.write_value(data=int(round(self.A_plus * w)), data_type=DataType.INT32)
            spec.write_value(data=int(round(self.A_minus * w)), data_type=DataType.INT32)
    
    @property
    def vertex_executable_suffix(self):
        return "multiplicative"
