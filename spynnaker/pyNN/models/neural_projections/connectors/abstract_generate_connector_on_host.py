# Copyright (c) 2021 The University of Manchester
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
from typing import List, Tuple, TYPE_CHECKING
from numpy.typing import NDArray
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.model.graphs.common import Slice
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import SynapseInformation


class AbstractGenerateConnectorOnHost(object, metaclass=AbstractBase):
    """
    A connector that can be generated on host.
    """

    # Mix-in class, so don't add anything here!
    __slots__: Tuple[str, ...] = ()

    @abstractmethod
    def create_synaptic_block(
            self, post_slices: List[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        """
        Create a synaptic block from the data.

        :param list(~pacman.model.graphs.common.Slice) post_slices:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param AbstractSynapseType synapse_type:
        :param SynapseInformation synapse_info:
        :returns:
            The synaptic matrix data to go to the machine, as a Numpy array
        :rtype: ~numpy.ndarray
        """
        raise NotImplementedError
