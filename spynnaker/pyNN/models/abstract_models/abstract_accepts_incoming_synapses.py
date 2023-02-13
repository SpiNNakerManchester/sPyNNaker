# Copyright (c) 2016-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.application import ApplicationVertex


@require_subclass(ApplicationVertex)
class AbstractAcceptsIncomingSynapses(object, metaclass=AbstractBase):
    """ Indicates an application vertex that can be a post-vertex in a PyNN\
        projection.

    .. note::
        See :py:meth:`verify_splitter`
    """
    __slots__ = ()

    @abstractmethod
    def get_synapse_id_by_target(self, target):
        """ Get the ID of a synapse given the name.

        :param str target: The name of the synapse
        :rtype: int
        """

    @abstractmethod
    def set_synapse_dynamics(self, synapse_dynamics):
        """ Set the synapse dynamics of this vertex.

        :param AbstractSynapseDynamics synapse_dynamics:
        """

    @abstractmethod
    def get_connections_from_machine(self, app_edge, synapse_info):
        # pylint: disable=too-many-arguments
        """ Get the connections from the machine post-run.

        :param ProjectionApplicationEdge app_edge:
            The edge for which the data is being read
        :param SynapseInformation synapse_info:
            The specific projection within the edge
        """

    @abstractmethod
    def clear_connection_cache(self):
        """ Clear the connection data stored in the vertex so far.
        """

    def verify_splitter(self, splitter):
        """
        Check that the splitter implements the API(s) expected by the\
        SynapticMatrices

        Any Vertex that implements this api should override
        ApplicationVertex.splitter method to also call this function

        :param splitter: the splitter
        :type splitter:
            ~spynnaker.pyNN.extra_algorithms.splitter_components.AbstractSpynnakerSplitterDelay
        :raises PacmanConfigurationException: if the splitter is not an
            instance of AbstractSpynnakerSplitterDelay
        """
        # Delayed import to avoid cicular dependency
        from spynnaker.pyNN.extra_algorithms.splitter_components import (
            AbstractSpynnakerSplitterDelay)
        if not isinstance(splitter, AbstractSpynnakerSplitterDelay):
            raise PacmanConfigurationException(
                "The splitter needs to be an instance of "
                "----------------AbstractSpynnakerSplitterDelay")
