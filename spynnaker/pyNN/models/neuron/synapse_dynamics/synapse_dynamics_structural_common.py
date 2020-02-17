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
import numpy
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION, MICRO_TO_SECOND_CONVERSION,
    BYTES_PER_WORD, BYTES_PER_SHORT)
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.utilities import constants
import math


class SynapseDynamicsStructuralCommon(object):
    """ Utility class that holds properties of synaptic rewiring\
        both in the presence and absence of STDP.

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

    # 7 32-bit numbers (fast; p_rew; s_max; app_no_atoms; machine_no_atoms;
    # low_atom; high_atom) + 2 4-word RNG seeds (shared_seed; local_seed)
    # + 1 32-bit number (no_pre_pops)
    REWIRING_DATA_SIZE = (
        (7 * BYTES_PER_WORD) + (2 * 4 * BYTES_PER_WORD) + BYTES_PER_WORD)

    # Size excluding key_atom_info (as variable length)
    # 4 16-bit numbers (no_pre_vertices; sp_control; delay_lo; delay_hi)
    # + 3 32-bit numbers (weight; connection_type; total_no_atoms)
    PRE_POP_INFO_BASE_SIZE = (4 * BYTES_PER_SHORT) + (3 * BYTES_PER_WORD)

    # 5 32-bit numbers (key; mask; n_atoms; lo_atom; m_pop_index)
    KEY_ATOM_INFO_SIZE = (5 * BYTES_PER_WORD)

    # 1 16-bit number (neuron_index)
    # + 2 8-bit numbers (sub_pop_index; pop_index)
    POST_TO_PRE_ENTRY_SIZE = BYTES_PER_SHORT + (2 * 1)

    DEFAULT_F_REW = 10**4
    DEFAULT_INITIAL_WEIGHT = 0
    DEFAULT_INITIAL_DELAY = 1
    DEFAULT_S_MAX = 32

    def __init__(
            self, partner_selection, formation, elimination, f_rew,
            initial_weight, initial_delay, s_max, seed):
        """

        :param partner_selection: The partner selection rule
        :param formation: The formation rule
        :param elimination: The elimination rule
        :param f_rew: How many rewiring attempts will be done per second.
        :type f_rew: int
        :param initial_weight:\
            Initial weight assigned to a newly formed connection
        :type initial_weight: float
        :param initial_delay: Delay assigned to a newly formed connection
        :type initial_delay: int or (int, int)
        :param s_max: Maximum fan-in per target layer neuron
        :type s_max: int
        :param seed: seed the random number generators
        :type seed: int
        """
        self.__partner_selection = partner_selection
        self.__formation = formation
        self.__elimination = elimination
        self.__f_rew = f_rew
        self.__p_rew = 1. / self.__f_rew
        self.__initial_weight = initial_weight
        self.__initial_delay = initial_delay
        self.__s_max = s_max
        self.__seed = seed
        self.__connections = dict()

        self.__actual_row_max_length = self.__s_max

        self.__rng = numpy.random.RandomState(seed)
        self.__seeds = dict()

        # Addition information -- used for SDRAM usage
        self.__actual_sdram_usage = dict()

    def set_projection_parameter(self, param, value):
        has_set = False
        for item in [self.__partner_selection, self.__formation,
                     self.__elimination]:
            if hasattr(item, param):
                setattr(item, param, value)
                has_set = True
                break
        if not has_set:
            raise Exception("Unknown parameter {}".format(param))

    def get_parameter_names(self):
        names = ['initial_weight', 'initial_delay', 'f_rew', 'p_rew', 's_max']
        names.extend(self.__partner_selection.get_parameter_names())
        names.extend(self.__formation.get_parameter_names())
        names.extend(self.__elimination.get_parameter_names())
        return names

    @property
    def p_rew(self):
        """ The period of rewiring.

        :return: The period of rewiring
        :rtype: int
        """
        return self.__p_rew

    @property
    def actual_sdram_usage(self):
        """ Actual SDRAM usage (based on what is written to spec).

        :return: actual SDRAM usage
        :rtype: int
        """
        return self.__actual_sdram_usage

    def write_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, app_vertex, post_slice, graph_mapper,
            routing_info, synapse_indices):
        """ Write the synapse parameters to the spec.
        """
        spec.comment("Writing structural plasticity parameters")
        if spec.current_region != constants.POPULATION_BASED_REGIONS. \
                SYNAPSE_DYNAMICS.value:
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
            spec, app_vertex, structural_edges, graph_mapper, routing_info,
            weight_scales, post_slice, synapse_indices, machine_time_step)

        # Write the post-to-pre table
        self.__write_post_to_pre_table(
            spec, pop_index, app_vertex, post_slice, graph_mapper)

        # Write the component parameters
        self.__partner_selection.write_parameters(spec)
        for _, synapse_info in structural_edges:
            dynamics = synapse_info.synapse_dynamics
            dynamics.formation.write_parameters(spec)
        for _, synapse_info in structural_edges:
            dynamics = synapse_info.synapse_dynamics
            dynamics.elimination.write_parameters(
                spec, weight_scales[synapse_info.synapse_type])

    def __get_structural_edges(self, application_graph, app_vertex):
        structural_application_edges = list()
        for app_edge in application_graph.get_edges_ending_at_vertex(
                app_vertex):
            if isinstance(app_edge, ProjectionApplicationEdge):
                found = False
                for synapse_info in app_edge.synapse_information:
                    if isinstance(synapse_info.synapse_dynamics,
                                  AbstractSynapseDynamicsStructural):
                        if found:
                            raise SynapticConfigurationException(
                                "Only one Projection between each pair of"
                                " Populations can use structural plasticity ")
                        found = True
                        structural_application_edges.append(
                            (app_edge, synapse_info))

        return structural_application_edges

    def __write_common_rewiring_data(
            self, spec, app_vertex, post_slice, machine_time_step, n_pre_pops):
        """ Write the non-sub-population synapse parameters to the spec.

        :param spec: the data spec
        :type spec: spec
        :param app_vertex: \
            the highest level object of the post-synaptic population
        :type app_vertex: :py:class:`ApplicationVertex`
        :param post_slice: \
            the slice of the app vertex corresponding to this machine vertex
        :type post_slice: :py:class:`Slice`
        :param machine_time_step: the duration of a machine time step (ms)
        :type machine_time_step: int
        :param n_pre_pops: the number of pre-populations
        :type n_pre_pops: int
        :return: None
        :rtype: None
        """
        if (self.__p_rew * MICRO_TO_MILLISECOND_CONVERSION <
                machine_time_step / MICRO_TO_MILLISECOND_CONVERSION):
            # Fast rewiring
            spec.write_value(data=1)
            spec.write_value(data=int(
                machine_time_step / (
                    self.__p_rew * MICRO_TO_SECOND_CONVERSION)))
        else:
            # Slow rewiring
            spec.write_value(data=0)
            spec.write_value(data=int((
                self.__p_rew * MICRO_TO_SECOND_CONVERSION) /
                float(machine_time_step)))
        # write s_max
        spec.write_value(data=int(self.__s_max))
        # write total number of atoms in the application vertex
        spec.write_value(data=app_vertex.n_atoms)
        # write local low, high and number of atoms
        spec.write_value(data=post_slice.n_atoms)
        spec.write_value(data=post_slice.lo_atom)
        spec.write_value(data=post_slice.hi_atom)

        # Generate a seed for the RNG on chip that is the same for all
        # of the cores that have perform structural updates.
        # NOTE: it should be different between application vertices
        if app_vertex not in self.__seeds.keys():
            self.__seeds[app_vertex] = \
                [self.__rng.randint(0x7FFFFFFF) for _ in range(4)]

        # write the random seed (4 words), generated randomly,
        # but the same for all postsynaptic vertices!
        for seed in self.__seeds[app_vertex]:
            spec.write_value(data=seed)

        # write local seed (4 words), generated randomly!
        for _ in range(4):
            spec.write_value(data=numpy.random.randint(0x7FFFFFFF))

        # write the number of pre-populations
        spec.write_value(data=n_pre_pops)

    def __write_prepopulation_info(
            self, spec, app_vertex, structural_edges, graph_mapper,
            routing_info, weight_scales, post_slice, synapse_indices,
            machine_time_step):
        pop_index = dict()
        index = 0
        for app_edge, synapse_info in structural_edges:
            pop_index[app_edge.pre_vertex, synapse_info] = index
            index += 1
            all_machine_edges = graph_mapper.get_machine_edges(app_edge)
            machine_edges = [
                e for e in all_machine_edges
                if graph_mapper.get_slice(e.post_vertex) == post_slice]
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
                vertex_slice = graph_mapper.get_slice(machine_edge.pre_vertex)
                skey = (synapse_info, vertex_slice.lo_atom, post_slice.lo_atom)
                spec.write_value(r_info.first_key)
                spec.write_value(r_info.first_mask)
                spec.write_value(vertex_slice.n_atoms)
                spec.write_value(vertex_slice.lo_atom)
                spec.write_value(synapse_indices[skey])
        return pop_index

    def __write_post_to_pre_table(
            self, spec, pop_index, app_vertex, post_slice, graph_mapper):
        """ Post to pre table is basically the transpose of the synaptic\
            matrix
        """
        # Get connections for this post slice
        key = (app_vertex, post_slice.lo_atom)
        slice_conns = self.__connections[key]
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
            [graph_mapper.get_machine_vertex_index(m_edge.pre_vertex)
             for (_, _, m_edge, _) in slice_conns], conn_lens)
        # Get the low atom for each source and subtract
        lo_atoms = numpy.repeat(
            [graph_mapper.get_slice(m_edge.pre_vertex).lo_atom
             for (_, _, m_edge, _) in slice_conns], conn_lens)
        connections["source"] = connections["source"] - lo_atoms
        connections["target"] = connections["target"] - post_slice.lo_atom

        # Make an array of all data required
        conn_data = numpy.dstack(
            (pop_indices, subpop_indices, connections["source"]))[0]

        # Break data into rows based on target and strip target out
        rows = [conn_data[connections["target"] == i]
                for i in range(0, post_slice.n_atoms)]

        if any(len(row) > self.__s_max for row in rows):
            raise Exception("Too many initial connections per incoming neuron")

        # Make each row the required length through padding with 0xFFFF
        padded_rows = [numpy.pad(row, [(self.__s_max - len(row), 0), (0, 0)],
                                 "constant", constant_values=0xFFFF)
                       for row in rows]

        # Finally make the table and write it out
        post_to_pre = numpy.core.records.fromarrays(
            numpy.concatenate(padded_rows).T, formats="u1, u1, u2").view("u4")
        spec.write_array(post_to_pre)

    def get_parameters_sdram_usage_in_bytes(
            self, application_graph, app_vertex, n_neurons):
        """ Get SDRAM usage

        :return: SDRAM usage
        :rtype: int
        """
        # Work out how many sub-edges we will end up with, as this is used
        # for key_atom_info
        n_sub_edges = 0
        structural_edges = self.__get_structural_edges(
            application_graph, app_vertex)
        # Also keep track of the parameter sizes
        param_sizes = self.__partner_selection\
            .get_parameters_sdram_usage_in_bytes()
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

        return int((self.REWIRING_DATA_SIZE +
                   (self.PRE_POP_INFO_BASE_SIZE * len(structural_edges)) +
                   (self.KEY_ATOM_INFO_SIZE * n_sub_edges) +
                   (self.POST_TO_PRE_ENTRY_SIZE * n_neurons * self.__s_max) +
                   param_sizes))

    def synaptic_data_update(
            self, connections, post_vertex_slice, app_edge, synapse_info,
            machine_edge):
        """ Set synaptic data
        """
        if not isinstance(synapse_info.synapse_dynamics,
                          AbstractSynapseDynamicsStructural):
            return
        key = (app_edge.post_vertex, post_vertex_slice.lo_atom)
        if key not in self.__connections.keys():
            self.__connections[key] = []
        self.__connections[key].append(
            (connections, app_edge, machine_edge, synapse_info))

    def n_words_for_plastic_connections(self, value):
        """ Set size of plastic connections in words
        """
        self.__actual_row_max_length = value

    def n_words_for_static_connections(self, value):
        """ Set size of static connections in words
        """
        self.__actual_row_max_length = value

    def get_vertex_executable_suffix(self):
        name = "_structural"
        name += self.__partner_selection.vertex_executable_suffix
        name += self.__formation.vertex_executable_suffix
        name += self.__elimination.vertex_executable_suffix
        return name

    def is_same_as(self, synapse_dynamics):
        # Note noqa because exact type comparison is required here
        return (
            self.__s_max == synapse_dynamics.s_max and
            self.__f_rew == synapse_dynamics.f_rew and
            self.__initial_weight == synapse_dynamics.initial_weight and
            self.__initial_delay == synapse_dynamics.initial_delay and
            (type(self.__partner_selection) ==  # noqa
             type(synapse_dynamics.partner_selection)) and
            (type(self.__formation) ==
             type(synapse_dynamics.formation)) and
            (type(self.__elimination) ==
             type(synapse_dynamics.elimination)))

    @property
    def initial_weight(self):
        return self.__initial_weight

    @property
    def initial_delay(self):
        return self.__initial_delay

    @property
    def f_rew(self):
        return self.__f_rew

    @property
    def s_max(self):
        return self.__s_max

    @property
    def seed(self):
        return self.__seed

    @property
    def partner_selection(self):
        return self.__partner_selection

    @property
    def formation(self):
        return self.__formation

    @property
    def elimination(self):
        return self.__elimination
