from spynnaker.pyNN.utilities import constants


class AdditiveWeightDependence(object):
    
    def __init__(self, w_min=0.0, w_max=1.0, a_plus=0.01, a_minus=0.01):
        self.w_min = w_min
        self.w_max = w_max
        self.a_plus = a_plus
        self.a_minus = a_minus
    
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, AdditiveWeightDependence)):
            return False
        return ((self.w_min == other.w_min)
                and (self.w_max == other.w_max)
                and (self.a_plus == other.a_plus)
                and (self.a_minus == other.a_minus))

    @staticmethod
    def get_synaptic_row_header_words():
        return 0

    @staticmethod
    def get_params_size_bytes():
        return 4 * 4

    def write_plastic_params(self, spec, weight_scale):
        # In the synaptic row IO, write weights as integers
        # **NOTE** these are in 12.4 weight fixed-point format
        spec.write_value(data=int(round(self.w_min * weight_scale)),
                         sizeof="uint32")
        spec.write_value(data=int(round(self.w_max * weight_scale)),
                         sizeof="uint32")

        # Based on
        # http://data.andrewdavison.info/docs/PyNN/_modules/pyNN/
        # standardmodels/synapses.html
        # Pre-multiply A+ and A- by Wmax in pA, convert to 21.11 fixed point
        # format and write
        spec.write_value(data=spec.doubleToS2111(self.a_plus * self.w_max *
                                                 constants.NA_TO_PA_SCALE),
                         sizeof="s2111")
        spec.write_value(data=spec.doubleToS2111(self.a_minus * self.w_max *
                                                 constants.NA_TO_PA_SCALE),
                         sizeof="s2111")
