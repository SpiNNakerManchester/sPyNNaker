from spynnaker.pyNN.utilities import constants
from data_specification.enums.data_type import DataType
from spynnaker.pyNN import exceptions

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
        
    def write_plastic_params(self, spec, machineTimeStep, subvertex, 
            weight_scale):
        # In the synaptic row IO, write weights as integers
        # **NOTE** these are in the runtime-defined weight fixed-point format
        spec.write(data=int(round(self.w_min * weight_scale)), sizeof="uint32")
        spec.write(data=int(round(self.w_max * weight_scale)), sizeof="uint32")

        # Calculate scaling factor to incorporate the conversion to weight scale into additive constants
        # **TODO** move me, along with a load of other stuff to magical stdp helper place
        stdp_to_weight_scale = float(weight_scale) / 2048.0
        
        # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN/standardmodels/synapses.html
        # Pre-multiply A+ and A- by Wmax, convert to 21.11 fixed point format and write
        a_plus = spec.doubleToS2111(self.A_plus * self.w_max * stdp_to_weight_scale)
        a_minus = spec.doubleToS2111(self.A_minus * self.w_max * stdp_to_weight_scale)
        print("A+ %d A- %d" % (a_plus, a_minus))
        spec.write(data=spec.doubleToS2111(self.A_plus * self.w_max * stdp_to_weight_scale), sizeof="s2111")
        spec.write(data=spec.doubleToS2111(self.A_minus * self.w_max * stdp_to_weight_scale), sizeof="s2111")
