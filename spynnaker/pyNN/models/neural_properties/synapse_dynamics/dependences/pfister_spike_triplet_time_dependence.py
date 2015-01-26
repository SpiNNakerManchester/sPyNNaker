from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_time_dependency import AbstractTimeDependency
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.\
    plastic_weight_synapse_row_io import PlasticWeightSynapseRowIo
from spynnaker.pyNN.models.neural_properties.synapse_dynamics\
    import plasticity_helpers

import logging
logger = logging.getLogger(__name__)

# Constants
# **NOTE** these should be passed through magical per-vertex build setting
# thing
LOOKUP_TAU_PLUS_SIZE = 256
LOOKUP_TAU_PLUS_SHIFT = 0
LOOKUP_TAU_MINUS_SIZE = 256
LOOKUP_TAU_MINUS_SHIFT = 0
LOOKUP_TAU_X_SIZE = 256
LOOKUP_TAU_X_SHIFT = 2
LOOKUP_TAU_Y_SIZE = 256
LOOKUP_TAU_Y_SHIFT = 2


class PfisterSpikeTripletTimeDependence(AbstractTimeDependency):

    # noinspection PyPep8Naming
    def __init__(self, tau_plus, tau_minus, tau_x, tau_y):
        AbstractTimeDependency.__init__(self)

        self._tau_plus = tau_plus
        self._tau_minus = tau_minus
        self._tau_x = tau_x
        self._tau_y = tau_y

    def __eq__(self, other):
        if (other is None) or (
                not isinstance(other, PfisterSpikeTripletTimeDependence)):
            return False
        return ((self._tau_plus == other.tau_plus)
                and (self._tau_minus == other.tau_minus)
                and (self._tau_x == other.tau_x)
                and (self._tau_y == other.tau_y))

    def create_synapse_row_io(
            self, synaptic_row_header_words, dendritic_delay_fraction):
        return PlasticWeightSynapseRowIo(
            synaptic_row_header_words, dendritic_delay_fraction)

    def get_params_size_bytes(self):
        return (2 * (LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE +
                     LOOKUP_TAU_X_SIZE + LOOKUP_TAU_Y_SIZE))

    def is_time_dependance_rule_part(self):
        return True

    def write_plastic_params(self, spec, machine_time_step, weight_scales,
                             global_weight_scale):
        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError("STDP LUT generation currently only "
                                      "supports 1ms timesteps")

        # Write lookup tables
        plasticity_helpers.write_exp_lut(spec, self._tau_plus,
                                         LOOKUP_TAU_PLUS_SIZE,
                                         LOOKUP_TAU_PLUS_SHIFT)
        plasticity_helpers.write_exp_lut(spec, self._tau_minus,
                                         LOOKUP_TAU_MINUS_SIZE,
                                         LOOKUP_TAU_MINUS_SHIFT)
        plasticity_helpers.write_exp_lut(spec, self._tau_x,
                                         LOOKUP_TAU_X_SIZE,
                                         LOOKUP_TAU_X_SHIFT)
        plasticity_helpers.write_exp_lut(spec, self._tau_y,
                                         LOOKUP_TAU_Y_SIZE,
                                         LOOKUP_TAU_Y_SHIFT)

    @property
    def num_terms(self):
        return 2

    @property
    def vertex_executable_suffix(self):
        return "pfister_triplet"

    @property
    def pre_trace_size_bytes(self):
        # Triplet rule trace entries consists of two 16-bit traces - R1 and R2
        return 4

    @property
    def tau_plus(self):
        return self._tau_plus

    @property
    def tau_minus(self):
        return self._tau_minus

    @property
    def tau_x(self):
        return self._tau_x

    @property
    def tau_y(self):
        return self._tau_y
