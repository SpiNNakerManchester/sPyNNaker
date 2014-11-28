from data_specification.enums.data_type import DataType
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
LOOKUP_TAU_X_SIZE = 256
LOOKUP_TAU_X_SHIFT = 2
LOOKUP_TAU_Y_SIZE = 256
LOOKUP_TAU_Y_SHIFT = 2

# How many pre-synaptic events are buffered
NUM_PRE_SYNAPTIC_EVENTS = 4

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = 4

# How large are the pre_synaptic_trace_entry_t structures
ALL_TO_ALL_EVENT_BYTES = 4

# Calculate number of words required for header
ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS = \
    1 + ((NUM_PRE_SYNAPTIC_EVENTS * (TIME_STAMP_BYTES + ALL_TO_ALL_EVENT_BYTES))
         / 4)


class PfisterSpikeTripletTimeDependence(AbstractTimeDependency):

    # noinspection PyPep8Naming
    def __init__(self, A3_plus, A3_minus, tau_plus, tau_minus, tau_x, tau_y,
                 w_max):
        AbstractTimeDependency.__init__(self, tau_plus, tau_minus)
        self._A3_plus = A3_plus
        self._A3_minus = A3_minus
        self._tau_x = tau_x
        self._tau_y = tau_y
        self._w_max = w_max  # HACK
        
    def __eq__(self, other):
        if (other is None) or (
                not isinstance(other, PfisterSpikeTripletTimeDependence)):
            return False
        return ((self._tau_plus == other.tau_plus)
                and (self._A3_plus == other.A3_plus)
                and (self._A3_minus == other.A3_minus)
                and (self._tau_minus == other.tau_minus)
                and (self._tau_x == other.tau_x)
                and (self._tau_y == other.tau_y))

    # noinspection PyPep8Naming
    @property
    def A3_plus(self):
        return self._A3_plus

    # noinspection PyPep8Naming
    @property
    def A3_minus(self):
        return self._A3_minus

    @property
    def tau_x(self):
        return self._tau_x

    @property
    def tau_y(self):
        return self._tau_y

    def get_synapse_row_io(self):
        return WeightBasedPlasticSynapseRowIo(
            ALL_TO_ALL_PLASTIC_REGION_HEADER_WORDS)

    def get_params_size_bytes(self):
        return (2 * (LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE +
                     LOOKUP_TAU_X_SIZE + LOOKUP_TAU_Y_SIZE)) + (4 * 2)

    def get_vertex_executable_suffix(self):
        return "pfister_triplet"

    def is_time_dependance_rule_part(self):
        return True
        
    def write_plastic_params(self, spec, machine_time_step, weight_scale):
        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError("STDP LUT generation currently only "
                                      "supports 1ms timesteps")
       
        # Write parameters 
        spec.write_value(data=int(
                         round(self._A3_plus * self._w_max * weight_scale)),
                         data_type=DataType.INT32)
        spec.write_value(data=int(
                         round(self._A3_minus * self._w_max * weight_scale)),
                         data_type=DataType.INT32)
        
        # Write lookup tables
        stdp_helpers.write_exponential_decay_lut(spec, self._tau_plus,
                                                 LOOKUP_TAU_PLUS_SIZE,
                                                 LOOKUP_TAU_PLUS_SHIFT)
        stdp_helpers.write_exponential_decay_lut(spec, self._tau_minus,
                                                 LOOKUP_TAU_MINUS_SIZE,
                                                 LOOKUP_TAU_MINUS_SHIFT)
        stdp_helpers.write_exponential_decay_lut(spec, self._tau_x,
                                                 LOOKUP_TAU_X_SIZE,
                                                 LOOKUP_TAU_X_SHIFT)
        stdp_helpers.write_exponential_decay_lut(spec, self._tau_y,
                                                 LOOKUP_TAU_Y_SIZE,
                                                 LOOKUP_TAU_Y_SHIFT)