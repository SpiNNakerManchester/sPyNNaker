# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pyNN.random import NumpyRNG
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine)


class SynapseInformation(object):
    """ Contains the synapse information including the connector, synapse type\
        and synapse dynamics
    """
    __slots__ = [
        "__connector",
        "__pre_population",
        "__post_population",
        "__prepop_is_view",
        "__postpop_is_view",
        "__rng",
        "__synapse_dynamics",
        "__synapse_type",
        "__is_virtual_machine",
        "__weights",
        "__delays",
        "__pre_run_connection_holders"]

    def __init__(self, connector, pre_population, post_population,
                 prepop_is_view, postpop_is_view, rng,
                 synapse_dynamics, synapse_type, is_virtual_machine,
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
        :param rng: Seeded random number generator
        :type rng: ~pyNN.random.NumpyRNG or None
        :param AbstractSynapseDynamics synapse_dynamics:
            The dynamic behaviour of the synapse
        :param AbstractSynapseType synapse_type: The type of the synapse
        :param bool is_virtual_machine: Whether the machine is virtual
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
        self.__rng = (rng or NumpyRNG())
        self.__synapse_dynamics = synapse_dynamics
        self.__synapse_type = synapse_type
        self.__weights = weights
        self.__delays = delays
        self.__is_virtual_machine = is_virtual_machine

        # Make a list of holders to be updated
        self.__pre_run_connection_holders = list()

    @property
    def connector(self):
        """ The connector connected to the synapse

        :rtype: AbstractConnector
        """
        return self.__connector

    @property
    def pre_population(self):
        """ The population sending spikes to the synapse

        :rtype: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
        """
        return self.__pre_population

    @property
    def post_population(self):
        """ The population hosting the synapse

        :rtype: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
        """
        return self.__post_population

    @property
    def n_pre_neurons(self):
        """ The number of neurons in the prepopulation

        :rtype: int
        """
        return self.__pre_population.size

    @property
    def n_post_neurons(self):
        """ The number of neurons in the postpopulation

        :rtype: int
        """
        return self.__post_population.size

    @property
    def prepop_is_view(self):
        """ Whether the :py:meth:`pre_population` is a view

        :rtype: bool
        """
        return self.__prepop_is_view

    @property
    def postpop_is_view(self):
        """ Whether the :py:meth:`post_population` is a view

        :rtype: bool
        """
        return self.__postpop_is_view

    @property
    def rng(self):
        """ Random number generator

        :rtype: ~pyNN.random.NumpyRNG
        """
        return self.__rng

    @property
    def synapse_dynamics(self):
        """ The dynamic behaviour of the synapse

        :rtype: AbstractSynapseDynamics
        """
        return self.__synapse_dynamics

    @property
    def synapse_type(self):
        """ The type of the synapse

        :rtype: AbstractSynapseType
        """
        return self.__synapse_type

    @property
    def weights(self):
        """ The synaptic weights (if any)

        :rtype: float or list(float) or ~numpy.ndarray(float) or None
        """
        return self.__weights

    @property
    def delays(self):
        """ The total synaptic delays (if any)

        :rtype: float or list(float) or ~numpy.ndarray(float) or None
        """
        return self.__delays

    def may_generate_on_machine(self):
        """ Do we describe a collection of synapses whose synaptic matrix may\
            be generated on SpiNNaker instead of needing to be calculated in\
            this process and uploaded? This depends on the connector, the\
            definitions of the weights and delays, and the dynamics of the\
            synapses.

        :return: True if the synaptic matrix may be generated on machine (or
            may have already been so done)
        :rtype: bool
        """
        # If we are using a virtual machine, we can't generate on the machine
        if self.__is_virtual_machine:
            return False
        connector_gen = (
            isinstance(self.connector, AbstractGenerateConnectorOnMachine) and
            self.connector.generate_on_machine(self.weights, self.delays))
        synapse_gen = (
            isinstance(self.synapse_dynamics, AbstractGenerateOnMachine) and
            self.synapse_dynamics.generate_on_machine())
        return connector_gen and synapse_gen

    @property
    def pre_run_connection_holders(self):
        """ The list of connection holders to be filled in before run

        :rtype: list(ConnectionHolder)
        """
        return self.__pre_run_connection_holders

    def add_pre_run_connection_holder(self, pre_run_connection_holder):
        """ Add a connection holder that will be filled in before run

        :param ConnectionHolder pre_run_connection_holder:
            The connection holder to be added
        """
        self.__pre_run_connection_holders.append(pre_run_connection_holder)

    def finish_connection_holders(self):
        """ Finish all the connection holders, and clear the list so that they
            are not generated again later
        """
        for holder in self.__pre_run_connection_holders:
            holder.finish()
        del self.__pre_run_connection_holders[:]
