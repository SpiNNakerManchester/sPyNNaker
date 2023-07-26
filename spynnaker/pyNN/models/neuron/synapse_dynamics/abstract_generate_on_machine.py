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
from __future__ import annotations
from enum import Enum
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from numpy import uint32
from numpy.typing import NDArray
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.neuron.synapse_io import MaxRowInfo


class MatrixGeneratorID(Enum):
    STATIC_MATRIX = 0
    STDP_MATRIX = 1
    NEUROMODULATION_MATRIX = 2


class AbstractGenerateOnMachine(object, metaclass=AbstractBase):
    """
    A synapse dynamics that can be generated on the machine.
    """
    __slots__ = ()

    def generate_on_machine(self) -> bool:
        """
        Determines if this instance should be generated on the machine.

        Default implementation returns True

        :rtype: bool
        """
        return True

    @property
    @abstractmethod
    def gen_matrix_id(self) -> int:
        """
        The ID of the on-machine matrix generator.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def gen_matrix_params(
            self, synaptic_matrix_offset: int, delayed_matrix_offset: int,
            app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation, max_row_info: MaxRowInfo,
            max_pre_atoms_per_core: int, max_post_atoms_per_core: int
            ) -> NDArray[uint32]:
        """
        Any parameters required by the matrix generator.

        :rtype: ~numpy.ndarray(uint32)
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def gen_matrix_params_size_in_bytes(self) -> int:
        """
        The size of the parameters of the matrix generator in bytes.

        :rtype: int
        """
        raise NotImplementedError
