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

from typing import Iterable

from numpy import floating
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides

from spinn_front_end_common.interface.ds import (
    DataSpecificationBase, DataType)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    AbstractTimingDependence)
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightOnly)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    float_to_fixed, get_exp_lut_array)


class TimingDependenceVogels2011(AbstractTimingDependence):
    """
    A timing dependence STDP rule due to Vogels (2011).
    """
    __slots__ = (
        "__alpha",
        "__tau",
        "__tau_data",
        "__a_plus",
        "__a_minus")
    __PARAM_NAMES = ('alpha', 'tau')

    def __init__(self, alpha: float, tau: float = 20.0,
                 A_plus: float = 0.01, A_minus: float = 0.01):
        r"""
        :param alpha: :math:`\alpha`
        :param tau: :math:`\tau`
        :param A_plus: :math:`A^+`
        :param A_minus: :math:`A^-`
        """
        super().__init__(SynapseStructureWeightOnly())
        self.__alpha = alpha
        self.__tau = tau
        self.__a_plus = A_plus
        self.__a_minus = A_minus

        self.__tau_data = get_exp_lut_array(
            SpynnakerDataView.get_simulation_time_step_ms(), self.__tau)

    @property
    def alpha(self) -> float:
        r"""
        :math:`\alpha`
        """
        return self.__alpha

    @property
    def tau(self) -> float:
        r"""
        :math:`\tau`
        """
        return self.__tau

    @property
    def A_plus(self) -> float:
        r"""
        :math:`A^+`
        """
        return self.__a_plus

    @A_plus.setter
    def A_plus(self, new_value: float) -> None:
        self.__a_plus = new_value

    @property
    def A_minus(self) -> float:
        r"""
        :math:`A^-`
        """
        return self.__a_minus

    @A_minus.setter
    def A_minus(self, new_value: float) -> None:
        self.__a_minus = new_value

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence: AbstractTimingDependence) -> bool:
        if not isinstance(timing_dependence, TimingDependenceVogels2011):
            return False
        return (self.__tau == timing_dependence.tau and
                self.__alpha == timing_dependence.alpha)

    @property
    def vertex_executable_suffix(self) -> str:
        """
        The suffix to be appended to the vertex executable for this rule.
        """
        return "vogels_2011"

    @property
    def pre_trace_n_bytes(self) -> int:
        """
        The number of bytes used by the pre-trace of the rule per neuron.
        """
        # Trace entries consist of a single 16-bit number
        return BYTES_PER_SHORT

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self) -> int:
        return BYTES_PER_WORD + BYTES_PER_WORD * len(self.__tau_data)

    @property
    def n_weight_terms(self) -> int:
        """
        The number of weight terms expected by this timing rule.
        """
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationBase, global_weight_scale: float,
            synapse_weight_scales: NDArray[floating]) -> None:
        # Write alpha to spec
        fixed_point_alpha = float_to_fixed(self.__alpha)
        spec.write_value(data=fixed_point_alpha, data_type=DataType.INT32)

        # Write lookup table
        spec.write_array(self.__tau_data)

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        return self.__PARAM_NAMES
