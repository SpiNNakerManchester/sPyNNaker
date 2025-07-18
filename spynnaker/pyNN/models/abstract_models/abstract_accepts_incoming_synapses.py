# Copyright (c) 2016 The University of Manchester
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
from typing import Optional, TYPE_CHECKING
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.application import ApplicationVertex
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
        ConnectionsArray)
    from spynnaker.pyNN.models.neuron.synapse_dynamics import (
        AbstractSynapseDynamics)
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.extra_algorithms.splitter_components import (
        AbstractSpynnakerSplitterDelay)


@require_subclass(ApplicationVertex)
class AbstractAcceptsIncomingSynapses(object, metaclass=AbstractBase):
    """
    Indicates an application vertex that can be a post-vertex in a PyNN
    projection.

    .. note::
        See :py:meth:`verify_splitter`
    """
    __slots__ = ()

    @abstractmethod
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        """
        Get the ID of a synapse given the name.

        :param target: The name of the synapse
        """
        raise NotImplementedError

    @abstractmethod
    def set_synapse_dynamics(
            self, synapse_dynamics: AbstractSynapseDynamics) -> None:
        """
        Set the synapse dynamics of this vertex.

        :param synapse_dynamics:
        """
        raise NotImplementedError

    @abstractmethod
    def get_connections_from_machine(
            self, app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> ConnectionsArray:
        """
        Get the connections from the machine post-run.

        :param app_edge:
            The edge for which the data is being read
        :param synapse_info:
            The specific projection within the edge
        """
        raise NotImplementedError

    @abstractmethod
    def clear_connection_cache(self) -> None:
        """
        Clear the connection data stored in the vertex so far.
        """
        raise NotImplementedError

    def verify_splitter(
            self, splitter: AbstractSpynnakerSplitterDelay) -> None:
        """
        Check that the splitter implements the API(s) expected by the
        SynapticMatrices

        Any Vertex that implements this API should override
        `ApplicationVertex.splitter` method to also call this function.

        :param splitter: the splitter
        :raises PacmanConfigurationException: if the splitter is not an
            instance of AbstractSpynnakerSplitterDelay
        """
        # Delayed import to avoid circular dependency
        # pylint: disable=import-outside-toplevel
        from spynnaker.pyNN.extra_algorithms.splitter_components import (
            AbstractSpynnakerSplitterDelay as DelaySplitter)
        if not isinstance(splitter, DelaySplitter):
            raise PacmanConfigurationException(
                "The splitter needs to be an instance of "
                "----------------AbstractSpynnakerSplitterDelay")
