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

from spinn_utilities.config_holder import get_config_bool
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine)


class SynapseInformation(object):
    """
    Contains the synapse information including the connector, synapse type
    and synapse dynamics.
    """
    __slots__ = [
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
        "__synapse_type_from_dynamics"]

    def __init__(self, connector, pre_population, post_population,
                 prepop_is_view, postpop_is_view, synapse_dynamics,
                 synapse_type, receptor_type, synapse_type_from_dynamics,
                 weights=None, delays=None):
        """
        :param AbstractConnector connector:
            The connector connected to the synapse
        :param pre_population: The population sending spikes to the synapse
        :type pre_population: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
        :param post_population: The population hosting the synapse
        :type post_population: ~spynnaker.pyNN.models.populations.Population
            or ~spynnaker.pyNN.models.populations.PopulationView
        :param bool prepop_is_view: Whether the ``pre_population`` is a view
        :param bool postpop_is_view: Whether the ``post_population`` is a view
        :param AbstractSynapseDynamics synapse_dynamics:
            The dynamic behaviour of the synapse
        :param int synapse_type: The type of the synapse
        :param str receptor_type: Description of the receptor (e.g. excitatory)
        :param bool synapse_type_from_dynamics:
            Whether the synapse type came from synapse dynamics
        :param weights: The synaptic weights
        :type weights: float or list(float) or ~numpy.ndarray(float) or None
        :param delays: The total synaptic delays
        :type delays: float or list(float) or ~numpy.ndarray(float) or None
        """
        self.__connector = connector
        self.__pre_population = pre_population
        self.__post_population = post_population
        self.__prepop_is_view = prepop_is_view
        self.__postpop_is_view = postpop_is_view
        self.__synapse_dynamics = synapse_dynamics
        self.__synapse_type = synapse_type
        self.__receptor_type = receptor_type
        self.__weights = weights
        self.__delays = delays
        self.__synapse_type_from_dynamics = synapse_type_from_dynamics

        # Make a list of holders to be updated
        self.__pre_run_connection_holders = list()

    @property
    def connector(self):
        """
        The connector connected to the synapse.

        :rtype: AbstractConnector
        """
        return self.__connector

    @property
    def pre_population(self):
        """
        The population sending spikes to the synapse.

        :rtype: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
        """
        return self.__pre_population

    @property
    def post_population(self):
        """
        The population hosting the synapse.

        :rtype: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
        """
        return self.__post_population

    @property
    def pre_vertex(self):
        """
        The vertex sending spikes to the synapse.

        :rtype: ApplicationVertex
        """
        return self.__pre_population._vertex

    @property
    def post_vertex(self):
        """
        The vertex hosting the synapse.

        :rtype: ApplicationVertex
        """
        return self.__post_population._vertex

    @property
    def n_pre_neurons(self):
        """
        The number of neurons in the pre-population.

        :rtype: int
        """
        return self.__pre_population.size

    @property
    def n_post_neurons(self):
        """
        The number of neurons in the post-population.

        :rtype: int
        """
        return self.__post_population.size

    @property
    def prepop_is_view(self):
        """
        Whether the :py:meth:`pre_population` is a view.

        :rtype: bool
        """
        return self.__prepop_is_view

    @property
    def postpop_is_view(self):
        """
        Whether the :py:meth:`post_population` is a view.

        :rtype: bool
        """
        return self.__postpop_is_view

    @property
    def synapse_dynamics(self):
        """
        The dynamic behaviour of the synapse.

        :rtype: AbstractSynapseDynamics
        """
        return self.__synapse_dynamics

    @property
    def synapse_type(self):
        """
        The type of the synapse.

        :rtype: int
        """
        return self.__synapse_type

    @property
    def receptor_type(self):
        """
        A string representing the receptor type.

        :rtype: str
        """
        return self.__receptor_type

    @property
    def weights(self):
        """
        The synaptic weights (if any).

        :rtype: float or list(float) or ~numpy.ndarray(float) or None
        """
        return self.__weights

    @property
    def delays(self):
        """
        The total synaptic delays (if any).

        :rtype: float or list(float) or ~numpy.ndarray(float) or None
        """
        return self.__delays

    def may_generate_on_machine(self):
        """
        Do we describe a collection of synapses whose synaptic matrix may
        be generated on SpiNNaker instead of needing to be calculated in
        this process and uploaded? This depends on the connector, the
        definitions of the weights and delays, and the dynamics of the
        synapses.

        :return: True if the synaptic matrix may be generated on machine (or
            may have already been so done)
        :rtype: bool
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
    def pre_run_connection_holders(self):
        """
        The list of connection holders to be filled in before run.

        :rtype: list(ConnectionHolder)
        """
        return self.__pre_run_connection_holders

    def add_pre_run_connection_holder(self, pre_run_connection_holder):
        """
        Add a connection holder that will be filled in before run.

        :param ConnectionHolder pre_run_connection_holder:
            The connection holder to be added
        """
        self.__pre_run_connection_holders.append(pre_run_connection_holder)

    def finish_connection_holders(self):
        """
        Finish all the connection holders, and clear the list so that they
        are not generated again later.
        """
        for holder in self.__pre_run_connection_holders:
            holder.finish()
        del self.__pre_run_connection_holders[:]

    @property
    def synapse_type_from_dynamics(self):
        """
        Whether the synapse type comes from the synapse dynamics.

        :rtype: bool
        """
        return self.__synapse_type_from_dynamics
