
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import plasticity_helpers
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    import SynapseStructureWeightOnly


import logging
logger = logging.getLogger(__name__)

LOOKUP_TAU_PLUS_SIZE = 256
LOOKUP_TAU_PLUS_SHIFT = 0
LOOKUP_TAU_MINUS_SIZE = 256
LOOKUP_TAU_MINUS_SHIFT = 0


class TimingDependenceSpikePair(AbstractTimingDependence):

    def __init__(self, tau_plus=20.0, tau_minus=20.0, tau_c=1000, tau_d=200,
                 nearest=False):
        AbstractTimingDependence.__init__(self)
        self._tau_plus = tau_plus
        self._tau_minus = tau_minus
        self._tau_c = tau_c
        self._taU_d = tau_d
        self._nearest = nearest

        self._synapse_structure = SynapseStructureWeightOnly()

        # provenance data
        self._tau_plus_last_entry = None
        self._tau_minus_last_entry = None

    @property
    def tau_plus(self):
        return self._tau_plus

    @property
    def tau_minus(self):
        return self._tau_minus

    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence, TimingDependenceSpikePair):
            return False
        return ((self.tau_plus == timing_dependence.tau_plus) and
                (self.tau_minus == timing_dependence.tau_minus))

    @property
    def vertex_executable_suffix(self):
        return "pair"

    @property
    def pre_trace_n_bytes(self):

        # Pair rule requires no pre-synaptic trace when only the nearest
        # Neighbours are considered and, a single 16-bit R1 trace
        return 2

    def get_parameters_sdram_usage_in_bytes(self):
        return 2 * (LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE)

    @property
    def n_weight_terms(self):
        return 1

    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError(
                "STDP LUT generation currently only supports 1ms timesteps")

        # Write lookup tables
        self._tau_plus_last_entry = plasticity_helpers.write_exp_lut(
            spec, self._tau_plus, LOOKUP_TAU_PLUS_SIZE,
            LOOKUP_TAU_PLUS_SHIFT)
        self._tau_minus_last_entry = plasticity_helpers.write_exp_lut(
            spec, self._tau_minus, LOOKUP_TAU_MINUS_SIZE,
            LOOKUP_TAU_MINUS_SHIFT)

        self._tau_c_last_entry = plasticity_helpers.write_exp_lut(
            spec, self._tau_c, LOOKUP_TAU_PLUS_SIZE,
            LOOKUP_TAU_PLUS_SHIFT)
        self._tau_c_last_entry = plasticity_helpers.write_exp_lut(
            spec, self._tau_d, LOOKUP_TAU_PLUS_SIZE,
            LOOKUP_TAU_PLUS_SHIFT)

    @property
    def synaptic_structure(self):
        return self._synapse_structure

    def get_provenance_data(self, pre_population_label, post_population_label):
        prov_data = list()
        prov_data.append(plasticity_helpers.get_lut_provenance(
            pre_population_label, post_population_label, "SpikePairRule",
            "tau_plus_last_entry", "tau_plus", self._tau_plus_last_entry))
        prov_data.append(plasticity_helpers.get_lut_provenance(
            pre_population_label, post_population_label, "SpikePairRule",
            "tau_minus_last_entry", "tau_minus", self._tau_minus_last_entry))
        return prov_data
