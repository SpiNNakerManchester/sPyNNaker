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
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from .synapse_dynamics_structural_common import (
    SynapseDynamicsStructuralCommon as CommonSP)
from .synapse_dynamics_static import SynapseDynamicsStatic
from .synapse_dynamics_stdp import SynapseDynamicsSTDP
from .synapse_dynamics_structural_stdp import SynapseDynamicsStructuralSTDP
from spynnaker.pyNN.exceptions import SynapticConfigurationException


class SynapseDynamicsStructuralStatic(
        SynapseDynamicsStatic, AbstractSynapseDynamicsStructural):
    """ Class that enables synaptic rewiring in the absence of STDP.

        It acts as a wrapper around SynapseDynamicsStatic, meaning that \
        rewiring can operate in parallel with static synapses.

        Written by Petrut Bogdan.

    :param partner_selection: The partner selection rule
    :param formation: The formation rule
    :param elimination: The elimination rule
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
            f_rew=CommonSP.DEFAULT_F_REW,
            initial_weight=CommonSP.DEFAULT_INITIAL_WEIGHT,
            initial_delay=CommonSP.DEFAULT_INITIAL_DELAY,
            s_max=CommonSP.DEFAULT_S_MAX, seed=None,
            weight=0.0, delay=1.0):

        super(SynapseDynamicsStructuralStatic, self).__init__(
            weight=weight, delay=delay, pad_to_length=s_max)

        self.__common_sp = CommonSP(
            partner_selection, formation, elimination, f_rew, initial_weight,
            initial_delay, s_max, seed)

    @overrides(SynapseDynamicsStatic.merge)
    def merge(self, synapse_dynamics):
        # If the dynamics is structural, check if same as this
        if isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
            if not self.is_same_as(synapse_dynamics):
                raise SynapticConfigurationException(
                    "Synapse dynamics must match exactly when using multiple"
                    " edges to the same population")

            # If structural part matches, return other as it might also be STDP
            return synapse_dynamics

        # If the dynamics is STDP but not Structural (as here), merge
        if isinstance(synapse_dynamics, SynapseDynamicsSTDP):
            return SynapseDynamicsStructuralSTDP(
                self.partner_selection, self.formation,
                self.elimination,
                synapse_dynamics.timing_dependence,
                synapse_dynamics.weight_dependence,
                # voltage dependence is not supported
                None, synapse_dynamics.dendritic_delay_fraction,
                self.f_rew, self.initial_weight, self.initial_delay,
                self.s_max, self.seed,
                backprop_delay=synapse_dynamics.backprop_delay)

        # Otherwise, it is static, so return ourselves
        return self

    @overrides(AbstractSynapseDynamicsStructural.write_structural_parameters)
    def write_structural_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, app_vertex, post_slice, graph_mapper,
            routing_info, synapse_indices):
        super(SynapseDynamicsStructuralStatic, self).write_parameters(
            spec, region, machine_time_step, weight_scales)
        self.__common_sp.write_parameters(
            spec, region, machine_time_step, weight_scales, application_graph,
            app_vertex, post_slice, graph_mapper, routing_info,
            synapse_indices)

    def set_projection_parameter(self, param, value):
        self.__common_sp.set_projection_parameter(param, value)

    @overrides(SynapseDynamicsStatic.is_same_as)
    def is_same_as(self, synapse_dynamics):
        return self.__common_sp.is_same_as(synapse_dynamics)

    @overrides(SynapseDynamicsStatic.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        name = super(SynapseDynamicsStructuralStatic,
                     self).get_vertex_executable_suffix()
        name += self.__common_sp.get_vertex_executable_suffix()
        return name

    @overrides(AbstractSynapseDynamicsStructural
               .get_structural_parameters_sdram_usage_in_bytes)
    def get_structural_parameters_sdram_usage_in_bytes(
            self, application_graph, app_vertex, n_neurons, n_synapse_types):
        size = super(SynapseDynamicsStructuralStatic, self).\
            get_parameters_sdram_usage_in_bytes(n_neurons, n_synapse_types)
        size += self.__common_sp.get_parameters_sdram_usage_in_bytes(
            application_graph, app_vertex, n_neurons)
        return size

    @overrides(SynapseDynamicsStatic.get_n_words_for_static_connections)
    def get_n_words_for_static_connections(self, n_connections):
        value = super(SynapseDynamicsStructuralStatic,
                      self).get_n_words_for_static_connections(n_connections)
        self.__common_sp.n_words_for_static_connections(value)
        return value

    @overrides(AbstractSynapseDynamicsStructural.set_connections)
    def set_connections(
            self, connections, post_vertex_slice, app_edge, synapse_info,
            machine_edge):
        self.__common_sp.synaptic_data_update(
            connections, post_vertex_slice, app_edge, synapse_info,
            machine_edge)

    @overrides(SynapseDynamicsStatic.get_parameter_names)
    def get_parameter_names(self):
        names = super(
            SynapseDynamicsStructuralStatic, self).get_parameter_names()
        names.extend(self.__common_sp.get_parameter_names())
        return names

    @property
    @overrides(SynapseDynamicsStatic.changes_during_run)
    def changes_during_run(self):
        return True

    @property
    @overrides(AbstractSynapseDynamicsStructural.f_rew)
    def f_rew(self):
        return self.__common_sp.f_rew

    @property
    @overrides(AbstractSynapseDynamicsStructural.seed)
    def seed(self):
        return self.__common_sp.seed

    @property
    @overrides(AbstractSynapseDynamicsStructural.s_max)
    def s_max(self):
        return self.__common_sp.s_max

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

    @overrides(SynapseDynamicsStatic.get_weight_mean)
    def get_weight_mean(self, connector, synapse_info):
        return self.get_weight_maximum(connector, synapse_info)

    @overrides(SynapseDynamicsStatic.get_weight_variance)
    def get_weight_variance(self, connector, weights):
        return 0.0

    @overrides(SynapseDynamicsStatic.get_weight_maximum)
    def get_weight_maximum(self, connector, synapse_info):
        w_m = super(SynapseDynamicsStructuralStatic, self).get_weight_maximum(
            connector, synapse_info)
        return max(w_m, self.__common_sp.initial_weight)
