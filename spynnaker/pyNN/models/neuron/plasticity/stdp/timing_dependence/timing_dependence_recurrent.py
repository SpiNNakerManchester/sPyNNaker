import math
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightAccumulator)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    plasticity_helpers)


class TimingDependenceRecurrent(AbstractTimingDependence):
    __slots__ = [
        "__accumulator_depression_plus_one",
        "__accumulator_potentiation_minus_one",
        "__dual_fsm",
        "__mean_post_window",
        "__mean_pre_window",
        "__synapse_structure"]

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
        # pylint: disable=too-many-arguments
        self.__accumulator_depression_plus_one = accumulator_depression + 1
        self.__accumulator_potentiation_minus_one = \
            accumulator_potentiation - 1
        self.__mean_pre_window = mean_pre_window
        self.__mean_post_window = mean_post_window
        self.__dual_fsm = dual_fsm

        self.__synapse_structure = SynapseStructureWeightAccumulator()

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if timing_dependence is None or not isinstance(
                timing_dependence, TimingDependenceRecurrent):
            return False
        return ((self.__accumulator_depression_plus_one ==
                 timing_dependence.accumulator_depression_plus_one) and
                (self.__accumulator_potentiation_minus_one ==
                 timing_dependence.accumulator_potentiation_minus_one) and
                (self.__mean_pre_window ==
                 timing_dependence.mean_pre_window) and
                (self.__mean_post_window ==
                 timing_dependence.mean_post_window))

    @property
    def vertex_executable_suffix(self):
        if self.__dual_fsm:
            return "recurrent_dual_fsm"
        return "recurrent_pre_stochastic"

    @property
    def pre_trace_n_bytes(self):

        # When using the separate FSMs, pre-trace contains window length,
        # otherwise it's in the synapse
        return 2 if self.__dual_fsm else 0

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):

        # 2 * 32-bit parameters
        # 2 * LUTS with STDP_FIXED_POINT_ONE * 16-bit entries
        return (4 * 2) + (2 * (2 * plasticity_helpers.STDP_FIXED_POINT_ONE))

    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Write parameters
        spec.write_value(data=self.__accumulator_depression_plus_one,
                         data_type=DataType.INT32)
        spec.write_value(data=self.__accumulator_potentiation_minus_one,
                         data_type=DataType.INT32)

        # Convert mean times into machine timesteps
        mean_pre_timesteps = (float(self.__mean_pre_window) *
                              (1000.0 / float(machine_time_step)))
        mean_post_timesteps = (float(self.__mean_post_window) *
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
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['accumulator_depression', 'accumulator_potentiation',
                'mean_pre_window', 'mean_post_window', 'dual_fsm']
