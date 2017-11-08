from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
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


class TimingDependencePreOnly(AbstractTimingDependence):

    def __init__(self, A_plus=0.01, A_minus=0.01, th_v_mem = -55.0, th_ca_up_l=0.0, th_ca_up_h=10.0, th_ca_dn_l=0.0, th_ca_dn_h=5.0 ):
        AbstractTimingDependence.__init__(self)
        self._A_plus = A_plus
        self._A_minus = A_minus
        self._th_v_mem = th_v_mem

        self._th_ca_up_l = th_ca_up_l
        self._th_ca_up_h = th_ca_up_h
        self._th_ca_dn_l = th_ca_dn_l
        self._th_ca_dn_h = th_ca_dn_h

        self._synapse_structure = SynapseStructureWeightOnly()

        # provenance data
        #self._tau_plus_last_entry = None # what's this for?
        #self._tau_minus_last_entry = None

    @property
    def A_plus(self):
        return self._A_plus

    @property
    def A_minus(self):
        return self._A_minus

    @property
    def th_v_mem(self):
        return self._th_v_mem

    @property
    def th_ca_up_l(self):
        return self._th_ca_up_l

    @property
    def th_ca_up_h(self):
        return self._th_ca_up_h

    @property
    def th_ca_dn_l(self):
        return self._th_ca_dn_l

    @property
    def th_ca_dn_h(self):
        return self._th_ca_dn_h

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence, TimingDependencePreOnly):
            return False
        return ((self.A_plus == timing_dependence.A_plus) and
                (self.A_minus == timing_dependence.A_minus))

    @property
    def vertex_executable_suffix(self):
        return "pre_only"

    @property
    def pre_trace_n_bytes(self):

        # Pair rule requires no pre-synaptic trace when only the nearest
        # Neighbours are considered and, a single 16-bit R1 trace
        return 2

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
#         return ( 4 + 4 + 4 )
        return ( 4 * 5 )
    @property
    def n_weight_terms(self):
        return 1

    def write_parameters(self, spec, machine_time_step, weight_scales):

#         spec.write_value(
#             data=int(round(self.A_plus)),
#             data_type=DataType.INT32)
#         spec.write_value(
#             data=int(round(self.A_minus)),
#             data_type=DataType.INT32)

        # write thresholds
        spec.write_value(
            data=self.th_v_mem,
            data_type=DataType.S1615)

        spec.write_value(
            data=self.th_ca_up_l,
            data_type=DataType.S1615)

        spec.write_value(
            data=self.th_ca_up_h,
            data_type=DataType.S1615)

        spec.write_value(
            data=self.th_ca_dn_l,
            data_type=DataType.S1615)

        spec.write_value(
            data=self.th_ca_dn_h,
            data_type=DataType.S1615)


    @property
    def synaptic_structure(self):
        return self._synapse_structure

    def get_provenance_data(self, pre_population_label, post_population_label):
        prov_data = list()
#         prov_data.append(plasticity_helpers.get_lut_provenance(
#             pre_population_label, post_population_label, "SpikePairRule",
#             "tau_plus_last_entry", "tau_plus", self._tau_plus_last_entry))
#         prov_data.append(plasticity_helpers.get_lut_provenance(
#             pre_population_label, post_population_label, "SpikePairRule",
#             "tau_minus_last_entry", "tau_minus", self._tau_minus_last_entry))
        return prov_data

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['A_plus', 'A_minus', 'th_v_mem', 'th_ca_up_l', 'th_ca_up_h', 'th_ca_dn_l', 'th_ca_dn_h']
