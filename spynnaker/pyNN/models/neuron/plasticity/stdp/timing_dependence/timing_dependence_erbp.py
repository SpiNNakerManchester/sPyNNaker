from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import plasticity_helpers
from spynnaker.pyNN.models.neuron.plasticity.stdp.common\
    .plasticity_helpers import get_exp_lut_array
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    import SynapseStructureWeightAndTrace
from data_specification.enums import DataType
from spinn_front_end_common.utilities.globals_variables import get_simulator

import logging
logger = logging.getLogger(__name__)

LOOKUP_TAU_PLUS_SIZE = 2048
LOOKUP_TAU_PLUS_SHIFT = 0
LOOKUP_TAU_MINUS_SIZE = 0
LOOKUP_TAU_MINUS_SHIFT = 0


class TimingDependenceERBP(AbstractTimingDependence):
    __slots__ = [
        "__synapse_structure",
        "__tau_minus",
        "__tau_minus_last_entry",
        "__tau_plus_data",
        "__tau_plus",
        "__tau_plus_last_entry",
        "__is_readout"]

    def __init__(self, tau_plus=20.0, tau_minus=20.0, is_readout=False):
        self.__tau_plus = tau_plus
        self.__tau_minus = tau_minus

        self.__is_readout = is_readout
        self.__synapse_structure = SynapseStructureWeightAndTrace()

        ts = get_simulator().machine_time_step / 1000.
        self.__tau_plus_data = get_exp_lut_array(ts, self.__tau_plus, size=LOOKUP_TAU_PLUS_SIZE)
        print("len after creation of table : {}".format(len(self.__tau_plus_data)))
        # provenance data
        self.__tau_plus_last_entry = None
        self.__tau_minus_last_entry = None


    @property
    def tau_plus(self):
        return self.__tau_plus

    @property
    def tau_minus(self):
        return self.__tau_minus

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence, TimingDependenceERBP):
            return False
        return (self.__tau_plus == timing_dependence.tau_plus and
                self.__tau_minus == timing_dependence.tau_minus)

    @property
    def vertex_executable_suffix(self):
        return "timing"

    @property
    def pre_trace_n_bytes(self):

        # Pair rule requires no pre-synaptic trace when only the nearest
        # Neighbours are considered and, a single 16-bit R1 trace
        return 2

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        print("len table : {}".format(len(self.__tau_plus_data)))

        return (4 * len(self.__tau_plus_data)) + 4  # 4 is for is_readout flag
    #(LOOKUP_TAU_PLUS_SIZE + LOOKUP_TAU_MINUS_SIZE) \


    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, machine_time_step, weight_scales):
        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError(
                "STDP LUT generation currently only supports 1ms timesteps")

#         # Write lookup tables
#         self._tau_plus_last_entry = plasticity_helpers.write_exp_lut(
#             spec, self.__tau_plus, LOOKUP_TAU_PLUS_SIZE,
#             LOOKUP_TAU_PLUS_SHIFT)
        spec.write_array(self.__tau_plus_data)
#         self._tau_minus_last_entry = plasticity_helpers.write_exp_lut(
#             spec, self._tau_minus, LOOKUP_TAU_MINUS_SIZE,
#             LOOKUP_TAU_MINUS_SHIFT)

        print("Is readout val: {}".format(int(self.__is_readout)))
        spec.write_value(
                data=int(self.__is_readout),
                data_type=DataType.INT32)

    @property
    def synaptic_structure(self):
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_provenance_data)
    def get_provenance_data(self, pre_population_label, post_population_label):
        prov_data = list()
#         prov_data.append(plasticity_helpers.get_lut_provenance(
#             pre_population_label, post_population_label, "SpikePairRule",
#             "tau_plus_last_entry", "tau_plus", self.__tau_plus_last_entry))
#         prov_data.append(plasticity_helpers.get_lut_provenance(
#             pre_population_label, post_population_label, "SpikePairRule",
#             "tau_minus_last_entry", "tau_minus", self._tau_minus_last_entry))
        return prov_data

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['tau_plus', 'tau_minus']
