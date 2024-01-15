# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy
from numpy import floating
from numpy.typing import NDArray
from typing import cast, Iterable
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationBase)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)

from spynnaker.pyNN.data import SpynnakerDataView
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightAccumulator)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    STDP_FIXED_POINT_ONE)


class TimingDependenceRecurrent(AbstractTimingDependence):
    """
    A timing dependence STDP rule based on recurrences.
    """
    __slots__ = (
        "__accumulator_depression_plus_one",
        "__accumulator_potentiation_minus_one",
        "__dual_fsm",
        "__mean_post_window",
        "__mean_pre_window",
        "__a_plus",
        "__a_minus")

    __PARAM_NAMES = (
        'accumulator_depression', 'accumulator_potentiation',
        'mean_pre_window', 'mean_post_window', 'dual_fsm')

    default_parameters = {
        'accumulator_depression': -6, 'accumulator_potentiation': 6,
        'mean_pre_window': 35.0, 'mean_post_window': 35.0, 'dual_fsm': True}

    def __init__(
            self, accumulator_depression: int = cast(int, default_parameters[
                'accumulator_depression']),
            accumulator_potentiation: int = cast(int, default_parameters[
                'accumulator_potentiation']),
            mean_pre_window: float = default_parameters['mean_pre_window'],
            mean_post_window: float = default_parameters['mean_post_window'],
            dual_fsm: bool = cast(bool, default_parameters['dual_fsm']),
            A_plus: float = 0.01, A_minus: float = 0.01):
        """
        :param int accumulator_depression:
        :param int accumulator_potentiation:
        :param float mean_pre_window:
        :param float mean_post_window:
        :param bool dual_fsm:
        :param float A_plus: :math:`A^+`
        :param float A_minus: :math:`A^-`
        """
        # pylint: disable=too-many-arguments
        super().__init__(SynapseStructureWeightAccumulator())
        self.__accumulator_depression_plus_one = accumulator_depression + 1
        self.__accumulator_potentiation_minus_one = \
            accumulator_potentiation - 1
        self.__mean_pre_window = mean_pre_window
        self.__mean_post_window = mean_post_window
        self.__dual_fsm = dual_fsm
        self.__a_plus = A_plus
        self.__a_minus = A_minus

    @property
    def A_plus(self) -> float:
        r"""
        :math:`A^+`

        :rtype: float
        """
        return self.__a_plus

    @A_plus.setter
    def A_plus(self, new_value: float):
        self.__a_plus = new_value

    @property
    def A_minus(self) -> float:
        r"""
        :math:`A^-`

        :rtype: float
        """
        return self.__a_minus

    @A_minus.setter
    def A_minus(self, new_value: float):
        self.__a_minus = new_value

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence: AbstractTimingDependence) -> bool:
        if not isinstance(timing_dependence, TimingDependenceRecurrent):
            return False
        # pylint: disable=protected-access
        return self._character() == timing_dependence._character()

    def _character(self) -> object:
        """
        Two instances of this class are the same if their characterisation is
        the same.
        """
        return (self.__accumulator_depression_plus_one,
                self.__accumulator_potentiation_minus_one,
                self.__mean_pre_window, self.__mean_post_window)

    @property
    def vertex_executable_suffix(self) -> str:
        """
        The suffix to be appended to the vertex executable for this rule.

        :rtype: str
        """
        if self.__dual_fsm:
            return "recurrent_dual_fsm"
        return "recurrent_pre_stochastic"

    @property
    def pre_trace_n_bytes(self) -> int:
        """
        The number of bytes used by the pre-trace of the rule per neuron.

        :rtype: int
        """
        # When using the separate FSMs, pre-trace contains window length,
        # otherwise it's in the synapse
        return BYTES_PER_SHORT if self.__dual_fsm else 0

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self) -> int:
        # 2 * 32-bit parameters
        # 2 * LUTS with STDP_FIXED_POINT_ONE * 16-bit entries
        return (2 * BYTES_PER_WORD) + (
            2 * STDP_FIXED_POINT_ONE * BYTES_PER_SHORT)

    @property
    def n_weight_terms(self) -> int:
        """
        The number of weight terms expected by this timing rule.

        :rtype: int
        """
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationBase, global_weight_scale: float,
            synapse_weight_scales: NDArray[floating]):
        # Write parameters
        spec.write_value(data=self.__accumulator_depression_plus_one,
                         data_type=DataType.INT32)
        spec.write_value(data=self.__accumulator_potentiation_minus_one,
                         data_type=DataType.INT32)

        # Convert mean times into machine timesteps
        time_step_per_ms = SpynnakerDataView.get_simulation_time_step_per_ms()

        mean_pre_timesteps = float(self.__mean_pre_window * time_step_per_ms)
        mean_post_timesteps = float(self.__mean_post_window * time_step_per_ms)

        # Write lookup tables
        self._write_exp_dist_lut(spec, mean_pre_timesteps)
        self._write_exp_dist_lut(spec, mean_post_timesteps)

    @staticmethod
    def _write_exp_dist_lut(spec: DataSpecificationBase, mean: float):
        """
        :param .DataSpecificationGenerator spec:
        :param float mean:
        """
        indices = numpy.arange(STDP_FIXED_POINT_ONE)
        inv_cdf = numpy.log(1.0 - indices/float(STDP_FIXED_POINT_ONE)) * -mean
        spec.write_array(
            inv_cdf.astype(numpy.uint16), data_type=DataType.UINT16)

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        return self.__PARAM_NAMES
