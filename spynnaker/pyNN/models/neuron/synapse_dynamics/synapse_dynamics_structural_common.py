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

import collections
import math
import numpy
from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION, MICRO_TO_SECOND_CONVERSION,
    BYTES_PER_WORD, BYTES_PER_SHORT)
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.exceptions import SynapticConfigurationException

#: Default value for frequency of rewiring
DEFAULT_F_REW = 10 ** 4
#: Default value for initial weight on connection formation
DEFAULT_INITIAL_WEIGHT = 0
#: Default value for initial delay on connection formation
DEFAULT_INITIAL_DELAY = 1
#: Default value for maximum fan-in per target layer neuron
DEFAULT_S_MAX = 32


@add_metaclass(AbstractBase)
class SynapseDynamicsStructuralCommon(AbstractSynapseDynamicsStructural):

    # 7 32-bit numbers (fast; p_rew; s_max; app_no_atoms; machine_no_atoms;
    # low_atom; high_atom) + 2 4-word RNG seeds (shared_seed; local_seed)
    # + 1 32-bit number (no_pre_pops)
    _REWIRING_DATA_SIZE = (
        (7 * BYTES_PER_WORD) + (2 * 4 * BYTES_PER_WORD) + BYTES_PER_WORD)

    # Size excluding key_atom_info (as variable length)
    # 4 16-bit numbers (no_pre_vertices; sp_control; delay_lo; delay_hi)
    # + 3 32-bit numbers (weight; connection_type; total_no_atoms)
    _PRE_POP_INFO_BASE_SIZE = (4 * BYTES_PER_SHORT) + (3 * BYTES_PER_WORD)

    # 5 32-bit numbers (key; mask; n_atoms; lo_atom; m_pop_index)
    _KEY_ATOM_INFO_SIZE = (5 * BYTES_PER_WORD)

    # 1 16-bit number (neuron_index)
    # + 2 8-bit numbers (sub_pop_index; pop_index)
    _POST_TO_PRE_ENTRY_SIZE = BYTES_PER_SHORT + (2 * 1)

    def get_parameter_names(self):
        """
        :rtype: list(str)
        """
        names = ['initial_weight', 'initial_delay', 'f_rew', 'p_rew', 's_max']
        # pylint: disable=no-member
        names.extend(self.partner_selection.get_parameter_names())
        names.extend(self.formation.get_parameter_names())
        names.extend(self.elimination.get_parameter_names())
        return names

    @property
    def p_rew(self):
        """ The period of rewiring.

        :return: The period of rewiring
        :rtype: int
        """
        return 1. / self.f_rew

    @overrides(AbstractSynapseDynamicsStructural.write_structural_parameters)
    def write_structural_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, app_vertex, post_slice, routing_info,
            synapse_indices):
        """ Write structural plasticity parameters

        :param ~data_specification.DataSpecificationGenerator spec:
            the data spec
        :param int region: region ID
        :param int machine_time_step: the duration of a machine time step (ms)
        :param weight_scales:
        :type weight_scales: ~numpy.ndarray or list(float)
        :param ~pacman.model.graphs.application.ApplicationGraph\
                application_graph:
            the entire, highest level, graph of the network to be simulated
        :param AbstractPopulationVertex app_vertex:
            the highest level object of the post-synaptic population
        :param ~pacman.model.graphs.common.Slice post_slice:
            the slice of the app vertex corresponding to this machine vertex
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            All of the routing information on the network
        :param dict(tuple(SynapseInformation,int),int) synapse_indices:
        """
        spec.comment("Writing structural plasticity parameters")
        spec.switch_write_focus(region)

        # Get relevant edges
        structural_edges = self.__get_structural_edges(
            application_graph, app_vertex)

        # Write the common part of the rewiring data
        self.__write_common_rewiring_data(
            spec, app_vertex, post_slice, machine_time_step,
            len(structural_edges))

        # Write the pre-population info
        pop_index = self.__write_prepopulation_info(
            spec, app_vertex, structural_edges, routing_info, weight_scales,
            post_slice, synapse_indices, machine_time_step)

        # Write the post-to-pre table
        self.__write_post_to_pre_table(spec, pop_index, app_vertex, post_slice)

        # Write the component parameters
        # pylint: disable=no-member
        self.partner_selection.write_parameters(spec)
        for _, synapse_info in structural_edges:
            dynamics = synapse_info.synapse_dynamics
            dynamics.formation.write_parameters(spec)
        for _, synapse_info in structural_edges:
            dynamics = synapse_info.synapse_dynamics
            dynamics.elimination.write_parameters(
                spec, weight_scales[synapse_info.synapse_type])

    def __get_structural_edges(self, app_graph, app_vertex):
        """
        :param ~pacman.model.graphs.application.ApplicationGraph app_graph:
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
        :rtype: list(tuple(ProjectionApplicationEdge, SynapseInformation))
        """
        structural_edges = list()
        for app_edge in app_graph.get_edges_ending_at_vertex(app_vertex):
            if isinstance(app_edge, ProjectionApplicationEdge):
                found = False
                for synapse_info in app_edge.synapse_information:
                    if isinstance(synapse_info.synapse_dynamics,
                                  AbstractSynapseDynamicsStructural):
                        if found:
                            raise SynapticConfigurationException(
                                "Only one Projection between each pair of "
                                "Populations can use structural plasticity")
                        found = True
                        structural_edges.append((app_edge, synapse_info))
        return structural_edges

    def __write_common_rewiring_data(
            self, spec, app_vertex, post_slice, machine_time_step, n_pre_pops):
        """ Write the non-sub-population synapse parameters to the spec.

        :param ~data_specification.DataSpecificationGenerator spec:
            the data spec
        :param AbstractPopulationVertex app_vertex:
            the highest level object of the post-synaptic population
        :param ~pacman.model.graphs.common.Slice post_slice:
            the slice of the app vertex corresponding to this machine vertex
        :param int machine_time_step: the duration of a machine time step (ms)
        :param int n_pre_pops: the number of pre-populations
        :return: None
        :rtype: None
        """
        if (self.p_rew * MICRO_TO_MILLISECOND_CONVERSION <
                machine_time_step / MICRO_TO_MILLISECOND_CONVERSION):
            # Fast rewiring
            spec.write_value(data=1)
            spec.write_value(data=int(
                machine_time_step / (
                    self.p_rew * MICRO_TO_SECOND_CONVERSION)))
        else:
            # Slow rewiring
            spec.write_value(data=0)
            spec.write_value(data=int((
                self.p_rew * MICRO_TO_SECOND_CONVERSION) /
                float(machine_time_step)))
        # write s_max
        spec.write_value(data=int(self.s_max))
        # write total number of atoms in the application vertex
        spec.write_value(data=app_vertex.n_atoms)
        # write local low, high and number of atoms
        spec.write_value(data=post_slice.n_atoms)
        spec.write_value(data=post_slice.lo_atom)
        spec.write_value(data=post_slice.hi_atom)

        # write app level seeds
        spec.write_array(self.get_seeds(app_vertex))

        # write local seed (4 words), generated randomly!
        spec.write_array(self.get_seeds())

        # write the number of pre-populations
        spec.write_value(data=n_pre_pops)

    def __write_prepopulation_info(
            self, spec, app_vertex, structural_edges,
            routing_info, weight_scales, post_slice, synapse_indices,
            machine_time_step):
        """
        :param ~data_specification.DataSpecificationGenerator spec:
        :param AbstractPopulationVertex app_vertex:
        :param list(tuple(ProjectionApplicationEdge,SynapseInformation)) \
                structural_edges:
        :param RoutingInfo routing_info:
        :param dict(AbstractSynapseType,float) weight_scales:
        :param ~pacman.model.graphs.common.Slice post_slice:
        :param dict(tuple(SynapseInformation,int),int) synapse_indices:
        :param int machine_time_step:
        :rtype: dict(tuple(AbstractPopulationVertex,SynapseInformation),int)
        """
        pop_index = dict()
        index = 0
        for app_edge, synapse_info in structural_edges:
            pop_index[app_edge.pre_vertex, synapse_info] = index
            index += 1
            machine_edges = [
                e for e in app_edge.machine_edges
                if e.post_vertex.vertex_slice == post_slice]
            dynamics = synapse_info.synapse_dynamics

            # Number of machine edges
            spec.write_value(len(machine_edges), data_type=DataType.UINT16)
            # Controls - currently just if this is a self connection or not
            self_connected = app_vertex == app_edge.pre_vertex
            spec.write_value(int(self_connected), data_type=DataType.UINT16)
            # Delay
            delay_scale = 1000.0 / machine_time_step
            if isinstance(dynamics.initial_delay, collections.Iterable):
                spec.write_value(int(dynamics.initial_delay[0] * delay_scale),
                                 data_type=DataType.UINT16)
                spec.write_value(int(dynamics.initial_delay[1] * delay_scale),
                                 data_type=DataType.UINT16)
            else:
                scaled_delay = dynamics.initial_delay * delay_scale
                spec.write_value(scaled_delay, data_type=DataType.UINT16)
                spec.write_value(scaled_delay, data_type=DataType.UINT16)

            # Weight
            spec.write_value(round(dynamics.initial_weight *
                                   weight_scales[synapse_info.synapse_type]))
            # Connection type
            spec.write_value(synapse_info.synapse_type)
            # Total number of atoms in pre-vertex
            spec.write_value(app_edge.pre_vertex.n_atoms)
            # Machine edge information
            for machine_edge in machine_edges:
                r_info = routing_info.get_routing_info_for_edge(machine_edge)
                vertex_slice = machine_edge.pre_vertex.vertex_slice
                spec.write_value(r_info.first_key)
                spec.write_value(r_info.first_mask)
                spec.write_value(vertex_slice.n_atoms)
                spec.write_value(vertex_slice.lo_atom)
                spec.write_value(
                    synapse_indices[synapse_info, vertex_slice.lo_atom])
        return pop_index

    def __write_post_to_pre_table(
            self, spec, pop_index, app_vertex, post_slice):
        """ Post to pre table is basically the transpose of the synaptic\
            matrix.

        :param ~data_specification.DataSpecificationGenerator spec:
        :param dict(tuple(AbstractPopulationVertex,SynapseInformation),int) \
                pop_index:
        :param AbstractPopulationVertex app_vertex:
        :param ~pacman.model.graphs.common.Slice post_slice:
        """
        # pylint: disable=unsubscriptable-object
        # Get connections for this post slice
        slice_conns = self.connections[app_vertex, post_slice.lo_atom]
        # Make a single large array of connections
        connections = numpy.concatenate(
            [conn for (conn, _, _, _) in slice_conns])
        # Make a single large array of population index
        conn_lens = [len(conn) for (conn, _, _, _) in slice_conns]
        for (_, a_edge, _, s_info) in slice_conns:
            if (a_edge.pre_vertex, s_info) not in pop_index:
                print("Help!")
        pop_indices = numpy.repeat(
            [pop_index[a_edge.pre_vertex, s_info]
             for (_, a_edge, _, s_info) in slice_conns], conn_lens)
        # Make a single large array of sub-population index
        subpop_indices = numpy.repeat(
            [m_edge.pre_vertex.index
             for (_, _, m_edge, _) in slice_conns], conn_lens)
        # Get the low atom for each source and subtract
        lo_atoms = numpy.repeat(
            [m_edge.pre_vertex.vertex_slice.lo_atom
             for (_, _, m_edge, _) in slice_conns], conn_lens)
        connections["source"] = connections["source"] - lo_atoms
        connections["target"] = connections["target"] - post_slice.lo_atom

        # Make an array of all data required
        conn_data = numpy.dstack(
            (pop_indices, subpop_indices, connections["source"]))[0]

        # Break data into rows based on target and strip target out
        rows = [conn_data[connections["target"] == i]
                for i in range(0, post_slice.n_atoms)]

        if any(len(row) > self.s_max for row in rows):
            raise Exception("Too many initial connections per incoming neuron")

        # Make each row the required length through padding with 0xFFFF
        padded_rows = [numpy.pad(row, [(self.s_max - len(row), 0), (0, 0)],
                                 "constant", constant_values=0xFFFF)
                       for row in rows]

        # Finally make the table and write it out
        post_to_pre = numpy.core.records.fromarrays(
            numpy.concatenate(padded_rows).T, formats="u1, u1, u2").view("u4")
        spec.write_array(post_to_pre)

    @overrides(AbstractSynapseDynamicsStructural.
               get_structural_parameters_sdram_usage_in_bytes)
    def get_structural_parameters_sdram_usage_in_bytes(
            self, application_graph, app_vertex, n_neurons, n_synapse_types):
        """ Get the size of SDRAM usage for the structural parameters

        :param ~pacman.model.graphs.application.ApplicationGraph \
                application_graph:
        :param ~spynnaker.pyNN.models.neuron.AbstractPopulationVertex \
                app_vertex:
        :param int n_neurons:
        :param int n_synapse_types:
        :return: the size of the parameters, in bytes
        :rtype: int
        """
        # Work out how many sub-edges we will end up with, as this is used
        # for key_atom_info
        n_sub_edges = 0
        structural_edges = self.__get_structural_edges(
            application_graph, app_vertex)
        # Also keep track of the parameter sizes
        # pylint: disable=no-member
        param_sizes = (
            self.partner_selection.get_parameters_sdram_usage_in_bytes())
        for (in_edge, synapse_info) in structural_edges:
            max_atoms = in_edge.pre_vertex.get_max_atoms_per_core()
            if in_edge.pre_vertex.n_atoms < max_atoms:
                max_atoms = in_edge.pre_vertex.n_atoms
            n_sub_edges += int(math.ceil(
                float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))
            dynamics = synapse_info.synapse_dynamics
            param_sizes += dynamics.formation\
                .get_parameters_sdram_usage_in_bytes()
            param_sizes += dynamics.elimination\
                .get_parameters_sdram_usage_in_bytes()

        return int((self._REWIRING_DATA_SIZE +
                   (self._PRE_POP_INFO_BASE_SIZE * len(structural_edges)) +
                   (self._KEY_ATOM_INFO_SIZE * n_sub_edges) +
                   (self._POST_TO_PRE_ENTRY_SIZE * n_neurons * self.s_max) +
                   param_sizes))

    def get_vertex_executable_suffix(self):
        """
        :rtype: str
        """
        name = "_structural"
        # pylint: disable=no-member
        name += self.partner_selection.vertex_executable_suffix
        name += self.formation.vertex_executable_suffix
        name += self.elimination.vertex_executable_suffix
        return name

    def is_same_as(self, synapse_dynamics):
        """
        :param SynapseDynamicsStructuralCommon synapse_dynamics:
        :rtype: bool
        """
        # Note noqa because exact type comparison is required here
        return (
            self.s_max == synapse_dynamics.s_max and
            self.f_rew == synapse_dynamics.f_rew and
            self.initial_weight == synapse_dynamics.initial_weight and
            self.initial_delay == synapse_dynamics.initial_delay and
            (type(self.partner_selection) ==  # noqa
             type(synapse_dynamics.partner_selection)) and
            (type(self.formation) ==
             type(synapse_dynamics.formation)) and
            (type(self.elimination) ==
             type(synapse_dynamics.elimination)))

    @abstractproperty
    def connections(self):
        """
        initial connectivity as defined via connector
        :rtype dict:
        """

    @abstractmethod
    def get_seeds(self, app_vertex=None):
        """
        Generate a seed for the RNG on chip that is the same for all
        of the cores that have perform structural updates.

        It should be different between application vertices
            but the same for the same app_vertex
        It should be different every time called with None

        :param app_vertex:
        :type app_vertex: ApplicationVertex or None
        :return: list of random seed (4 words), generated randomly
        """
