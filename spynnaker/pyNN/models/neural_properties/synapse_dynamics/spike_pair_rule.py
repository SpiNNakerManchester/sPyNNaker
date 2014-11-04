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

# How large are the pre_trace_t structures
ALL_TO_ALL_PRE_TRACE_BYTES = 2
NEAREST_PAIR_PRE_TRACE_BYTES = 0

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

    def create_synapse_row_io(self, synaptic_row_header_words, dendritic_delay_fraction):
        return SynapseRowIoPlasticWeight(synaptic_row_header_words, dendritic_delay_fraction)
        
    def write_plastic_params(self, spec, machineTimeStep, weight_scale):
        # Check timestep is valid
        if machineTimeStep != 1000:
            raise NotImplementedError("STDP LUT generation currently only supports 1ms timesteps")

        # Write lookup tables
        plasticity_helpers.write_exp_lut(spec, self.tau_plus, 
            TAU_PLUS_LUT_SIZE, TAU_PLUS_LUT_SHIFT, FIXED_POINT_ONE)
        plasticity_helpers.write_exp_lut(spec, self.tau_minus, 
            TAU_MINUS_LUT_SIZE, TAU_MINUS_LUT_SHIFT, FIXED_POINT_ONE)
    
    @property
    def pre_trace_size_bytes(self):
        return (NEAREST_PAIR_PRE_TRACE_BYTES if self.nearest else ALL_TO_ALL_PRE_TRACE_BYTES)
    
    @property
    def params_size_bytes(self):
        return 2 * (TAU_PLUS_LUT_SIZE + TAU_MINUS_LUT_SIZE)

    @property
    def num_terms(self):
        return 1
    
    @property
    def vertex_executable_suffix(self):
        return "nearest_pair" if self.nearest else "pair"