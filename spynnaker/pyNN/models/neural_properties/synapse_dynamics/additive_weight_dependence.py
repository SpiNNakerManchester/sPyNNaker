from spynnaker.pyNN.utilities import constants
from data_specification.enums.data_type import DataType
from spynnaker.pyNN import exceptions

class AdditiveWeightDependence(object):

    # noinspection PyPep8Naming
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01):
        self.w_min = w_min
        self.w_max = w_max
        self.a_plus = A_plus
        self.a_minus = A_minus
    
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
                         data_type=DataType.UINT32)
        spec.write_value(data=int(round(self.w_max * weight_scale)),
                         data_type=DataType.UINT32)

        # Based on
        # http://data.andrewdavison.info/docs/PyNN/_modules/pyNN/
        # standardmodels/synapses.html
        # Pre-multiply A+ and A- by Wmax in pA, convert to 21.11 fixed point
        # format and write
        spec.write_value(data=self._double_to_s2111(self.a_plus * self.w_max *
                                                    constants.NA_TO_PA_SCALE),
                         data_type=DataType.UINT32)
        spec.write_value(data=self._double_to_s2111(self.a_minus * self.w_max *
                                                    constants.NA_TO_PA_SCALE),
                         data_type=DataType.UINT32)

    @staticmethod
    def _double_to_s2111(my_double):
        """
        Reformat a double into a 32-bit unsigned integer representing u2111 format
        (i.e. unsigned 21.11 - 32-bit extension of 5.11 used for STDP).
        Raise an exception if the value cannot be represented in this way.
        """
        if (my_double < -2097152.0) or (my_double >= 2097152.0):
            raise exceptions.ConfigurationException(
                "the double value cannot be recast as a u2111. Exiting.")

        # Shift up by 11 bits:
        scaled_my_double = float(my_double) * 2048.0

        # Round to an integer:
        # **THINK** should we actually round here?
        my_s2111 = int(scaled_my_double)
        return my_s2111
