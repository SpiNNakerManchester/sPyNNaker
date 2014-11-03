from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_time_dependency import AbstractTimeDependency
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.\
    weight_based_plastic_synapse_row_io import WeightBasedPlasticSynapseRowIo
from spynnaker.pyNN.models.neural_properties.synapse_dynamics import stdp_helpers

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
ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS = \
    1 + ((NUM_PRE_SYNAPTIC_EVENTS * (TIME_STAMP_BYTES + ALL_TO_ALL_EVENT_BYTES))
         / 4)
NEAREST_PAIR_PLASTIC_REGION_HEADER_WORDS = \
    1 + ((NUM_PRE_SYNAPTIC_EVENTS *
          (TIME_STAMP_BYTES + NEAREST_PAIR_EVENT_BYTES)) / 4)


class SpikePairTimeDependency(AbstractTimeDependency):

    def __init__(self, tau_plus=20.0, tau_minus=20.0, nearest=False):
        AbstractTimeDependency.__init__(self, tau_plus, tau_minus)
        self._nearest = nearest

    @property
    def nearest(self):
        return self._nearest
        
    def __eq__(self, other):
        if (other is None) or (not isinstance(other, SpikePairTimeDependency)):
            return False
        return ((self._tau_plus == other.tau_plus)
                and (self._tau_minus == other.tau_minus)
                and (self._nearest == other.nearest))

    def get_synapse_row_io(self):
        synaptic_row_header_words = \
            NEAREST_PAIR_PLASTIC_REGION_HEADER_WORDS \
            if self.nearest else ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS
        return WeightBasedPlasticSynapseRowIo(synaptic_row_header_words)

    def get_params_size_bytes(self):
        return 2 * (LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE)

    def get_vertex_executable_suffix(self):
        return "nearest_pair" if self.nearest else "pair"

    def is_time_dependance_rule_part(self):
        return True
        
    def write_plastic_params(self, spec, machine_time_step, weight_scale):
        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError("STDP LUT generation currently only "
                                      "supports 1ms timesteps")

        # Write lookup tables
        stdp_helpers.write_exponential_decay_lut(spec, self.tau_plus,
                                                 LOOKUP_TAU_PLUS_SIZE,
                                                 LOOKUP_TAU_PLUS_SHIFT)
        stdp_helpers.write_exponential_decay_lut(spec, self.tau_minus,
                                                 LOOKUP_TAU_MINUS_SIZE,
                                                 LOOKUP_TAU_MINUS_SHIFT)