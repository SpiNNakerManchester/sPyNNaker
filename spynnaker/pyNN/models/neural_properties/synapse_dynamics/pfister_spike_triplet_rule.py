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

# How large are the pre_trace_t structures
ALL_TO_ALL_PRE_TRACE_BYTES = 4

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

    
    def create_synapse_row_io(self, synaptic_row_header_words, dendritic_delay_fraction):
        return SynapseRowIoPlasticWeight(synaptic_row_header_words, dendritic_delay_fraction)
        
    def write_plastic_params(self, spec, machineTimeStep, weight_scales):
        # Check timestep is valid
        if machineTimeStep != 1000:
            raise NotImplementedError("STDP LUT generation currently only supports 1ms timesteps")

        # Write lookup tables
        plasticity_helpers.write_exp_lut(spec, self.tau_plus, TAU_PLUS_LUT_SIZE, TAU_PLUS_LUT_SHIFT, FIXED_POINT_ONE)
        plasticity_helpers.write_exp_lut(spec, self.tau_minus, TAU_MINUS_LUT_SIZE, TAU_MINUS_LUT_SHIFT, FIXED_POINT_ONE)
        plasticity_helpers.write_exp_lut(spec, self.tau_x, TAU_X_LUT_SIZE, TAU_X_LUT_SHIFT, FIXED_POINT_ONE)
        plasticity_helpers.write_exp_lut(spec, self.tau_y, TAU_Y_LUT_SIZE, TAU_Y_LUT_SHIFT, FIXED_POINT_ONE)
    
    @property
    def pre_trace_size_bytes(self):
        return ALL_TO_ALL_PRE_TRACE_BYTES
    
    @property
    def params_size_bytes(self):
        return (2 * (TAU_PLUS_LUT_SIZE + TAU_MINUS_LUT_SIZE + TAU_X_LUT_SIZE + TAU_Y_LUT_SIZE)) + (4 * 2)
    
    @property
    def num_terms(self):
        return 2
    
    @property
    def vertex_executable_suffix(self):
        return "pfister_triplet"