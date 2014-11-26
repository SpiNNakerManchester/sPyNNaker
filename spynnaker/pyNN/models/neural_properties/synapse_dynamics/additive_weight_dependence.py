from data_specification.enums.data_type import DataType

class AdditiveWeightDependence(object):
    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01, A3_plus=None, A3_minus=None):
        self.w_min = w_min
        self.w_max = w_max
        self.A_plus = A_plus
        self.A_minus = A_minus
        self.A3_plus = A3_plus
        self.A3_minus = A3_minus
    
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, AdditiveWeightDependence)):
            return False
        return ((self.w_min == other.w_min)
                and (self.w_max == other.w_max)
                and (self.A_plus == other.A_plus) 
                and (self.A_minus == other.A_minus)
                and (self.A3_plus == other.A3_plus)
                and (self.A3_minus == other.A3_minus))

    def get_params_size_bytes(self, num_synapse_types, num_terms):
        if num_terms == 1:
            return (4 * 4) * num_synapse_types
        elif num_terms == 2:
            return (6 * 4) * num_synapse_types
        else:
            raise NotImplementedError("Additive weight dependence only supports one or two terms")    
        
    def write_plastic_params(self, spec, machineTimeStep, weight_scales, num_terms):
        # Loop through each synapse type's weight scale
        for w in weight_scales:
            # In the synaptic row IO, write weights as integers
            spec.write_value(data=int(round(self.w_min * w)), data_type=DataType.INT32)
            spec.write_value(data=int(round(self.w_max * w)), data_type=DataType.INT32)

            # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN/standardmodels/synapses.html
            # Pre-multiply A+ and A- by Wmax
            spec.write_value(data=int(round(self.A_plus * self.w_max * w)), data_type=DataType.INT32)
            spec.write_value(data=int(round(self.A_minus * self.w_max * w)), data_type=DataType.INT32)

            # If triplet term is required, write A3+ and A3-, also multiplied by Wmax
            if num_terms == 2:
                spec.write_value(data=int(round(self.A3_plus * self.w_max * w)), data_type=DataType.INT32)
                spec.write_value(data=int(round(self.A3_minus * self.w_max * w)), data_type=DataType.INT32)
            elif num_terms != 1:
                raise NotImplementedError("Additive weight dependence only supports one or two terms")
        
    @property
    def vertex_executable_suffix(self):
        return "additive"