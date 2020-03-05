# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy
from spinn_front_end_common.utilities.constants import \
    MICRO_TO_MILLISECOND_CONVERSION
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightAccumulator)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common.plasticity_helpers \
    import (
        STDP_FIXED_POINT_ONE)


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
        return BYTES_PER_SHORT if self.__dual_fsm else 0

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        # 2 * 32-bit parameters
        # 2 * LUTS with STDP_FIXED_POINT_ONE * 16-bit entries
        return (BYTES_PER_WORD * 2) + (
            BYTES_PER_SHORT * (2 * STDP_FIXED_POINT_ONE))

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
        mean_pre_timesteps = (
            float(self.__mean_pre_window) *
            (MICRO_TO_MILLISECOND_CONVERSION / float(machine_time_step)))
        mean_post_timesteps = (
            float(self.__mean_post_window) *
            (MICRO_TO_MILLISECOND_CONVERSION / float(machine_time_step)))

        # Write lookup tables
        self._write_exp_dist_lut(spec, mean_pre_timesteps)
        self._write_exp_dist_lut(spec, mean_post_timesteps)

    @staticmethod
    def _write_exp_dist_lut(spec, mean):
        """
        :param .DataSpecificationGenerator spec:
        :param float mean:
        """
        indices = numpy.arange(STDP_FIXED_POINT_ONE)
        inv_cdf = numpy.log(1.0 - indices/float(STDP_FIXED_POINT_ONE)) * -mean
        spec.write_array(
            inv_cdf.astype(numpy.uint16), data_type=DataType.UINT16)

    @property
    def synaptic_structure(self):
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['accumulator_depression', 'accumulator_potentiation',
                'mean_pre_window', 'mean_post_window', 'dual_fsm']
