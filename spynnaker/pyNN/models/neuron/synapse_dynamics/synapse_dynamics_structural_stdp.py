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

from spinn_utilities.overrides import overrides
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from .synapse_dynamics_structural_common import (
    SynapseDynamicsStructuralCommon as
    CommonSP)
from spynnaker.pyNN.exceptions import SynapticConfigurationException


class SynapseDynamicsStructuralSTDP(
        SynapseDynamicsSTDP, AbstractSynapseDynamicsStructural):
    """ Class that enables synaptic rewiring in the presence of STDP.

        It acts as a wrapper around SynapseDynamicsSTDP, meaning rewiring can\
        operate in parallel with STDP synapses.

        Written by Petrut Bogdan.


    :param partner_selection: The partner selection rule
    :param formation: The formation rule
    :param elimination: The elimination rule
    :param timing_dependence: The STDP timing dependence
    :param weight_dependence: The STDP weight dependence
    :param voltage_dependence: The STDP voltage dependence
    :param dendritic_delay_fraction: The STDP dendritic delay fraction
    :param f_rew: How many rewiring attempts will be done per second.
    :type f_rew: int
    :param initial_weight: Weight assigned to a newly formed connection
    :type initial_weight: float
    :param initial_delay:\
        Delay assigned to a newly formed connection; a single value means a\
        fixed delay value, or a tuple of two values means the delay will be\
        chosen at random from a uniform distribution between the given values
    :type initial_delay: float or (float, float)
    :param s_max: Maximum fan-in per target layer neuron
    :type s_max: int
    :param seed: seed the random number generators
    :type seed: int
    :param weight: The weight of connections formed by the connector
    :param delay: The delay of connections formed by the connector
    """
    __slots__ = ["__common_sp"]

    def __init__(
            self, partner_selection, formation, elimination,
            timing_dependence=None, weight_dependence=None,
            voltage_dependence=None, dendritic_delay_fraction=1.0,
            f_rew=CommonSP.DEFAULT_F_REW,
            initial_weight=CommonSP.DEFAULT_INITIAL_WEIGHT,
            initial_delay=CommonSP.DEFAULT_INITIAL_DELAY,
            s_max=CommonSP.DEFAULT_S_MAX, seed=None,
            weight=0.0, delay=1.0, backprop_delay=True):
        super(SynapseDynamicsStructuralSTDP, self).__init__(
            timing_dependence, weight_dependence, voltage_dependence,
            dendritic_delay_fraction, weight, delay, pad_to_length=s_max,
            backprop_delay=backprop_delay)
        self.__common_sp = CommonSP(
            partner_selection, formation, elimination, f_rew, initial_weight,
            initial_delay, s_max, seed)

    @overrides(SynapseDynamicsSTDP.merge)
    def merge(self, synapse_dynamics):
        # If other is structural, check structural matches
        if isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
            if not self.__common_sp.is_same_as(synapse_dynamics):
                raise SynapticConfigurationException(
                    "Synapse dynamics must match exactly when using multiple"
                    " edges to the same population")
        # If other is STDP, check STDP matches
        if isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            if not super(SynapseDynamicsStructuralSTDP, self).is_same_as(
                    synapse_dynamics):
                raise SynapticConfigurationException(
                    "Synapse dynamics must match exactly when using multiple"
                    " edges to the same population")

        # If everything matches, return ourselves as supreme!
        return self

    @overrides(AbstractSynapseDynamicsStructural.write_structural_parameters)
    def write_structural_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, app_vertex, post_slice, graph_mapper,
            routing_info, synapse_indices):
        super(SynapseDynamicsStructuralSTDP, self).write_parameters(
            spec, region, machine_time_step, weight_scales)
        self.__common_sp.write_parameters(
            spec, region, machine_time_step, weight_scales, application_graph,
            app_vertex, post_slice, graph_mapper, routing_info,
            synapse_indices)

    def set_projection_parameter(self, param, value):
        self.__common_sp.set_projection_parameter(param, value)

    @overrides(SynapseDynamicsSTDP.is_same_as)
    def is_same_as(self, synapse_dynamics):
        if (isinstance(synapse_dynamics, SynapseDynamicsSTDP) and
                not super(SynapseDynamicsStructuralSTDP, self).is_same_as(
                    synapse_dynamics)):
            return False
        return self.__common_sp.is_same_as(synapse_dynamics)

    @overrides(SynapseDynamicsSTDP.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        name = super(SynapseDynamicsStructuralSTDP,
                     self).get_vertex_executable_suffix()
        name += self.__common_sp.get_vertex_executable_suffix()
        return name

    @overrides(AbstractSynapseDynamicsStructural
               .get_structural_parameters_sdram_usage_in_bytes)
    def get_structural_parameters_sdram_usage_in_bytes(
            self, application_graph, app_vertex, n_neurons, n_synapse_types):
        size = super(SynapseDynamicsStructuralSTDP, self).\
            get_parameters_sdram_usage_in_bytes(n_neurons, n_synapse_types)
        size += self.__common_sp.get_parameters_sdram_usage_in_bytes(
            application_graph, app_vertex, n_neurons)
        return size

    @overrides(SynapseDynamicsSTDP.get_n_words_for_plastic_connections)
    def get_n_words_for_plastic_connections(self, n_connections):
        value = super(SynapseDynamicsStructuralSTDP,
                      self).get_n_words_for_plastic_connections(n_connections)
        self.__common_sp.n_words_for_plastic_connections(value)
        return value

    @overrides(AbstractSynapseDynamicsStructural.set_connections)
    def set_connections(
            self, connections, post_vertex_slice, app_edge, synapse_info,
            machine_edge):
        self.__common_sp.synaptic_data_update(
            connections, post_vertex_slice, app_edge, synapse_info,
            machine_edge)

    @overrides(SynapseDynamicsSTDP.get_parameter_names)
    def get_parameter_names(self):
        names = super(
            SynapseDynamicsStructuralSTDP, self).get_parameter_names()
        names.extend(self.__common_sp.get_parameter_names())
        return names

    @property
    @overrides(AbstractSynapseDynamicsStructural.f_rew)
    def f_rew(self):
        return self.__common_sp.f_rew

    @property
    @overrides(AbstractSynapseDynamicsStructural.s_max)
    def s_max(self):
        return self.__common_sp.s_max

    @property
    @overrides(AbstractSynapseDynamicsStructural.seed)
    def seed(self):
        return self.__common_sp.seed

    @property
    @overrides(AbstractSynapseDynamicsStructural.initial_weight)
    def initial_weight(self):
        return self.__common_sp.initial_weight

    @property
    @overrides(AbstractSynapseDynamicsStructural.initial_delay)
    def initial_delay(self):
        return self.__common_sp.initial_delay

    @property
    @overrides(AbstractSynapseDynamicsStructural.partner_selection)
    def partner_selection(self):
        return self.__common_sp.partner_selection

    @property
    @overrides(AbstractSynapseDynamicsStructural.formation)
    def formation(self):
        return self.__common_sp.formation

    @property
    @overrides(AbstractSynapseDynamicsStructural.elimination)
    def elimination(self):
        return self.__common_sp.elimination

    @overrides(SynapseDynamicsSTDP.get_weight_mean)
    def get_weight_mean(self, connector, synapse_info):
        return self.get_weight_maximum(connector, synapse_info)

    @overrides(SynapseDynamicsSTDP.get_weight_maximum)
    def get_weight_maximum(self, connector, synapse_info):
        w_max = super(SynapseDynamicsStructuralSTDP, self).get_weight_maximum(
            connector, synapse_info)
        return max(w_max, self.__common_sp.initial_weight)
