'''
Created on 7 Apr 2014

@author: zzalsar4
'''

NA_TO_PA_SCALE = 1000.0

class AdditiveWeightDependence(object):
    
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

    def get_synaptic_row_header_words(self):
        return 0

    def get_params_size_bytes(self):
        return (4 * 4)

    def write_plastic_params(self, spec, machineTimeStep, subvertex, 
            weight_scale):
        # In the synaptic row IO, write weights as integers
        # **NOTE** these are in 12.4 weight fixed-point format
        spec.write(data=int(round(self.w_min * weight_scale)), sizeof="uint32")
        spec.write(data=int(round(self.w_max * weight_scale)), sizeof="uint32")

        # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN/standardmodels/synapses.html
        # Pre-multiply A+ and A- by Wmax in pA, convert to 21.11 fixed point format and write
        spec.write(data=spec.doubleToS2111(self.A_plus * self.w_max * NA_TO_PA_SCALE), sizeof="s2111")
        spec.write(data=spec.doubleToS2111(self.A_minus * self.w_max * NA_TO_PA_SCALE), sizeof="s2111")
