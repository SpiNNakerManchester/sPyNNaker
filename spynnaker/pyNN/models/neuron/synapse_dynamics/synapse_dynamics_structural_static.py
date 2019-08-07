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


class SynapseDynamicsStructuralStatic(
        SynapseDynamicsStatic, AbstractSynapseDynamicsStructural):
    """ Class that enables synaptic rewiring. It acts as a wrapper\
        around SynapseDynamicsStatic.
        This means rewiring can operate in parallel with these\
        types of synapses.

        Written by Petrut Bogdan.

        Example usage to allow rewiring in parallel with STDP::

            stdp_model = sim.STDPMechanism(...)

            structure_model_with_stdp = sim.StructuralMechanismStatic(
                weight=0,
                s_max=32,
                grid=[np.sqrt(pop_size), np.sqrt(pop_size)],
                random_partner=True,
                f_rew=10 ** 4,  # Hz
                sigma_form_forward=1.,
                delay=10
            )
            plastic_projection = sim.Projection(
                ...,
                synapse_dynamics=sim.SynapseDynamics(
                    slow=structure_model_with_stdp
                )
            )

    :param partner_selection: The partner selection rule
    :param formation: The formation rule
    :param elimination: The elimination rule
    :param f_rew: How many rewiring attempts will be done per second.
    :type f_rew: int
    :param initial_weight: Weight assigned to a newly formed connection
    :type initial_weight: float
    :param initial_delay: Delay assigned to a newly formed connection
    :type initial_delay: int or (int, int)
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

    @overrides(AbstractSynapseDynamicsStructural.write_structural_parameters)
    def write_structural_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, app_vertex, post_slice, graph_mapper,
            routing_info):
        super(SynapseDynamicsStructuralStatic, self).write_parameters(
            spec, region, machine_time_step, weight_scales)
        self.__common_sp.write_parameters(
            spec, region, machine_time_step, weight_scales, application_graph,
            app_vertex, post_slice, graph_mapper, routing_info)

    def set_projection_parameter(self, projection, param, value):
        self.__common_sp.set_projection_parameter(projection, param, value)

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
