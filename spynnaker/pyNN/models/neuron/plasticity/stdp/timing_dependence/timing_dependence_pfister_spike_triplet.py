import logging
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    plasticity_helpers)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence\
    import (
        AbstractTimingDependence)
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    import (
        SynapseStructureWeightOnly)

logger = logging.getLogger(__name__)

LOOKUP_TAU_PLUS_SIZE = 256
LOOKUP_TAU_PLUS_SHIFT = 0
LOOKUP_TAU_MINUS_SIZE = 256
LOOKUP_TAU_MINUS_SHIFT = 0
LOOKUP_TAU_X_SIZE = 256
LOOKUP_TAU_X_SHIFT = 2
LOOKUP_TAU_Y_SIZE = 256
LOOKUP_TAU_Y_SHIFT = 2


class TimingDependencePfisterSpikeTriplet(AbstractTimingDependence):
    __slots__ = [
        "__synapse_structure",
        "__tau_minus",
        "__tau_minus_last_entry",
        "__tau_plus",
        "__tau_plus_last_entry",
        "__tau_x",
        "__tau_x_last_entry",
        "__tau_y",
        "__tau_y_last_entry"]

    # noinspection PyPep8Naming
    def __init__(self, tau_plus, tau_minus, tau_x, tau_y):
        self.__tau_plus = tau_plus
        self.__tau_minus = tau_minus
        self.__tau_x = tau_x
        self.__tau_y = tau_y

        self.__synapse_structure = SynapseStructureWeightOnly()

        # provenance data
        self.__tau_plus_last_entry = None
        self.__tau_minus_last_entry = None
        self.__tau_x_last_entry = None
        self.__tau_y_last_entry = None

    @property
    def tau_plus(self):
        return self.__tau_plus

    @property
    def tau_minus(self):
        return self.__tau_minus

    @property
    def tau_x(self):
        return self.__tau_x

    @property
    def tau_y(self):
        return self.__tau_y

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if not isinstance(
                timing_dependence, TimingDependencePfisterSpikeTriplet):
            return False
        return (
            (self.__tau_plus == timing_dependence.tau_plus) and
            (self.__tau_minus == timing_dependence.tau_minus) and
            (self.__tau_x == timing_dependence.tau_x) and
            (self.__tau_y == timing_dependence.tau_y))

    @property
    def vertex_executable_suffix(self):
        return "pfister_triplet"

    @property
    def pre_trace_n_bytes(self):

        # Triplet rule trace entries consists of two 16-bit traces - R1 and R2
        return 4

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return (2 * (LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE +
                     LOOKUP_TAU_X_SIZE + LOOKUP_TAU_Y_SIZE))

    @property
    def n_weight_terms(self):
        return 2

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError(
                "STDP LUT generation currently only supports 1ms timesteps")

        # Write lookup tables
        self.__tau_plus_last_entry = plasticity_helpers.write_exp_lut(
            spec, self.__tau_plus, LOOKUP_TAU_PLUS_SIZE,
            LOOKUP_TAU_PLUS_SHIFT)
        self.__tau_minus_last_entry = plasticity_helpers.write_exp_lut(
            spec, self.__tau_minus, LOOKUP_TAU_MINUS_SIZE,
            LOOKUP_TAU_MINUS_SHIFT)
        self.__tau_x_last_entry = plasticity_helpers.write_exp_lut(
            spec, self.__tau_x, LOOKUP_TAU_X_SIZE, LOOKUP_TAU_X_SHIFT)
        self.__tau_y_last_entry = plasticity_helpers.write_exp_lut(
            spec, self.__tau_y, LOOKUP_TAU_Y_SIZE, LOOKUP_TAU_Y_SHIFT)

    @property
    def synaptic_structure(self):
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_provenance_data)
    def get_provenance_data(self, pre_population_label, post_population_label):
        prov_data = list()
        prov_data.append(plasticity_helpers.get_lut_provenance(
            pre_population_label, post_population_label,
            "PfisterSpikeTripletRule", "tau_plus_last_entry",
            "tau_plus", self.__tau_plus_last_entry))
        prov_data.append(plasticity_helpers.get_lut_provenance(
            pre_population_label, post_population_label,
            "PfisterSpikeTripletRule", "tau_minus_last_entry",
            "tau_minus", self.__tau_minus_last_entry))
        prov_data.append(plasticity_helpers.get_lut_provenance(
            pre_population_label, post_population_label,
            "PfisterSpikeTripletRule", "tau_x_last_entry",
            "tau_x", self.__tau_x_last_entry))
        prov_data.append(plasticity_helpers.get_lut_provenance(
            pre_population_label, post_population_label,
            "PfisterSpikeTripletRule", "tau_y_last_entry",
            "tau_y", self.__tau_y_last_entry))
        return prov_data

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['tau_plus', 'tau_minus', 'tau_x', 'tau_y']
