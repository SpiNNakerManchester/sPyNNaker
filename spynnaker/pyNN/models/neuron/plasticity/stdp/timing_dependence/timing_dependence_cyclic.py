import math
import numpy
from data_specification.enums import DataType

from spinn_utilities.overrides import overrides
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure \
    import SynapseStructureWeightRecurrentAccumulator
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import plasticity_helpers


class TimingDependenceCyclic(AbstractTimingDependence):
    __slots__ = [
#         "accumulator_depression_plus_one",
#         "accumulator_potentiation_minus_one",
#         "dual_fsm",
#         "mean_post_window",
#         "mean_pre_window",
#         "_synapse_structure",
        #
        'accum_decay',
        'accum_dep_thresh_excit',
        'accum_pot_thresh_excit',
        'pre_window_tc_excit',
        'post_window_tc_excit',
        'accum_dep_thresh_excit2',
        'accum_pot_thresh_excit2',
        'pre_window_tc_excit2',
        'post_window_tc_excit2',
        'accum_dep_thresh_inhib',
        'accum_pot_thresh_inhib',
        'pre_window_tc_inhib',
        'post_window_tc_inhib',
        'accum_dep_thresh_inhib2',
        'accum_pot_thresh_inhib2',
        'pre_window_tc_inhib2',
        'post_window_tc_inhib2',
        'seed',
        'accum_dep_plus_one_excit',
        'accum_pot_minus_one_excit',
        'accum_dep_plus_one_excit2',
        'accum_pot_minus_one_excit2',
        'accum_dep_plus_one_inhib',
        'accum_pot_minus_one_inhib',
        'accum_dep_plus_one_inhib2',
        'accum_pot_minus_one_inhib2',
        'rng',
        'random_enabled',
        'v_diff_pot_threshold',
        '_synapse_structure'
        ]

    default_parameters = {
#         'accumulator_depression': -6, 'accumulator_potentiation': 6,
#         'mean_pre_window': 35.0, 'mean_post_window': 35.0
        'accum_decay':10.00,
        'accum_dep_thresh_excit':-6,
        'accum_pot_thresh_excit':7,
        'pre_window_tc_excit':20.0,
        'post_window_tc_excit':25.0,
        'accum_dep_thresh_excit2':-6,
        'accum_pot_thresh_excit2':7,
        'pre_window_tc_excit2':20.0,
        'post_window_tc_excit2':25.0,
        'accum_dep_thresh_inhib':-4,
        'accum_pot_thresh_inhib':5,
        'pre_window_tc_inhib':35.0,
        'post_window_tc_inhib':45.0,
        'accum_dep_thresh_inhib2':-4,
        'accum_pot_thresh_inhib2':5,
        'pre_window_tc_inhib2':35.0,
        'post_window_tc_inhib2':45.0,
        'seed':None,
        'random_enabled': True,
        'v_diff_pot_threshold': 1}

    def __init__(
            self, accum_decay = default_parameters['accum_decay'],
            accum_dep_thresh_excit=default_parameters['accum_dep_thresh_excit'],
            accum_pot_thresh_excit=default_parameters['accum_pot_thresh_excit'],
            pre_window_tc_excit=default_parameters['pre_window_tc_excit'],
            post_window_tc_excit=default_parameters['post_window_tc_excit'],
            accum_dep_thresh_excit2=default_parameters['accum_dep_thresh_excit2'],
            accum_pot_thresh_excit2=default_parameters['accum_pot_thresh_excit2'],
            pre_window_tc_excit2=default_parameters['pre_window_tc_excit2'],
            post_window_tc_excit2=default_parameters['post_window_tc_excit2'],
            accum_dep_thresh_inhib=default_parameters['accum_dep_thresh_inhib'],
            accum_pot_thresh_inhib=default_parameters['accum_pot_thresh_inhib'],
            pre_window_tc_inhib=default_parameters['pre_window_tc_inhib'],
            post_window_tc_inhib=default_parameters['post_window_tc_inhib'],
            accum_dep_thresh_inhib2=default_parameters['accum_dep_thresh_inhib2'],
            accum_pot_thresh_inhib2=default_parameters['accum_pot_thresh_inhib2'],
            pre_window_tc_inhib2=default_parameters['pre_window_tc_inhib2'],
            post_window_tc_inhib2=default_parameters['post_window_tc_inhib2'],
            seed=default_parameters['seed'],
            random_enabled=default_parameters['random_enabled'],
            v_diff_pot_threshold=default_parameters['v_diff_pot_threshold']):
        AbstractTimingDependence.__init__(self)

        self.accum_decay = accum_decay

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
        self.rng = numpy.random.RandomState(seed)
        self.random_enabled=random_enabled
        self.v_diff_pot_threshold = v_diff_pot_threshold

        self._synapse_structure = SynapseStructureWeightRecurrentAccumulator()

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if timing_dependence is None or not isinstance(
                timing_dependence, TimingDependenceCyclic):
            return False
        return True
        # SD Removed this as it now cuases erros after move to PyNN8:
        #return ((self.accum_dep_plus_one_excit == other.accum_dep_plus_one_excit) and
        #        (self.accum_pot_minus_one_excit == other.accum_pot_minus_one_excit) and
        #        (self.pre_window_tc_excit == other.pre_window_tc_excit) and
        #        (self.post_window_tc_excit == other.post_window_tc_excit))

    @property
    def vertex_executable_suffix(self):
        return "cyclic"

    @property
    def pre_trace_n_bytes(self):

        # otherwise it's in the synapse
        return 2

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):

        # 2 * 32-bit parameters
        # 2 * LUTS with STDP_FIXED_POINT_ONE * 16-bit entries
        numParams = (4 * 4) + 1 + 1 + 1
        # +acc_decay_per_32ts, +random_enabled, +v_diff_pot_threshold
        numLUTs   = 8
        numSeeds  = 4
        thirty_two_bit_wordlength = 4
        sixteen_bit_wordlength = 2

        return (
            (thirty_two_bit_wordlength * numParams)
          + (sixteen_bit_wordlength *
             (plasticity_helpers.STDP_FIXED_POINT_ONE>>2) * numLUTs)
          + (thirty_two_bit_wordlength * numSeeds)
          )

    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Acc decay per timeStep is scaled up by 1024 to preserve 10-bit precision:
        #acc_decay_per_ts = (int)((float(self.accum_decay) * float(machine_time_step)*1.024))
        acc_decay_per_32ts = (int)(float(self.accum_decay) * 32 * 1.024
                                   * float(machine_time_step)/1000.0)
        spec.write_value(data=acc_decay_per_32ts,
                         data_type=DataType.INT32)

        # Write parameters (four per synapse type):
        spec.write_value(data=self.accum_dep_plus_one_excit,
                         data_type=DataType.INT32)
        spec.write_value(data=self.accum_pot_minus_one_excit,
                         data_type=DataType.INT32)
        spec.write_value(data=self.pre_window_tc_excit,
                         data_type=DataType.INT32)
        spec.write_value(data=self.post_window_tc_excit,
                         data_type=DataType.INT32)

        spec.write_value(data=self.accum_dep_plus_one_excit2,
                         data_type=DataType.INT32)
        spec.write_value(data=self.accum_pot_minus_one_excit2,
                         data_type=DataType.INT32)
        spec.write_value(data=self.pre_window_tc_excit2,
                         data_type=DataType.INT32)
        spec.write_value(data=self.post_window_tc_excit2,
                         data_type=DataType.INT32)

        spec.write_value(data=self.accum_dep_plus_one_inhib,
                         data_type=DataType.INT32)
        spec.write_value(data=self.accum_pot_minus_one_inhib,
                         data_type=DataType.INT32)
        spec.write_value(data=self.pre_window_tc_inhib,
                         data_type=DataType.INT32)
        spec.write_value(data=self.post_window_tc_inhib,
                         data_type=DataType.INT32)

        spec.write_value(data=self.accum_dep_plus_one_inhib2,
                         data_type=DataType.INT32)
        spec.write_value(data=self.accum_pot_minus_one_inhib2,
                         data_type=DataType.INT32)
        spec.write_value(data=self.pre_window_tc_inhib2,
                         data_type=DataType.INT32)
        spec.write_value(data=self.post_window_tc_inhib2,
                         data_type=DataType.INT32)

        if self.random_enabled:
            spec.write_value(data=1,
                data_type=DataType.INT32)
            # print "random_enabled = true"
        else:
            spec.write_value(data=0,
                data_type=DataType.INT32)
            # print "random_enabled = False"

        spec.write_value(data=self.v_diff_pot_threshold,
                         data_type=DataType.S1615)


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
        #self._write_exp_dist_lut_print(spec, mean_pre_timesteps_inhib2)
        self._write_exp_dist_lut(spec, mean_pre_timesteps_inhib2)
        self._write_exp_dist_lut(spec, mean_post_timesteps_inhib2)

        # Write random seeds
        spec.write_value(data=self.rng.randint(0x7FFFFFF1),
                         data_type=DataType.UINT32)
        spec.write_value(data=self.rng.randint(0x7FFFFFF2),
                         data_type=DataType.UINT32)
        spec.write_value(data=self.rng.randint(0x7FFFFFF3),
                         data_type=DataType.UINT32)
        spec.write_value(data=self.rng.randint(0x7FFFFFF4),
                         data_type=DataType.UINT32)
        #spec.write_value(data=0x7FFFFFF1,
        #                 data_type=DataType.UINT32)
        #spec.write_value(data=0x7FFFFFF2,
        #                data_type=DataType.UINT32)
        #spec.write_value(data=0x7FFFFFF3,
        #                 data_type=DataType.UINT32)
        #spec.write_value(data=0x7FFFFFF4,
        #                 data_type=DataType.UINT32)




    @property
    def pre_trace_size_bytes(self):
        # When using the separate FSMs, pre-trace contains window length,
        # otherwise it's in the synapse
        return 2 if self.dual_fsm else 0

    @property
    def num_terms(self):
        return 1

    def _write_exp_dist_lut(self, spec, mean):
        for x in range(plasticity_helpers.STDP_FIXED_POINT_ONE>>2):

            # Calculate inverse CDF
            x_float = float(x) / float(plasticity_helpers.STDP_FIXED_POINT_ONE>>2)
            p_float = math.log(1.0 - x_float) * -mean

            p = round(p_float)
            spec.write_value(data=p, data_type=DataType.UINT16)

    def _write_exp_dist_lut_print(self, spec, mean):
        count = 0
        for x in range(plasticity_helpers.STDP_FIXED_POINT_ONE>>2):

            # Calculate inverse CDF
            x_float = float(x) / float(plasticity_helpers.STDP_FIXED_POINT_ONE>>2)
            p_float = -math.log(1.0 - x_float) * mean

            p = round(p_float)
            print "x: ", x, " xfloat: ", x_float, " p_float: ", p_float, "  p_int: ", p
#             if count == 5:
#                print "x: ", x, " xfloat: ", x_float, " p_float: ", p_float, "  p_int: ", p
#                count = 0
#             count += 1
            spec.write_value(data=p, data_type=DataType.UINT16)

    @property
    def synaptic_structure(self):
        return self._synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['acc_decay_per_ts' 'accum_dep_plus_one_excit', 'accum_pot_minus_one_excit', 'pre_window_tc_excit', 'post_window_tc_excit',
                               'accum_dep_plus_one_excit2', 'accum_pot_minus_one_excit2', 'pre_window_tc_excit2', 'post_window_tc_excit2',
                               'accum_dep_plus_one_inhib', 'accum_pot_minus_one_inhib', 'pre_window_tc_inhib', 'post_window_tc_inhib',
                               'accum_dep_plus_one_inhib2', 'accum_pot_minus_one_inhib2', 'pre_window_tc_inhib2', 'post_window_tc_inhib2',
                               'random_enabled', 'v_diff_pot_threshold']

