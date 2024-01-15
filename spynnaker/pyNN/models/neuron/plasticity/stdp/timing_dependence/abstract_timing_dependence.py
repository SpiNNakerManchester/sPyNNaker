# Copyright (c) 2015 The University of Manchester
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
from numpy import floating
from numpy.typing import NDArray
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_front_end_common.interface.ds import DataSpecificationBase
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractHasParameterNames)
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    AbstractSynapseStructure)


class AbstractTimingDependence(
        AbstractHasParameterNames, metaclass=AbstractBase):
    """
    An STDP timing dependence rule.
    """
    __slots__ = ("__synapse_structure", )

    def __init__(self, synapse_structure: AbstractSynapseStructure):
        """
        :param synapse_structure:
            The synaptic structure of the plastic part of the rows.
        """
        self.__synapse_structure = synapse_structure

    @abstractmethod
    def is_same_as(
            self, timing_dependence: 'AbstractTimingDependence') -> bool:
        """
        Determine if this timing dependence is the same as another.

        :param AbstractTimingDependence timing_dependence:
        :rtype: bool
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def vertex_executable_suffix(self) -> str:
        """
        The suffix to be appended to the vertex executable for this rule.

        :rtype: str
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def pre_trace_n_bytes(self) -> int:
        """
        The number of bytes used by the pre-trace of the rule per neuron.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self) -> int:
        """
        Get the amount of SDRAM used by the parameters of this rule.

        :rtype: int
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def n_weight_terms(self) -> int:
        """
        The number of weight terms expected by this timing rule.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def write_parameters(
            self, spec: DataSpecificationBase, global_weight_scale: float,
            synapse_weight_scales: NDArray[floating]):
        """
        Write the parameters of the rule to the spec.

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param float global_weight_scale: The weight scale applied globally
        :param list(float) synapse_weight_scales:
            The total weight scale applied to each synapse including the global
            weight scale
        """
        raise NotImplementedError

    @property
    def synaptic_structure(self) -> AbstractSynapseStructure:
        """
        The synaptic structure of the plastic part of the rows.

        :rtype: AbstractSynapseStructure
        """
        return self.__synapse_structure

    @property
    @abstractmethod
    def A_plus(self):
        r"""
        :math:`A^+`

        :rtype: float
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def A_minus(self):
        r"""
        :math:`A^-`

        :rtype: float
        """
        raise NotImplementedError
