'''
Created on 7 Apr 2014

@author: zzalsar4
'''
import math

import logging
logger = logging.getLogger(__name__)

# Constants
# **NOTE** these should be passed through magical per-vertex build setting thing
LOOKUP_TAU_PLUS_SIZE = 256
LOOKUP_TAU_PLUS_SHIFT = 0
LOOKUP_TAU_MINUS_SIZE = 256
LOOKUP_TAU_MINUS_SHIFT = 0

# How many pre-synaptic events are buffered
NUM_PRE_SYNAPTIC_EVENTS = 4

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = 4

# How large are the pre_synaptic_trace_entry_t structures
ALL_TO_ALL_EVENT_BYTES = 2
NEAREST_PAIR_EVENT_BYTES = 0

# Calculate number of words required for header
ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS = 1 + ((NUM_PRE_SYNAPTIC_EVENTS * (TIME_STAMP_BYTES + ALL_TO_ALL_EVENT_BYTES)) / 4)
NEAREST_PAIR_PLASTIC_REGION_HEADER_WORDS = 1 + ((NUM_PRE_SYNAPTIC_EVENTS * (TIME_STAMP_BYTES + NEAREST_PAIR_EVENT_BYTES)) / 4)

class SpikePairRule(object):
    
    def __init__(self, tau_plus = 20.0, tau_minus = 20.0, nearest = False):
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
        return NEAREST_PAIR_PLASTIC_REGION_HEADER_WORDS if self.nearest else ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS
    
    def get_params_size_bytes(self):
        return 2 * (LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE)

    def get_vertex_executable_suffix(self):
        return "nearest_pair" if self.nearest else "pair"
        
    def write_plastic_params(self, spec, machineTimeStep, subvertex, 
            weight_scale):
        # Check timestep is valid
        if machineTimeStep != 1000:
            raise NotImplementedError("STDP LUT generation currently only supports 1ms timesteps")

        # Write lookup tables
        self.__write_exponential_decay_lut(spec, self.tau_plus, LOOKUP_TAU_PLUS_SIZE, LOOKUP_TAU_PLUS_SHIFT)
        self.__write_exponential_decay_lut(spec, self.tau_minus, LOOKUP_TAU_MINUS_SIZE, LOOKUP_TAU_MINUS_SHIFT)
    
    # Move somewhere more generic STDPRuleBase perhaps?
    def __write_exponential_decay_lut(self, spec, timeConstant, size, shift):
        # Calculate time constant reciprocal
        timeConstantReciprocal = 1.0 / float(timeConstant)

        # Check that the last 
        lastTime = (size - 1) << shift
        lastValue = float(lastTime) * timeConstantReciprocal
        lastExponentialFloat = math.exp(-lastValue)
        if spec.doubleToS511(lastExponentialFloat) != 0:
            logger.warning("STDP lookup table with size %u is too short to contain decay with time constant %u - last entry is %f" % (size, timeConstant, lastExponentialFloat))

        # Generate LUT
        for i in range(size):
            # Apply shift to get time from index 
            time = (i << shift)

            # Multiply by time constant and calculate negative exponential
            value = float(time) * timeConstantReciprocal
            exponentialFloat = math.exp(-value);

            # Convert to fixed-point and write to spec
            spec.write(data=spec.doubleToS511(exponentialFloat), sizeof="s511")
            