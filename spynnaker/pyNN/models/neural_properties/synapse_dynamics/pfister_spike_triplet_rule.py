from data_specification.enums.data_type import DataType
from synapse_row_io_plastic_weight import SynapseRowIoPlasticWeight
import plasticity_helpers

import logging
logger = logging.getLogger(__name__)

# Constants
FIXED_POINT_ONE = (1 << 11)

# **NOTE** these should be passed through magical per-vertex build setting thing
TAU_PLUS_LUT_SIZE = 256
TAU_PLUS_LUT_SHIFT = 0
TAU_MINUS_LUT_SIZE = 256
TAU_MINUS_LUT_SHIFT = 0
TAU_X_LUT_SIZE = 256
TAU_X_LUT_SHIFT = 2
TAU_Y_LUT_SIZE = 256
TAU_Y_LUT_SHIFT = 2

# How many pre-synaptic events are buffered
NUM_PRE_SYNAPTIC_EVENTS = 4

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = 4

# How large are the pre_synaptic_trace_entry_t structures
ALL_TO_ALL_EVENT_BYTES = 4

# Calculate number of words required for header
ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS = 1 + ((NUM_PRE_SYNAPTIC_EVENTS * (TIME_STAMP_BYTES + ALL_TO_ALL_EVENT_BYTES)) / 4)

class PfisterSpikeTripletRule(object):
    def __init__(self, tau_plus, tau_minus, tau_x, tau_y):
        self.tau_plus = tau_plus
        self.tau_minus = tau_minus
        self.tau_x = tau_x
        self.tau_y = tau_y
        
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, PfisterSpikeTripletRule)):
            return False
        return ((self.tau_plus == other.tau_plus)
                and (self.tau_minus == other.tau_minus)
                and (self.tau_x == other.tau_x)
                and (self.tau_y == other.tau_y))

    def get_synapse_row_io(self, dendritic_delay_fraction):
        return SynapseRowIoPlasticWeight(ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS, dendritic_delay_fraction)
    
    def get_params_size_bytes(self):
        return (2 * (TAU_PLUS_LUT_SIZE + TAU_MINUS_LUT_SIZE + TAU_X_LUT_SIZE + TAU_Y_LUT_SIZE)) + (4 * 2)

    def get_num_terms(self):
        return 2

    def get_vertex_executable_suffix(self):
        return "pfister_triplet"
        
    def write_plastic_params(self, spec, machineTimeStep, weight_scale):
        # Check timestep is valid
        if machineTimeStep != 1000:
            raise NotImplementedError("STDP LUT generation currently only supports 1ms timesteps")

        # Write lookup tables
        plasticity_helpers.write_exp_lut(spec, self.tau_plus, TAU_PLUS_LUT_SIZE, TAU_PLUS_LUT_SHIFT, FIXED_POINT_ONE)
        plasticity_helpers.write_exp_lut(spec, self.tau_minus, TAU_MINUS_LUT_SIZE, TAU_MINUS_LUT_SHIFT, FIXED_POINT_ONE)
        plasticity_helpers.write_exp_lut(spec, self.tau_x, TAU_X_LUT_SIZE, TAU_X_LUT_SHIFT, FIXED_POINT_ONE)
        plasticity_helpers.write_exp_lut(spec, self.tau_y, TAU_Y_LUT_SIZE, TAU_Y_LUT_SHIFT, FIXED_POINT_ONE)