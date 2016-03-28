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
LOOKUP_TAU_X_SIZE = 256
LOOKUP_TAU_X_SHIFT = 2
LOOKUP_TAU_Y_SIZE = 256
LOOKUP_TAU_Y_SHIFT = 2


class TimingDependencePfisterSpikeTriplet(AbstractTimingDependence):

    # noinspection PyPep8Naming
    def __init__(self, tau_plus, tau_minus, tau_x, tau_y):
        AbstractTimingDependence.__init__(self)

        self._tau_plus = tau_plus
        self._tau_minus = tau_minus
        self._tau_x = tau_x
        self._tau_y = tau_y

        self._synapse_structure = SynapseStructureWeightOnly()

        # provenance data
        self._clipped_tau_plus = None
        self._tau_plus_last_entry = None
        self._clipped_tau_minus = None
        self._tau_minus_last_entry = None
        self._clipped_tau_x = None
        self._tau_x_last_entry = None
        self._clipped_tau_y = None
        self._tau_y_last_entry = None

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

    def is_same_as(self, timing_dependence):
        if not isinstance(
                timing_dependence, TimingDependencePfisterSpikeTriplet):
            return False
        return (
            (self._tau_plus == timing_dependence.tau_plus) and
            (self._tau_minus == timing_dependence.tau_minus) and
            (self._tau_x == timing_dependence.tau_x) and
            (self._tau_y == timing_dependence.tau_y))

    @property
    def vertex_executable_suffix(self):
        return "pfister_triplet"

    @property
    def pre_trace_n_bytes(self):

        # Triplet rule trace entries consists of two 16-bit traces - R1 and R2
        return 4

    def get_parameters_sdram_usage_in_bytes(self):
        return (2 * (LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE +
                     LOOKUP_TAU_X_SIZE + LOOKUP_TAU_Y_SIZE))

    @property
    def n_weight_terms(self):
        return 2

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
        self._clipped_tau_x, self._tau_x_last_entry = \
            plasticity_helpers.write_exp_lut(
                spec, self._tau_x, LOOKUP_TAU_X_SIZE, LOOKUP_TAU_X_SHIFT)
        self._clipped_tau_y, self._tau_y_last_entry = \
            plasticity_helpers.write_exp_lut(
                spec, self._tau_y, LOOKUP_TAU_Y_SIZE, LOOKUP_TAU_Y_SHIFT)

    @property
    def synaptic_structure(self):
        return self._synapse_structure

    def generate_provenance_data(self, pre_population, post_population):
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
        prov_data.append(ProvenanceDataItem(
            self._add_name(names, "times_tau_x_clipped"),
            self._clipped_tau_x,
            report=self._clipped_tau_x > 0,
            message=(
                "The timing dependence pfister spike triplet between {} and {}"
                " has had its tau_x parameter below {} clipped to {} a "
                "total of {} times. If this is a issue, try reducing the range"
                " of the tau x parameters or decreasing the time constant."
                .format(
                    pre_population.label, post_population.label,
                    self._tau_x_last_entry, self._tau_x_last_entry,
                    self._clipped_tau_x))))
        prov_data.append(ProvenanceDataItem(
            self._add_name(names, "times_tau_y_clipped"),
            self._clipped_tau_y,
            report=self._clipped_tau_y > 0,
            message=(
                "The timing dependence pfister spike triplet between {} and {}"
                " has had its tau_y parameter below {} clipped to {} a "
                "total of {} times. If this is a issue, try reducing the range"
                " of the tau y parameters or decreasing the time constant."
                .format(
                    pre_population.label, post_population.label,
                    self._tau_y_last_entry, self._tau_y_last_entry,
                    self._clipped_tau_y))))
        return prov_data

    @staticmethod
    def _add_name(names, name):
        new_names = list(names)
        new_names.append(name)
        return new_names
