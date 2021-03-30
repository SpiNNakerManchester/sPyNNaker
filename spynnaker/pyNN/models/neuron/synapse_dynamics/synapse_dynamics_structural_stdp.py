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

import numpy
from pyNN.standardmodels.synapses import StaticSynapse
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.utilities.utility_calls import create_mars_kiss_seeds
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .synapse_dynamics_structural_common import (
    DEFAULT_F_REW, DEFAULT_INITIAL_WEIGHT, DEFAULT_INITIAL_DELAY,
    DEFAULT_S_MAX, SynapseDynamicsStructuralCommon)


class SynapseDynamicsStructuralSTDP(
        SynapseDynamicsSTDP, SynapseDynamicsStructuralCommon):
    """ Class that enables synaptic rewiring in the presence of STDP.

        It acts as a wrapper around SynapseDynamicsSTDP, meaning rewiring can\
        operate in parallel with STDP synapses.

        Written by Petrut Bogdan.
    """
    __slots__ = [
        # Frequency of rewiring (Hz)
        "__f_rew",
        # Period of rewiring (ms)
        "__p_rew",
        # Initial weight assigned to a newly formed connection
        "__initial_weight",
        # Delay assigned to a newly formed connection
        "__initial_delay",
        # Maximum fan-in per target layer neuron
        "__s_max",
        # The seed
        "__seed",
        # Holds initial connectivity as defined via connector
        "__connections",
        # Maximum synaptic row length for created synapses
        "__actual_row_max_length",
        # The actual type of weights: static through the simulation or those
        # that can be change through STDP
        "__weight_dynamics",
        # Shared RNG seed to be written on all cores
        "__seeds",
        # Stores the actual SDRAM usage (value obtained only after writing spec
        # is finished)
        "__actual_sdram_usage",
        # The RNG used with the seed that is passed in
        "__rng",
        # The partner selection rule
        "__partner_selection",
        # The formation rule
        "__formation",
        # The elimination rule
        "__elimination"
    ]

    def __init__(
            self, partner_selection, formation, elimination,
            timing_dependence=None, weight_dependence=None,
            voltage_dependence=None, dendritic_delay_fraction=1.0,
            f_rew=DEFAULT_F_REW, initial_weight=DEFAULT_INITIAL_WEIGHT,
            initial_delay=DEFAULT_INITIAL_DELAY, s_max=DEFAULT_S_MAX,
            with_replacement=True, seed=None,
            weight=StaticSynapse.default_parameters['weight'], delay=None,
            backprop_delay=True):
        """
        :param AbstractPartnerSelection partner_selection:
            The partner selection rule
        :param AbstractFormation formation: The formation rule
        :param AbstractElimination elimination: The elimination rule
        :param AbstractTimingDependence timing_dependence:
            The STDP timing dependence rule
        :param AbstractWeightDependence weight_dependence:
            The STDP weight dependence rule
        :param None voltage_dependence:
            The STDP voltage dependence (unsupported)
        :param float dendritic_delay_fraction:
            The STDP dendritic delay fraction
        :param float f_rew:
            How many rewiring attempts will be done per second.
        :param float initial_weight:
            Weight assigned to a newly formed connection
        :param initial_delay:
            Delay assigned to a newly formed connection; a single value means
            a fixed delay value, or a tuple of two values means the delay will
            be chosen at random from a uniform distribution between the given
            values
        :type initial_delay: float or tuple(float, float)
        :param int s_max: Maximum fan-in per target layer neuron
        :param bool with_replacement:
            If set to True (default), a new synapse can be formed in a
            location where a connection already exists; if False, then it must
            form where no connection already exists
        :param seed: seed for the random number generators
        :type seed: int or None
        :param float weight: The weight of connections formed by the connector
        :param delay: The delay of connections formed by the connector
            Use ``None`` to get the simulator default minimum delay.
        :type delay: float or None
        """
        super().__init__(
            timing_dependence, weight_dependence, voltage_dependence,
            dendritic_delay_fraction, weight, delay, pad_to_length=s_max,
            backprop_delay=backprop_delay)
        self.__partner_selection = partner_selection
        self.__formation = formation
        self.__elimination = elimination
        self.__f_rew = float(f_rew)
        self.__p_rew = 1. / self.__f_rew
        self.__initial_weight = initial_weight
        self.__initial_delay = initial_delay
        self.__s_max = s_max
        self.__with_replacement = with_replacement
        self.__seed = seed
        self.__connections = dict()

        self.__actual_row_max_length = self.__s_max

        self.__rng = numpy.random.RandomState(seed)
        self.__seeds = dict()

        # Addition information -- used for SDRAM usage
        self.__actual_sdram_usage = dict()

    @overrides(SynapseDynamicsSTDP.merge)
    def merge(self, synapse_dynamics):
        # If other is structural, check structural matches
        if isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
            if not SynapseDynamicsStructuralCommon.is_same_as(
                    self, synapse_dynamics):
                raise SynapticConfigurationException(
                    "Synapse dynamics must match exactly when using multiple"
                    " edges to the same population")
        # If other is STDP, check STDP matches
        if isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            if not SynapseDynamicsSTDP.is_same_as(self, synapse_dynamics):
                raise SynapticConfigurationException(
                    "Synapse dynamics must match exactly when using multiple"
                    " edges to the same population")

        # If everything matches, return ourselves as supreme!
        return self

    def set_projection_parameter(self, param, value):
        """
        :param str param:
        :param value:
       """
        for item in (self.partner_selection, self.__formation,
                     self.__elimination):
            if hasattr(item, param):
                setattr(item, param, value)
                break
        else:
            raise Exception("Unknown parameter {}".format(param))

    @overrides(SynapseDynamicsSTDP.is_same_as)
    def is_same_as(self, synapse_dynamics):
        if (isinstance(synapse_dynamics, SynapseDynamicsSTDP) and
                not super().is_same_as(synapse_dynamics)):
            return False
        return SynapseDynamicsStructuralCommon.is_same_as(
            self, synapse_dynamics)

    @overrides(SynapseDynamicsSTDP.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        return (super().get_vertex_executable_suffix() +
                SynapseDynamicsStructuralCommon.get_vertex_executable_suffix(
                    self))

    @overrides(SynapseDynamicsSTDP.get_n_words_for_plastic_connections)
    def get_n_words_for_plastic_connections(self, n_connections):
        value = super().get_n_words_for_plastic_connections(n_connections)
        self.__actual_row_max_length = value
        return value

    @overrides(AbstractSynapseDynamicsStructural.set_connections)
    def set_connections(
            self, connections, post_vertex_slice, app_edge, synapse_info,
            machine_edge):
        if not isinstance(synapse_info.synapse_dynamics,
                          AbstractSynapseDynamicsStructural):
            return
        collector = self.__connections.setdefault(
            (app_edge.post_vertex, post_vertex_slice.lo_atom), [])
        collector.append(
            (connections, app_edge, machine_edge, synapse_info))

    @overrides(SynapseDynamicsSTDP.get_parameter_names)
    def get_parameter_names(self):
        names = super().get_parameter_names()
        names.extend(SynapseDynamicsStructuralCommon.get_parameter_names(self))
        return names

    @property
    @overrides(AbstractSynapseDynamicsStructural.f_rew)
    def f_rew(self):
        return self.__f_rew

    @property
    @overrides(AbstractSynapseDynamicsStructural.s_max)
    def s_max(self):
        return self.__s_max

    @property
    @overrides(AbstractSynapseDynamicsStructural.with_replacement)
    def with_replacement(self):
        return self.__with_replacement

    @property
    @overrides(AbstractSynapseDynamicsStructural.seed)
    def seed(self):
        return self.__seed

    @property
    @overrides(AbstractSynapseDynamicsStructural.initial_weight)
    def initial_weight(self):
        return self.__initial_weight

    @property
    @overrides(AbstractSynapseDynamicsStructural.initial_delay)
    def initial_delay(self):
        return self.__initial_delay

    @property
    @overrides(AbstractSynapseDynamicsStructural.partner_selection)
    def partner_selection(self):
        return self.__partner_selection

    @property
    @overrides(AbstractSynapseDynamicsStructural.formation)
    def formation(self):
        return self.__formation

    @property
    @overrides(AbstractSynapseDynamicsStructural.elimination)
    def elimination(self):
        return self.__elimination

    @property
    @overrides(SynapseDynamicsStructuralCommon.connections)
    def connections(self):
        return self.__connections

    @overrides(SynapseDynamicsSTDP.get_weight_mean)
    def get_weight_mean(self, connector, synapse_info):
        return self.get_weight_maximum(connector, synapse_info)

    @overrides(SynapseDynamicsSTDP.get_weight_maximum)
    def get_weight_maximum(self, connector, synapse_info):
        w_max = super().get_weight_maximum(connector, synapse_info)
        return max(w_max, self.__initial_weight)

    @overrides(SynapseDynamicsStructuralCommon.get_seeds)
    def get_seeds(self, app_vertex=None):
        if app_vertex:
            if app_vertex not in self.__seeds.keys():
                self.__seeds[app_vertex] = (
                    create_mars_kiss_seeds(self.__rng, self.__seed))
            return self.__seeds[app_vertex]
        else:
            return create_mars_kiss_seeds(self.__rng, self.__seed)

    @overrides(SynapseDynamicsSTDP.generate_on_machine)
    def generate_on_machine(self):
        # Never generate structural connections on the machine
        return False
