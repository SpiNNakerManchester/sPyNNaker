from spinn_front_end_common.utilities.utility_objs.provenance_data_item import \
    ProvenanceDataItem

from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import plasticity_helpers
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence\
    .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    .synapse_structure_weight_only import SynapseStructureWeightOnly


import logging
logger = logging.getLogger(__name__)

# TODO. When moving to the c make file adding magic numbers, these should be pushed in there.
LOOKUP_TAU_PLUS_SIZE = 256
LOOKUP_TAU_PLUS_SHIFT = 0
LOOKUP_TAU_MINUS_SIZE = 256
LOOKUP_TAU_MINUS_SHIFT = 0


class TimingDependenceSpikePair(AbstractTimingDependence):

    def __init__(self, tau_plus=20.0, tau_minus=20.0, nearest=False):
        AbstractTimingDependence.__init__(self)
        self._tau_plus = tau_plus
        self._tau_minus = tau_minus
        self._nearest = nearest

        self._synapse_structure = SynapseStructureWeightOnly()

        # provenance data
        self._clipped_tau_plus = None
        self._tau_plus_last_entry = None
        self._clipped_tau_minus = None
        self._tau_minus_last_entry = None

    @property
    def tau_plus(self):
        return self._tau_plus

    @property
    def tau_minus(self):
        return self._tau_minus

    @property
    def nearest(self):
        return self._nearest

    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence, TimingDependenceSpikePair):
            return False
        return (
            (self._tau_plus == timing_dependence._tau_plus) and
            (self._tau_minus == timing_dependence._tau_minus) and
            (self._nearest == timing_dependence._nearest))

    @property
    def vertex_executable_suffix(self):
        return "nearest_pair" if self._nearest else "pair"

    @property
    def pre_trace_n_bytes(self):

        # Pair rule requires no pre-synaptic trace when only the nearest
        # Neighbours are considered and, a single 16-bit R1 trace
        return 0 if self._nearest else 2

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
        self._clipped_tau_plus, self._tau_plus_last_entry = \
            plasticity_helpers.write_exp_lut(
                spec, self._tau_plus, LOOKUP_TAU_PLUS_SIZE,
                LOOKUP_TAU_PLUS_SHIFT)
        self._clipped_tau_minus, self._tau_minus_last_entry = \
            plasticity_helpers.write_exp_lut(
                spec, self._tau_minus, LOOKUP_TAU_MINUS_SIZE,
                LOOKUP_TAU_MINUS_SHIFT)

    @property
    def synaptic_structure(self):
        return self._synapse_structure

    def get_provenance_data(self, pre_population, post_population):
        prov_data = list()
        names = ["Timing_dependence_pfister_spike_triplet between {} and {}"
                 .format(pre_population.label, post_population.label)]
        prov_data.append(ProvenanceDataItem(
            self._add_name(names, "times_tau_plus_clipped"),
            self._clipped_tau_plus,
            report=self._clipped_tau_plus > 0,
            message=(
                "The timing dependence pfister spike triplet between {} and {}"
                " has had its tau_plus parameter below {} clipped to {} a "
                "total of {} times. If this is a issue, try reducing the range"
                " of the tau plus parameters or decreasing the time constant."
                .format(
                    pre_population.label, post_population.label,
                    self._tau_plus_last_entry, self._tau_plus_last_entry,
                    self._clipped_tau_plus))))
        prov_data.append(ProvenanceDataItem(
            self._add_name(names, "times_tau_minus_clipped"),
            self._clipped_tau_minus,
            report=self._clipped_tau_minus > 0,
            message=(
                "The timing dependence pfister spike triplet between {} and {}"
                " has had its tau_minus parameter below {} clipped to {} a "
                "total of {} times. If this is a issue, try reducing the range"
                " of the tau minus parameters or decreasing the time constant."
                .format(
                    pre_population.label, post_population.label,
                    self._tau_minus_last_entry, self._tau_minus_last_entry,
                    self._clipped_tau_minus))))
        return prov_data

    @staticmethod
    def _add_name(names, name):
        new_names = list(names)
        new_names.append(name)
        return new_names