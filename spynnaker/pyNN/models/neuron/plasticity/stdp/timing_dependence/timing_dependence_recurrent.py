import math
import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType

from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence.\
    abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp\
    .synapse_structure.synapse_structure_weight_accumulator \
    import SynapseStructureWeightAccumulator
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import plasticity_helpers


class TimingDependenceRecurrent(AbstractTimingDependence):
    def __init__(
            self, accum_decay = 10.00,
            accum_dep_thresh_excit=-6, accum_pot_thresh_excit=7,
            pre_window_tc_excit=20.0, post_window_tc_excit=25.0, 
            accum_dep_thresh_excit2=-6, accum_pot_thresh_excit2=7,
            pre_window_tc_excit2=20.0, post_window_tc_excit2=25.0, 
            accum_dep_thresh_inhib=-4, accum_pot_thresh_inhib=5,
            pre_window_tc_inhib=35.0, post_window_tc_inhib=45.0, 
            accum_dep_thresh_inhib2=-4, accum_pot_thresh_inhib2=5,
            pre_window_tc_inhib2=35.0, post_window_tc_inhib2=45.0, 
            dual_fsm=True, seed=None):
        AbstractTimingDependence.__init__(self)

        self.accum_decay               = accum_decay

        self.accum_dep_plus_one_excit  = accum_dep_thresh_excit + 1
        self.accum_pot_minus_one_excit = accum_pot_thresh_excit - 1
        self.pre_window_tc_excit = pre_window_tc_excit
        self.post_window_tc_excit = post_window_tc_excit

        self.accum_dep_plus_one_excit2  = accum_dep_thresh_excit2 + 1
        self.accum_pot_minus_one_excit2 = accum_pot_thresh_excit2 - 1
        self.pre_window_tc_excit2 = pre_window_tc_excit2
        self.post_window_tc_excit2 = post_window_tc_excit2

        self.accum_dep_plus_one_inhib  = accum_dep_thresh_inhib + 1
        self.accum_pot_minus_one_inhib = accum_pot_thresh_inhib - 1
        self.pre_window_tc_inhib = pre_window_tc_inhib
        self.post_window_tc_inhib = post_window_tc_inhib

        self.accum_dep_plus_one_inhib2  = accum_dep_thresh_inhib2 + 1
        self.accum_pot_minus_one_inhib2 = accum_pot_thresh_inhib2 - 1
        self.pre_window_tc_inhib2 = pre_window_tc_inhib2
        self.post_window_tc_inhib2 = post_window_tc_inhib2
        #self.accumulator_depression_plus_one = accumulator_depression + 1
        #self.accumulator_potentiation_minus_one = accumulator_potentiation - 1
        #self.mean_pre_window = mean_pre_window
        #self.mean_post_window = mean_post_window
        self.dual_fsm = dual_fsm
        self.rng = numpy.random.RandomState(seed)

        self._synapse_structure = SynapseStructureWeightAccumulator()

    def is_same_as(self, other):
        if (other is None) or (not isinstance(
                other, TimingDependenceRecurrent)):
            return False
        return ((self.accum_dep_plus_one_excit == other.accum_dep_plus_one_excit) and
                (self.accum_pot_minus_one_excit == other.accum_pot_minus_one_excit) and
                (self.pre_window_tc_excit == other.pre_window_tc_excit) and
                (self.pre_window_tc_excit == other.post_window_tc_excit))
        #return ((self.accumulator_depression_plus_one ==
        #         other.accumulator_depression_plus_one) and
        #        (self.accumulator_potentiation_minus_one ==
        #         other.accumulator_potentiation_minus_one) and
        #        (self.mean_pre_window == other.mean_pre_window) and
        #        (self.mean_post_window == other.mean_post_window))

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
        numParams = 17
        numLUTs   = 4
        numSeeds  = 4
        return (
            (4 * numParams) 
          + (4 * plasticity_helpers.STDP_FIXED_POINT_ONE * numLUTs)
          + (4 * numSeeds))

    @property
    def n_weight_terms(self):
        return 1

    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Acc decay per timeStep is scaled up by 1024 to preserve 10-bit precision:
        acc_decay_per_ts = (int)((float(self.accum_decay) * float(machine_time_step)*1.024))
        # Write parameters (four per synapse type):
        spec.write_value(data=acc_decay_per_ts,                data_type=DataType.INT32)
        spec.write_value(data=self.accum_dep_plus_one_excit,   data_type=DataType.INT32)
        spec.write_value(data=self.accum_pot_minus_one_excit,  data_type=DataType.INT32)
        spec.write_value(data=self.pre_window_tc_excit,        data_type=DataType.INT32)
        spec.write_value(data=self.post_window_tc_excit,       data_type=DataType.INT32)

        spec.write_value(data=self.accum_dep_plus_one_excit2,   data_type=DataType.INT32)
        spec.write_value(data=self.accum_pot_minus_one_excit2,  data_type=DataType.INT32)
        spec.write_value(data=self.pre_window_tc_excit2,        data_type=DataType.INT32)
        spec.write_value(data=self.post_window_tc_excit2,       data_type=DataType.INT32)

        spec.write_value(data=self.accum_dep_plus_one_inhib,   data_type=DataType.INT32)
        spec.write_value(data=self.accum_pot_minus_one_inhib,  data_type=DataType.INT32)
        spec.write_value(data=self.pre_window_tc_inhib,        data_type=DataType.INT32)
        spec.write_value(data=self.post_window_tc_inhib,       data_type=DataType.INT32)

        spec.write_value(data=self.accum_dep_plus_one_inhib2,   data_type=DataType.INT32)
        spec.write_value(data=self.accum_pot_minus_one_inhib2,  data_type=DataType.INT32)
        spec.write_value(data=self.pre_window_tc_inhib2,        data_type=DataType.INT32)
        spec.write_value(data=self.post_window_tc_inhib2,       data_type=DataType.INT32)

        # Convert mean times into machine timesteps
        mean_pre_timesteps_excit = (float(self.pre_window_tc_excit) *
                              (1000.0 / float(machine_time_step)))
        mean_post_timesteps_excit = (float(self.post_window_tc_excit) *
                               (1000.0 / float(machine_time_step)))
        mean_pre_timesteps_inhib = (float(self.pre_window_tc_inhib) *
                              (1000.0 / float(machine_time_step)))
        mean_post_timesteps_inhib = (float(self.post_window_tc_inhib) *
                               (1000.0 / float(machine_time_step)))

        mean_pre_timesteps_excit2 = (float(self.pre_window_tc_excit2) *
                              (1000.0 / float(machine_time_step)))
        mean_post_timesteps_excit2 = (float(self.post_window_tc_excit2) *
                               (1000.0 / float(machine_time_step)))
        mean_pre_timesteps_inhib2 = (float(self.pre_window_tc_inhib2) *
                              (1000.0 / float(machine_time_step)))
        mean_post_timesteps_inhib2 = (float(self.post_window_tc_inhib2) *
                               (1000.0 / float(machine_time_step)))

        # Write lookup tables
        self._write_exp_dist_lut(spec, mean_pre_timesteps_excit)
        self._write_exp_dist_lut(spec, mean_post_timesteps_excit)
        self._write_exp_dist_lut(spec, mean_pre_timesteps_excit2)
        self._write_exp_dist_lut(spec, mean_post_timesteps_excit2)
        self._write_exp_dist_lut(spec, mean_pre_timesteps_inhib)
        self._write_exp_dist_lut(spec, mean_post_timesteps_inhib)
        self._write_exp_dist_lut(spec, mean_pre_timesteps_inhib2)
        self._write_exp_dist_lut(spec, mean_post_timesteps_inhib2)

        # Write random seeds
        #spec.write_value(data=self.rng.randint(0x7FFFFFF1),
        #                 data_type=DataType.UINT32)
        #spec.write_value(data=self.rng.randint(0x7FFFFFF2),
        #                 data_type=DataType.UINT32)
        #spec.write_value(data=self.rng.randint(0x7FFFFFF3),
        #                 data_type=DataType.UINT32)
        #spec.write_value(data=self.rng.randint(0x7FFFFFF4),
        #                 data_type=DataType.UINT32)
        spec.write_value(data=0x7FFFFFF1,
                         data_type=DataType.UINT32)
        spec.write_value(data=0x7FFFFFF2,
                        data_type=DataType.UINT32)
        spec.write_value(data=0x7FFFFFF3,
                         data_type=DataType.UINT32)
        spec.write_value(data=0x7FFFFFF4,
                         data_type=DataType.UINT32)

    @property
    def pre_trace_size_bytes(self):
        # When using the separate FSMs, pre-trace contains window length,
        # otherwise it's in the synapse
        return 2 if self.dual_fsm else 0

    @property
    def num_terms(self):
        return 1

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
        return ['acc_decay_per_ts' 'accum_dep_plus_one_excit', 'accum_pot_minus_one_excit', 'pre_window_tc_excit', 'post_window_tc_excit', 'accum_dep_plus_one_inhib', 'accum_pot_minus_one_inhib', 'pre_window_tc_inhib', 'post_window_tc_inhib']

