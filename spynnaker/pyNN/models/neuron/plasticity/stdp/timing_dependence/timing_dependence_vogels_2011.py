from data_specification.enums import DataType

from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence\
    import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    import SynapseStructureWeightOnly
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import plasticity_helpers

import logging
logger = logging.getLogger(__name__)

# Constants
LOOKUP_TAU_SIZE = 256
LOOKUP_TAU_SHIFT = 0


class TimingDependenceVogels2011(AbstractTimingDependence):

    default_parameters = {'tau': 20.0}

    def __init__(self, alpha, tau=default_parameters['tau']):
        AbstractTimingDependence.__init__(self)

        self._alpha = alpha
        self._tau = tau

        self._synapse_structure = SynapseStructureWeightOnly()

    @property
    def tau(self):
        return self._tau

    def is_same_as(self, other):
        if (other is None) or (not isinstance(
                other, TimingDependenceVogels2011)):
            return False
        return ((self._tau == other._tau) and (self._alpha == other._alpha))

    @property
    def vertex_executable_suffix(self):
        return "vogels_2011"

    @property
    def pre_trace_n_bytes(self):

        # Trace entries consist of a single 16-bit number
        return 2

    def get_parameters_sdram_usage_in_bytes(self):
        return 4 + (2 * LOOKUP_TAU_SIZE)

    @property
    def n_weight_terms(self):
        return 1

    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError("STDP LUT generation currently only "
                                      "supports 1ms timesteps")

        # Write alpha to spec
        fixed_point_alpha = plasticity_helpers.float_to_fixed(
            self._alpha, plasticity_helpers.STDP_FIXED_POINT_ONE)
        spec.write_value(data=fixed_point_alpha, data_type=DataType.INT32)

        # Write lookup table
        plasticity_helpers.write_exp_lut(
            spec, self.tau, LOOKUP_TAU_SIZE, LOOKUP_TAU_SHIFT)

    @property
    def synaptic_structure(self):
        return self._synapse_structure
