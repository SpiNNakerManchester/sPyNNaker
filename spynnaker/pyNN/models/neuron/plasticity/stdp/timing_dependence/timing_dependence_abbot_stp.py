from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.plasticity.stdp.common.plasticity_helpers import STDP_FIXED_POINT_ONE
from __builtin__ import property
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import plasticity_helpers
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    import SynapseStructureWeightOnly
from data_specification.enums import DataType

import numpy
import logging
logger = logging.getLogger(__name__)

# LOOKUP_TAU_PLUS_SIZE = 256
# LOOKUP_TAU_PLUS_SHIFT = 0
# LOOKUP_TAU_MINUS_SIZE = 256
# LOOKUP_TAU_MINUS_SHIFT = 0
LOOKUP_TAU_P_SIZE = 4000
LOOKUP_TAU_P_SHIFT = 0


class TimingDependenceAbbotSTP(AbstractTimingDependence):

    _tau_P_depress = 1
    _tau_P_facil = 1

    def __init__(self, STP_type, f, P_baseline, tau_P,
                # unused parameters, but required due to using
                # existing STDP framework
                tau_plus=20.0, tau_minus=20.0):
        AbstractTimingDependence.__init__(self)
        self._tau_plus = tau_plus
        self._tau_minus = tau_minus

        if (STP_type is 0 or STP_type is 1):
            self._STP_type = STP_type
        else:
            print "Invalid STP type. Should be: 0 for depression," \
                "or 1 for potentiation"

        self._f = f
        self._P_baseline = P_baseline

        if STP_type is 0:
            TimingDependenceAbbotSTP._tau_P_depress = tau_P
        else:
            TimingDependenceAbbotSTP._tau_P_facil = tau_P

        self._synapse_structure = SynapseStructureWeightOnly()

        # For Provenance Data
        self._tau_P_depression_last_entry = None
        self._tau_P_facilitation_last_entry = None
        # Check transition back to baseline, and
        # what's resolvable precision-wise

    @property
    def STP_type(self):
        return self._STP_type

    @property
    def f(self):
        return self._f

    @property
    def P_baseline(self):
        return self._P_baseline

    @property
    def tau_P(self):
        return self._tau_P

    @property
    def tau_plus(self):
        return self._tau_plus

    @property
    def tau_minus(self):
        return self._tau_minus

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence, TimingDependenceAbbotSTP):
            return False
        return ((self.tau_plus == timing_dependence.tau_plus) and
                (self.tau_minus == timing_dependence.tau_minus))

    @property
    def vertex_executable_suffix(self):
        return "abbot_stp"

    @property
    def pre_trace_n_bytes(self):
        # Organised as array of 32-bit datastructures
        # [0] = [16 bit STDP pre_trace, 16-bit STP P_baseline]
        # [1] = [16-bit STP_trace, 16-bit STP type]
        # [2] = [16-bit stp_rate, 16-bit empty]

        # note that a third entry will be added by synapse_dynamics_stdp_mad
        # [2] = [32-bit time stamp]

        # here we need only account for the first three entries = 6 * 16-bits
        return 12

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        size = 0
        # two bytes per lookup table entry,
        size += (2 * LOOKUP_TAU_P_SIZE) # depression
        size += (2 * LOOKUP_TAU_P_SIZE) # facilitation

        # size += 2 * 4 # 1 parameters at 4 bytes
        return size

    @property
    def n_weight_terms(self):
        return 1

    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError(
                "STP LUT generation currently only supports 1ms timesteps")

        # Write STP depression lookup table
        self._tau_P_depression_last_entry = plasticity_helpers.write_exp_lut(
            spec, TimingDependenceAbbotSTP._tau_P_depress, LOOKUP_TAU_P_SIZE,
            LOOKUP_TAU_P_SHIFT)

        # Write STP depression lookup table
        self._tau_P_facilitation_last_entry = plasticity_helpers.write_exp_lut(
            spec, TimingDependenceAbbotSTP._tau_P_facil, LOOKUP_TAU_P_SIZE,
            LOOKUP_TAU_P_SHIFT)


    @property
    def synaptic_structure(self):
        return self._synapse_structure

    def get_provenance_data(self, pre_population_label, post_population_label):
        prov_data = list()
        prov_data.append(plasticity_helpers.get_lut_provenance(
            pre_population_label, post_population_label, "STP_Abbot_Rule",
            "tau_P_depression_last_entry", "tau_P_depression",
            self._tau_P_depression_last_entry))
        prov_data.append(plasticity_helpers.get_lut_provenance(
            pre_population_label, post_population_label, "STP_Abbot_Rule",
            "tau_P_facilitation_entry", "tau_P_facilitation",
            self._tau_P_facilitation_last_entry))
        return prov_data

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['STP_type', 'f', 'P_baseline','tau_P']

    @overrides(AbstractTimingDependence.initialise_row_headers)
    def initialise_row_headers(self, n_rows, n_header_bytes):
        # note that data is written here as 16-bit quantities, but converted
        # back to 8-bit quantities for consistency with synaptic row generation

        # Initialise header structure
        header = numpy.zeros(
            (n_rows, (n_header_bytes/2)), dtype="uint16")

#         fixed_point_f = plasticity_helpers.float_to_fixed(
#             self._f, plasticity_helpers.STDP_FIXED_POINT_ONE)

        # Initialise header parameters
        # header[0,0] = int(0.6 * STDP_FIXED_POINT_ONE) # STDP pre_trace
        header[0,1] = int(self._P_baseline * STDP_FIXED_POINT_ONE) # P_Baseline
        header[0,2] = int(self._P_baseline * STDP_FIXED_POINT_ONE) # STP trace
        header[0,3] = int(self._STP_type) # STP type (enables facilitation and
                                    # depression on same post-synaptic neuron)
        header[0,4] = int(self._f * STDP_FIXED_POINT_ONE)
        # header[0,5] = empty
        # header[0,6-7] = 32-bit timestamp

        # re-cast as array of 8-bit quantities to facilitate row generation
        return header.view(dtype="uint8")