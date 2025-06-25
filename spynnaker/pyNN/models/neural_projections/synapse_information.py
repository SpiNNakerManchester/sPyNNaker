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

from __future__ import annotations
from typing import List, Sequence, TYPE_CHECKING, Union, Optional
from spinn_utilities.config_holder import get_config_bool
from pacman.model.graphs.application import ApplicationVertex
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector, AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine)
from spynnaker.pyNN.types import (DELAYS, WEIGHTS)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
if TYPE_CHECKING:
    from spynnaker.pyNN.models.populations import Population, PopulationView
    from spynnaker.pyNN.models.neuron import ConnectionHolder
    from spynnaker.pyNN.models.neuron.synapse_dynamics import (
        AbstractSynapseDynamics)


class SynapseInformation(object):
    """
    Contains the synapse information including the connector, synapse type
    and synapse dynamics.
    """
    # Made by a Projection
    __slots__ = (
        "__connector",
        "__pre_population",
        "__post_population",
        "__prepop_is_view",
        "__postpop_is_view",
        "__synapse_dynamics",
        "__synapse_type",
        "__receptor_type",
        "__weights",
        "__delays",
        "__pre_run_connection_holders",
        "__synapse_type_from_dynamics",
        "__download_on_pause",
        "__partition_id")

    def __init__(self, connector: AbstractConnector,
                 pre_population: Union[Population, PopulationView],
                 post_population: Union[Population, PopulationView],
                 prepop_is_view: bool, postpop_is_view: bool,
                 synapse_dynamics: AbstractSynapseDynamics,
                 synapse_type: int, receptor_type: str,
                 synapse_type_from_dynamics: bool,
                 weights: WEIGHTS = None,
                 delays: DELAYS = None,
                 download_on_pause: bool = False,
                 partition_id: Optional[str] = None):
        """
        :param connector: The connector connected to the synapse
        :param pre_population: The population sending spikes to the synapse
        :param post_population: The population hosting the synapse
        :param prepop_is_view: Whether the ``pre_population`` is a view
        :param postpop_is_view: Whether the ``post_population`` is a view
        :param synapse_dynamics: The dynamic behaviour of the synapse
        :param synapse_type: The type of the synapse
        :param receptor_type: Description of the receptor (e.g. excitatory)
        :param synapse_type_from_dynamics:
            Whether the synapse type came from synapse dynamics
        :param weights: The synaptic weights
        :param delays: The total synaptic delays
        :param bool download_on_pause:
            Whether to download the synapse matrix when the simulation pauses
        :param partition_id:
            The partition id for the application edge when not standard; if
            None, the standard SPIKE_PARTITION_ID is used
        """
        self.__connector = connector
        self.__pre_population = pre_population
        self.__post_population = post_population
        self.__prepop_is_view = prepop_is_view
        self.__postpop_is_view = postpop_is_view
        self.__synapse_dynamics = synapse_dynamics
        self.__synapse_type = synapse_type
        self.__receptor_type = receptor_type
        assert (delays is not None)
        self.__weights = weights
        self.__delays = delays
        self.__synapse_type_from_dynamics = synapse_type_from_dynamics
        self.__download_on_pause = download_on_pause
        self.__partition_id = partition_id or SPIKE_PARTITION_ID

        # Make a list of holders to be updated
        self.__pre_run_connection_holders: List[ConnectionHolder] = list()

    @property
    def connector(self) -> AbstractConnector:
        """
        The connector connected to the synapse.
        """
        return self.__connector

    @property
    def pre_population(self) -> Union[Population, PopulationView]:
        """
        The population sending spikes to the synapse.
        """
        return self.__pre_population

    @property
    def post_population(self) -> Union[Population, PopulationView]:
        """
        The population hosting the synapse.
        """
        return self.__post_population

    @property
    def pre_vertex(self) -> ApplicationVertex:
        """
        The vertex sending spikes to the synapse.
        """
        # pylint: disable=protected-access
        return self.__pre_population._vertex

    @property
    def post_vertex(self) -> ApplicationVertex:
        """
        The vertex hosting the synapse.
        """
        # pylint: disable=protected-access
        return self.__post_population._vertex

    @property
    def n_pre_neurons(self) -> int:
        """
        The number of neurons in the pre-population.
        """
        return self.__pre_population.size

    @property
    def n_post_neurons(self) -> int:
        """
        The number of neurons in the post-population.
        """
        return self.__post_population.size

    @property
    def prepop_is_view(self) -> bool:
        """
        Whether the :py:meth:`pre_population` is a view.
        """
        return self.__prepop_is_view

    @property
    def postpop_is_view(self) -> bool:
        """
        Whether the :py:meth:`post_population` is a view.
        """
        return self.__postpop_is_view

    @property
    def synapse_dynamics(self) -> AbstractSynapseDynamics:
        """
        The dynamic behaviour of the synapse.
        """
        return self.__synapse_dynamics

    @property
    def synapse_type(self) -> int:
        """
        The type of the synapse. An index into the set of synapse types
        supported by a neuron.
        """
        return self.__synapse_type

    @property
    def receptor_type(self) -> str:
        """
        A string representing the receptor type.
        """
        return self.__receptor_type

    @property
    def weights(self) -> WEIGHTS:
        """
        The synaptic weights (if any).
        """
        return self.__weights

    @property
    def delays(self) -> DELAYS:
        """
        The total synaptic delays (if any).
        """
        return self.__delays

    def may_generate_on_machine(self) -> bool:
        """
        Do we describe a collection of synapses whose synaptic matrix may
        be generated on SpiNNaker instead of needing to be calculated in
        this process and uploaded? This depends on the connector, the
        definitions of the weights and delays, and the dynamics of the
        synapses.

        :return: True if the synaptic matrix may be generated on machine (or
            may have already been so done)
        """
        # If we are using a virtual machine, we can't generate on the machine
        if get_config_bool("Machine", "virtual_board"):
            return False
        connector_gen = (
            isinstance(self.connector, AbstractGenerateConnectorOnMachine) and
            self.connector.generate_on_machine(self))
        synapse_gen = (
            isinstance(self.synapse_dynamics, AbstractGenerateOnMachine) and
            self.synapse_dynamics.generate_on_machine())
        return connector_gen and synapse_gen

    @property
    def pre_run_connection_holders(self) -> Sequence[ConnectionHolder]:
        """
        The list of connection holders to be filled in before run.
        """
        return self.__pre_run_connection_holders

    def add_pre_run_connection_holder(
            self, pre_run_connection_holder: ConnectionHolder) -> None:
        """
        Add a connection holder that will be filled in before run.

        :param pre_run_connection_holder:
            The connection holder to be added
        """
        self.__pre_run_connection_holders.append(pre_run_connection_holder)

    def finish_connection_holders(self) -> None:
        """
        Finish all the connection holders, and clear the list so that they
        are not generated again later.
        """
        for holder in self.__pre_run_connection_holders:
            holder.finish()
        del self.__pre_run_connection_holders[:]

    @property
    def synapse_type_from_dynamics(self) -> bool:
        """
        Whether the synapse type comes from the synapse dynamics.
        """
        return self.__synapse_type_from_dynamics

    @property
    def download_on_pause(self) -> bool:
        """
        Whether to download the synapse matrix when the simulation pauses.
        """
        return self.__download_on_pause

    @download_on_pause.setter
    def download_on_pause(self, download_on_pause: bool) -> None:
        """
        Set whether to download the synapse matrix when the simulation pauses.

        :param download_on_pause:
            Whether to download the synapse matrix when the simulation pauses
        """
        self.__download_on_pause = download_on_pause

    @property
    def partition_id(self) -> str:
        """
        The partition id for the application edge
        """
        return self.__partition_id
