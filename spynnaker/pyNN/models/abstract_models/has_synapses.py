# Copyright (c) 2020 The University of Manchester
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
from typing import Sequence, TYPE_CHECKING

from numpy.typing import NDArray

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.model.placements import Placement

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)


class HasSynapses(object, metaclass=AbstractBase):
    """
    API for getting connections from the machine.
    """
    @abstractmethod
    def get_connections_from_machine(
            self, placement: Placement, app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> Sequence[NDArray]:
        """
        :param placement: Where the connection data is on the machine
        :param app_edge: The edge for which the data is being read
        :param synapse_info: The specific projection within the edge
        :returns: The connections from the machine for this vertex.
        """
        raise NotImplementedError
