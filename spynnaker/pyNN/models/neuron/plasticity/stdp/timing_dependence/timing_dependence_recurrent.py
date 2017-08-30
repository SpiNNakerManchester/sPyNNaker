import math

from data_specification.enums import DataType

from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence \
    import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure \
    import SynapseStructureWeightAccumulator
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import plasticity_helpers


class TimingDependenceRecurrent(AbstractTimingDependence):

    default_parameters = {
        'accumulator_depression': -6, 'accumulator_potentiation': 6,
        'mean_pre_window': 35.0, 'mean_post_window': 35.0, 'dual_fsm': True}

    def __init__(
            self, accumulator_depression=default_parameters[
                'accumulator_depression'],
            accumulator_potentiation=default_parameters[
                'accumulator_potentiation'],
            mean_pre_window=default_parameters['mean_pre_window'],
            mean_post_window=default_parameters['mean_post_window'],
            dual_fsm=default_parameters['dual_fsm']):

        AbstractTimingDependence.__init__(self)

        self.accumulator_depression_plus_one = accumulator_depression + 1
        self.accumulator_potentiation_minus_one = accumulator_potentiation - 1
        self.mean_pre_window = mean_pre_window
        self.mean_post_window = mean_post_window
        self.dual_fsm = dual_fsm

        self._synapse_structure = SynapseStructureWeightAccumulator()

    def is_same_as(self, other):
        if (other is None) or (not isinstance(
                other, TimingDependenceRecurrent)):
            return False
        return ((self.accumulator_depression_plus_one ==
                 other.accumulator_depression_plus_one) and
                (self.accumulator_potentiation_minus_one ==
                 other.accumulator_potentiation_minus_one) and
                (self.mean_pre_window == other.mean_pre_window) and
                (self.mean_post_window == other.mean_post_window))

    @property
    def vertex_executable_suffix(self):
        if self.dual_fsm:
            return "recurrent_dual_fsm"
        return "recurrent_pre_stochastic"

    @property
    def pre_trace_n_bytes(self):

        # When using the separate FSMs, pre-trace contains window length,
        # otherwise it's in the synapse
        return 2 if self.dual_fsm else 0

    def get_parameters_sdram_usage_in_bytes(self):

        # 2 * 32-bit parameters
        # 2 * LUTS with STDP_FIXED_POINT_ONE * 16-bit entries
        return (4 * 2) + (2 * (2 * plasticity_helpers.STDP_FIXED_POINT_ONE))

    @property
    def n_weight_terms(self):
        return 1

    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Write parameters
        spec.write_value(data=self.accumulator_depression_plus_one,
                         data_type=DataType.INT32)
        spec.write_value(data=self.accumulator_potentiation_minus_one,
                         data_type=DataType.INT32)

        # Convert mean times into machine timesteps
        mean_pre_timesteps = (float(self.mean_pre_window) *
                              (1000.0 / float(machine_time_step)))
        mean_post_timesteps = (float(self.mean_post_window) *
                               (1000.0 / float(machine_time_step)))

        # Write lookup tables
        self._write_exp_dist_lut(spec, mean_pre_timesteps)
        self._write_exp_dist_lut(spec, mean_post_timesteps)

    def _write_exp_dist_lut(self, spec, mean):
        for x in range(plasticity_helpers.STDP_FIXED_POINT_ONE):

            # Calculate inverse CDF
            x_float = float(x) / float(plasticity_helpers.STDP_FIXED_POINT_ONE)
            p_float = math.log(1.0 - x_float) * -mean

            p = round(p_float)
            spec.write_value(data=p, data_type=DataType.UINT16)

    @property
    def synaptic_structure(self):
        return self._synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['accumulator_depression', 'accumulator_potentiation',
                'mean_pre_window', 'mean_post_window', 'dual_fsm']
