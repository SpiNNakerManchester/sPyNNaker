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

from spinn_front_end_common.interface.ds import DataSpecificationBase
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_SHORT, BYTES_PER_WORD)

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    get_exp_lut_array)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    AbstractTimingDependence)
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightOnly)


class TimingDependencePfisterSpikeTriplet(AbstractTimingDependence):
    # pylint: disable=wrong-spelling-in-docstring
    """
    A timing dependence STDP rule based on spike triplets.

    Jean-Pascal Pfister, Wulfram Gerstner. Triplets of Spikes in a Model of
    Spike Timing-Dependent Plasticity. *Journal of Neuroscience*,
    20 September 2006, 26 (38) 9673-9682; DOI: 10.1523/JNEUROSCI.1425-06.2006
    """
    __slots__ = (
        "__tau_minus",
        "__tau_minus_data",
        "__tau_plus",
        "__tau_plus_data",
        "__tau_x",
        "__tau_x_data",
        "__tau_y",
        "__tau_y_data",
        "__a_plus",
        "__a_minus")
    __PARAM_NAMES = ('tau_plus', 'tau_minus', 'tau_x', 'tau_y')

    # noinspection PyPep8Naming
    def __init__(
            self, tau_plus: float, tau_minus: float,
            tau_x: float, tau_y: float, A_plus: float, A_minus: float):
        r"""
        :param tau_plus: :math:`\tau_+`
        :param tau_minus: :math:`\tau_-`
        :param tau_x: :math:`\tau_x`
        :param tau_y: :math:`\tau_y`
        :param A_plus: :math:`A^+`
        :param A_minus: :math:`A^-`
        """
        super().__init__(SynapseStructureWeightOnly())
        self.__tau_plus = tau_plus
        self.__tau_minus = tau_minus
        self.__tau_x = tau_x
        self.__tau_y = tau_y
        self.__a_plus = A_plus
        self.__a_minus = A_minus

        ts = SpynnakerDataView.get_simulation_time_step_ms()
        self.__tau_plus_data = get_exp_lut_array(ts, self.__tau_plus)
        self.__tau_minus_data = get_exp_lut_array(ts, self.__tau_minus)
        self.__tau_x_data = get_exp_lut_array(ts, self.__tau_x, shift=2)
        self.__tau_y_data = get_exp_lut_array(ts, self.__tau_y, shift=2)

    @property
    def tau_plus(self) -> float:
        r"""
        :math:`\tau_+`
        """
        return self.__tau_plus

    @property
    def tau_minus(self) -> float:
        r"""
        :math:`\tau_-`
        """
        return self.__tau_minus

    @property
    def tau_x(self) -> float:
        r"""
        :math:`\tau_x`
        """
        return self.__tau_x

    @property
    def tau_y(self) -> float:
        r"""
        :math:`\tau_y`
        """
        return self.__tau_y

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
        if not isinstance(
                timing_dependence, TimingDependencePfisterSpikeTriplet):
            return False
        return (
            (self.__tau_plus == timing_dependence.tau_plus) and
            (self.__tau_minus == timing_dependence.tau_minus) and
            (self.__tau_x == timing_dependence.tau_x) and
            (self.__tau_y == timing_dependence.tau_y))

    @property
    def vertex_executable_suffix(self) -> str:
        """
        The suffix to be appended to the vertex executable for this rule.
        """
        return "pfister_triplet"

    @property
    def pre_trace_n_bytes(self) -> int:
        """
        The number of bytes used by the pre-trace of the rule per neuron.
        """
        # Triplet rule trace entries consists of two 16-bit traces - R1 and R2
        # (Note: this is the pre-trace size, not the post-trace size)
        return BYTES_PER_SHORT * 2

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self) -> int:
        lut_array_words = (
            len(self.__tau_plus_data) + len(self.__tau_minus_data) +
            len(self.__tau_x_data) + len(self.__tau_y_data))
        return lut_array_words * BYTES_PER_WORD

    @property
    def n_weight_terms(self) -> int:
        """
        The number of weight terms expected by this timing rule.
        """
        return 2

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationBase, global_weight_scale: float,
            synapse_weight_scales: NDArray[floating]) -> None:
        # Write lookup tables
        spec.write_array(self.__tau_plus_data)
        spec.write_array(self.__tau_minus_data)
        spec.write_array(self.__tau_x_data)
        spec.write_array(self.__tau_y_data)

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        return self.__PARAM_NAMES
