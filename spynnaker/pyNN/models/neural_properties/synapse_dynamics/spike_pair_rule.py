import math
import logging

logger = logging.getLogger(__name__)

# How many pre-synaptic events are buffered
_NUM_PRE_SYNAPTIC_EVENTS = 4
# How large are the time-stamps stored with each event
_TIME_STAMP_BYTES = 4
# How large are the pre_synaptic_trace_entry_t structures
_ALL_TO_ALL_EVENT_BYTES = 2
_NEAREST_PAIR_EVENT_BYTES = 0


class SpikePairRule(object):

    _NEAREST_PAIR_PLASTIC_REGION_HEADER_WORDS = \
        1 + ((_NUM_PRE_SYNAPTIC_EVENTS *
            (_TIME_STAMP_BYTES + _NEAREST_PAIR_EVENT_BYTES)) / 4)

    _ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS = \
        1 + ((_NUM_PRE_SYNAPTIC_EVENTS *
            (_TIME_STAMP_BYTES + _ALL_TO_ALL_EVENT_BYTES)) / 4)

    _LOOKUP_TAU_PLUS_SIZE = 256
    _LOOKUP_TAU_PLUS_SHIFT = 0
    _LOOKUP_TAU_MINUS_SIZE = 256
    _LOOKUP_TAU_MINUS_SHIFT = 0
    
    def __init__(self, tau_plus=20.0, tau_minus=20.0, nearest=False):
        self.tau_plus = tau_plus
        self.tau_minus = tau_minus
        self.nearest = nearest
        
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, SpikePairRule)):
            return False
        return ((self.tau_plus == other.tau_plus) 
                and (self.tau_minus == other.tau_minus)
                and (self.nearest == other.nearest))

    def get_synaptic_row_header_words(self):
        return self._NEAREST_PAIR_PLASTIC_REGION_HEADER_WORDS \
            if self.nearest else \
            self._ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS

    def get_params_size_bytes(self):
        return 2 * (self._LOOKUP_TAU_PLUS_SIZE +
                    self._LOOKUP_TAU_MINUS_SIZE)

    def get_vertex_executable_suffix(self):
        return "nearest_pair" if self.nearest else "pair"
        
    def write_plastic_params(self, spec, machine_time_step):
        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError("STDP LUT generation currently "
                                      "only supports 1ms timesteps")

        # Write lookup tables
        self.__write_exponential_decay_lut(spec, self.tau_plus,
                                           self._LOOKUP_TAU_PLUS_SIZE,
                                           self._LOOKUP_TAU_PLUS_SHIFT)
        self.__write_exponential_decay_lut(spec, self.tau_minus,
                                           self._LOOKUP_TAU_MINUS_SIZE,
                                           self._LOOKUP_TAU_MINUS_SHIFT)
    
    # Move somewhere more generic STDPRuleBase perhaps?
    @staticmethod
    def __write_exponential_decay_lut(spec, time_constant, size, shift):
        # Calculate time constant reciprocal
        time_constant_reciprocal = 1.0 / float(time_constant)

        # Check that the last 
        last_time = (size - 1) << shift
        last_value = float(last_time) * time_constant_reciprocal
        last_exponential_float = math.exp(-last_value)
        if spec.doubleToS511(last_exponential_float) != 0:
            logger.warning("STDP lookup table with size %u is too short to "
                           "contain decay with time constant %u - last entry "
                           "is %f" % (size, time_constant,
                                      last_exponential_float))

        # Generate LUT
        for i in range(size):
            # Apply shift to get time from index 
            time = (i << shift)

            # Multiply by time constant and calculate negative exponential
            value = float(time) * time_constant_reciprocal
            exponential_float = math.exp(-value)

            # Convert to fixed-point and write to spec
            spec.write(data=spec.doubleToS511(exponential_float), sizeof="s511")