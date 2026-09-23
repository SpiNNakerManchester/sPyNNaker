# Copyright (c) 2019 The University of Manchester
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

import logging

from numpy import floating
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataSpecificationBase
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightOnly)
from .abstract_timing_dependence import AbstractTimingDependence

logger = logging.getLogger(__name__)


class TimingDependenceEprop(AbstractTimingDependence):
    """ Timing dependence for e-prop learning rule.
    """

    __slots__ = [
        "__a_minus",
        "__a_plus"
    ]

    def __init__(self, A_plus: float = 0.01,
                 A_minus: float = 0.01) -> None:
        """ Timing dependence for e-prop learning rule.

        :param A_plus:
            The height of the STDP curve for pre-before-post spike pair.
        :param A_minus:
            The height of the STDP curve for post-before-pre spike pair.
        """

        self.__a_plus = A_plus
        self.__a_minus = A_minus

        super().__init__(SynapseStructureWeightOnly())

    @property
    def A_plus(self) -> float:
        """ The height of the STDP curve for pre-before-post spike pair. """
        return self.__a_plus

    @A_plus.setter
    def A_plus(self, new_value: float) -> None:
        """ Set the height of the STDP curve for pre-before-post spike pair.
        """
        self.__a_plus = new_value

    @property
    def A_minus(self) -> float:
        """ The height of the STDP curve for post-before-pre spike pair. """
        return self.__a_minus

    @A_minus.setter
    def A_minus(self, new_value: float) -> None:
        """ Set the height of the STDP curve for post-before-pre spike pair.
        """
        self.__a_minus = new_value

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence: AbstractTimingDependence) -> bool:
        return isinstance(timing_dependence, TimingDependenceEprop)

    @property
    @overrides(AbstractTimingDependence.vertex_executable_suffix)
    def vertex_executable_suffix(self) -> str:
        return "eprop"

    @property
    @overrides(AbstractTimingDependence.pre_trace_n_bytes)
    def pre_trace_n_bytes(self) -> int:
        return 2

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self) -> int:
        return 0

    @property
    @overrides(AbstractTimingDependence.n_weight_terms)
    def n_weight_terms(self) -> int:
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationBase, global_weight_scale: float,
            synapse_weight_scales: NDArray[floating]) -> None:
        # There are currently no parameters to write for this rule
        pass

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self) -> list[str]:
        return []
