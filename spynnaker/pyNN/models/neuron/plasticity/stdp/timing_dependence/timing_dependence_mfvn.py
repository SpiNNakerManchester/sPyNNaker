from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import write_mfvn_lut, get_lut_provenance
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    import SynapseStructureWeightOnly


import logging
logger = logging.getLogger(__name__)

LUT_SIZE = 256

class TimingDependenceMFVN(AbstractTimingDependence):
    __slots__ = [
        "_synapse_structure",
        "_tau_minus",
        "_tau_minus_last_entry",
        "_tau_plus",
        "_tau_plus_last_entry",
        "_beta",
        "_sigma",
        "_kernel_scaling"
        ]

    def __init__(self, tau_plus=20.0, tau_minus=20.0, beta=10, sigma=200, kernel_scaling=1.0):
        self._tau_plus = tau_plus
        self._tau_minus = tau_minus
        self._kernel_scaling = kernel_scaling

        self._synapse_structure = SynapseStructureWeightOnly()

        self._beta = beta
        self._sigma = sigma

        # provenance data
        self._tau_plus_last_entry = None
        self._tau_minus_last_entry = None

    @property
    def tau_plus(self):
        return self._tau_plus

    @property
    def tau_minus(self):
        return self._tau_minus

    @property
    def beta(self):
        return self._beta

    @property
    def sigma(self):
        return self._sigma

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence, TimingDependenceMFVN):
            return False
        return (self.tau_plus == timing_dependence.tau_plus and
                self.tau_minus == timing_dependence.tau_minus)

    @property
    def vertex_executable_suffix(self):
        return "mfvn"

    @property
    def pre_trace_n_bytes(self):

        # Here we will record the last 16 spikes, these will be 32-bit quantities,
        return (16 * 4) + (2 * 16) # 16 4-byte entries, plus one counter for the number of spikes

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 2 * LUT_SIZE #in bytes: 256 * 16 bit values

    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, machine_time_step, weight_scales):
        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError(
                "exp cos LUT generation currently only supports 1ms timesteps")

        # Write exp_sin lookup table
        self._tau_plus_last_entry = write_mfvn_lut(
            spec,
            sigma=self._sigma,
            beta=self._beta,
            time_probe=None,
            lut_size=LUT_SIZE,
            shift=0,
            kernel_scaling=self._kernel_scaling)

    @property
    def synaptic_structure(self):
        return self._synapse_structure

    @overrides(AbstractTimingDependence.get_provenance_data)
    def get_provenance_data(self, pre_population_label, post_population_label):
        prov_data = list()
        prov_data.append(get_lut_provenance(
            pre_population_label, post_population_label, "MFVNRule",
            "tau_plus_last_entry", "tau_plus", self._tau_plus_last_entry))
        prov_data.append(get_lut_provenance(
            pre_population_label, post_population_label, "MFVNRule",
            "tau_minus_last_entry", "tau_minus", self._tau_minus_last_entry))
        return prov_data

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['tau_plus', 'tau_minus', 'beta', 'sigma']
