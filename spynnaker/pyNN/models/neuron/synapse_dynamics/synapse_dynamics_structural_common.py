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
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spinn_utilities.overrides import overrides
from data_specification.enums.data_type import DataType
from pacman.model.graphs.application import (
    ApplicationGraph, ApplicationVertex)
from pacman.model.graphs.machine import (MachineGraph, MachineVertex)
from pacman.exceptions import PacmanInvalidParameterException
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION, MICRO_TO_SECOND_CONVERSION,
    BYTES_PER_WORD, BYTES_PER_SHORT)
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step)
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge)
from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.exceptions import SynapticConfigurationException

#: Default value for frequency of rewiring
DEFAULT_F_REW = 10 ** 4.0
#: Default value for initial weight on connection formation
DEFAULT_INITIAL_WEIGHT = 0.0
#: Default value for initial delay on connection formation
DEFAULT_INITIAL_DELAY = 1.0
#: Default value for maximum fan-in per target layer neuron
DEFAULT_S_MAX = 32


class SynapseDynamicsStructuralCommon(
        AbstractSynapseDynamicsStructural, metaclass=AbstractBase):

    # 8 32-bit numbers (fast; p_rew; s_max; app_no_atoms; machine_no_atoms;
    # low_atom; high_atom; with_replacement) + 2 4-word RNG seeds (shared_seed;
    # local_seed) + 1 32-bit number (no_pre_pops)
    _REWIRING_DATA_SIZE = (
        (8 * BYTES_PER_WORD) + (2 * 4 * BYTES_PER_WORD) + BYTES_PER_WORD)

    # Size excluding key_atom_info (as variable length)
    # 4 16-bit numbers (no_pre_vertices; sp_control; delay_lo; delay_hi)
    # + 3 32-bit numbers (weight; connection_type; total_no_atoms)
    _PRE_POP_INFO_BASE_SIZE = (4 * BYTES_PER_SHORT) + (3 * BYTES_PER_WORD)

    # 5 32-bit numbers (key; mask; n_atoms; lo_atom; m_pop_index)
    _KEY_ATOM_INFO_SIZE = (5 * BYTES_PER_WORD)

    # 1 16-bit number (neuron_index)
    # + 2 8-bit numbers (sub_pop_index; pop_index)
    _POST_TO_PRE_ENTRY_SIZE = BYTES_PER_SHORT + (2 * 1)

    PAIR_ERROR = (
        "Only one Projection between each pair of Populations can use "
        "structural plasticity")

    def get_parameter_names(self):
        """
        :rtype: list(str)
        """
        names = ['initial_weight', 'initial_delay', 'f_rew', 'p_rew', 's_max',
                 'with_replacement']
        # pylint: disable=no-member
        names.extend(self.partner_selection.get_parameter_names())
        names.extend(self.formation.get_parameter_names())
        names.extend(self.elimination.get_parameter_names())
        return names

    @property
    def p_rew(self):
        """ The period of rewiring.

        :return: The period of rewiring
        :rtype: float
        """
        return 1. / self.f_rew

    @overrides(AbstractSynapseDynamicsStructural.write_structural_parameters,
               extend_doc=False)
    def write_structural_parameters(
            self, spec, region, weight_scales, machine_graph, machine_vertex,
            routing_info, synaptic_matrices):
        """ Write structural plasticity parameters

        :param ~data_specification.DataSpecificationGenerator spec:
            the data spec
        :param int region: region ID
        :param weight_scales: scaling the weights
        :type weight_scales: ~numpy.ndarray or list(float)
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            Full machine level network
        :param AbstractPopulationVertex machine_vertex:
            the vertex for which data specs are being prepared
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            All of the routing information on the network
        :param SynapticMatrices synaptic_matrices:
            The synaptic matrices for this vertex
        """
        spec.comment("Writing structural plasticity parameters")
        spec.switch_write_focus(region)

        # Get relevant edges
        structural_edges, machine_edges_by_app = (
            self.__get_structural_edges_by_machine(
                machine_graph, machine_vertex))

        # Write the common part of the rewiring data
        self.__write_common_rewiring_data(
            spec, machine_vertex, len(structural_edges))

        # Write the pre-population info
        pop_index = self.__write_prepopulation_info(
            spec, machine_vertex, structural_edges, machine_edges_by_app,
            routing_info, weight_scales, synaptic_matrices)

        # Write the post-to-pre table
        self.__write_post_to_pre_table(spec, pop_index, machine_vertex)

        # Write the component parameters
        # pylint: disable=no-member
        self.partner_selection.write_parameters(spec)
        for synapse_info in structural_edges.values():
            dynamics = synapse_info.synapse_dynamics
            dynamics.formation.write_parameters(spec)
        for synapse_info in structural_edges.values():
            dynamics = synapse_info.synapse_dynamics
            dynamics.elimination.write_parameters(
                spec, weight_scales[synapse_info.synapse_type])

    def __get_structural_edges_by_app(self, app_graph, app_vertex):
        """
        :param ~pacman.model.graphs.application.ApplicationGraph app_graph:
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
        :rtype: dict(ProjectionApplicationEdge, SynapseInformation)
        """
        structural_edges = dict()
        for app_edge in app_graph.get_edges_ending_at_vertex(app_vertex):
            if isinstance(app_edge, ProjectionApplicationEdge):
                for synapse_info in app_edge.synapse_information:
                    if isinstance(synapse_info.synapse_dynamics,
                                  AbstractSynapseDynamicsStructural):
                        if app_edge in structural_edges:
                            raise SynapticConfigurationException(
                                self.PAIR_ERROR)
                        structural_edges[app_edge] = synapse_info
        return structural_edges

    def __get_structural_edges_by_machine(self, machine_graph, machine_vertex):
        """
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
        :rtype: dict(ProjectionApplicationEdge, SynapseInformation)
        """
        structural_edges = collections.OrderedDict()
        machine_edges = collections.defaultdict(list)
        for machine_edge in machine_graph.get_edges_ending_at_vertex(
                machine_vertex):
            app_edge = machine_edge.app_edge
            if isinstance(app_edge, ProjectionApplicationEdge):
                for synapse_info in app_edge.synapse_information:
                    if isinstance(synapse_info.synapse_dynamics,
                                  AbstractSynapseDynamicsStructural):
                        if app_edge in structural_edges:
                            if structural_edges[app_edge] != synapse_info:
                                raise SynapticConfigurationException(
                                   self.PAIR_ERROR)
                        else:
                            structural_edges[app_edge] = synapse_info
                        machine_edges[app_edge].append(machine_edge)
        return structural_edges, machine_edges

    def __write_common_rewiring_data(
            self, spec, machine_vertex, n_pre_pops):
        """ Write the non-sub-population synapse parameters to the spec.

        :param ~data_specification.DataSpecificationGenerator spec:
            the data spec
        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
            the vertex for which data specs are being prepared
        :param int n_pre_pops: the number of pre-populations
        :return: None
        :rtype: None
        """
        if (self.p_rew * MICRO_TO_MILLISECOND_CONVERSION <
                machine_time_step() / MICRO_TO_MILLISECOND_CONVERSION):
            # Fast rewiring
            spec.write_value(data=1)
            spec.write_value(data=int(
                machine_time_step() / (
                    self.p_rew * MICRO_TO_SECOND_CONVERSION)))
        else:
            # Slow rewiring
            spec.write_value(data=0)
            spec.write_value(data=int((
                self.p_rew * MICRO_TO_SECOND_CONVERSION) /
                machine_time_step()))
        # write s_max
        spec.write_value(data=int(self.s_max))
        # write total number of atoms in the application vertex
        app_vertex = machine_vertex.app_vertex
        spec.write_value(data=app_vertex.n_atoms)
        # write local low, high and number of atoms
        post_slice = machine_vertex.vertex_slice
        spec.write_value(data=post_slice.n_atoms)
        spec.write_value(data=post_slice.lo_atom)
        spec.write_value(data=post_slice.hi_atom)
        # write with_replacement
        spec.write_value(data=self.with_replacement)

        # write app level seeds
        spec.write_array(self.get_seeds(app_vertex))

        # write local seed (4 words), generated randomly!
        spec.write_array(self.get_seeds())

        # write the number of pre-populations
        spec.write_value(data=n_pre_pops)

    def __write_prepopulation_info(
            self, spec, machine_vertex, structural_edges, machine_edges_by_app,
            routing_info, weight_scales, synaptic_matrices):
        """
        :param ~data_specification.DataSpecificationGenerator spec:
        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
            the vertex for which data specs are being prepared
        :param list(tuple(ProjectionApplicationEdge,SynapseInformation)) \
                structural_edges:
        :param machine_edges_by_app:
            map of app edge to associated machine edges
        :type machine_edges_by_app:
            dict(~pacman.model.graphs.application.ApplicationEdge,
            list(~pacman.model.graphs.machine.MachineEdge))
        :param RoutingInfo routing_info:
        :param dict(AbstractSynapseType,float) weight_scales:
        :param SynapticMatrices synaptic_matrices:
        :rtype: dict(tuple(AbstractPopulationVertex,SynapseInformation),int)
        """
        pop_index = dict()
        index = 0
        for app_edge, synapse_info in structural_edges.items():
            pop_index[app_edge.pre_vertex, synapse_info] = index
            index += 1
            machine_edges = machine_edges_by_app[app_edge]
            dynamics = synapse_info.synapse_dynamics

            # Number of machine edges
            spec.write_value(len(machine_edges), data_type=DataType.UINT16)
            # Controls - currently just if this is a self connection or not
            self_connected = machine_vertex.app_vertex == app_edge.pre_vertex
            spec.write_value(int(self_connected), data_type=DataType.UINT16)
            # Delay
            delay_scale = (
                    MICRO_TO_MILLISECOND_CONVERSION /
                    machine_time_step())
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
                spec.write_value(synaptic_matrices.get_index(
                    app_edge, synapse_info, machine_edge))
        return pop_index

    def __write_post_to_pre_table(self, spec, pop_index, machine_vertex):
        """ Post to pre table is basically the transpose of the synaptic\
            matrix.

        :param ~data_specification.DataSpecificationGenerator spec:
        :param dict(tuple(AbstractPopulationVertex,SynapseInformation),int) \
                pop_index:
        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
            the vertex for which data specs are being prepared
        """
        # pylint: disable=unsubscriptable-object
        # Get connections for this post slice
        post_slice = machine_vertex.vertex_slice
        slice_conns = self.connections[
            machine_vertex.app_vertex, post_slice.lo_atom]
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
            self, graph, vertex, n_neurons):
        # Work out how many sub-edges we will end up with, as this is used
        # for key_atom_info
        n_sub_edges = 0
        if (isinstance(graph, ApplicationGraph) and
                isinstance(vertex, ApplicationVertex)):
            structural_edges = self.__get_structural_edges_by_app(
                graph, vertex)
            machine_edges_by_app = None
        elif (isinstance(graph, MachineGraph) and
                isinstance(vertex, MachineVertex)):
            structural_edges, machine_edges_by_app = \
                self.__get_structural_edges_by_machine(graph, vertex)
        else:
            raise PacmanInvalidParameterException(
                "vertex", vertex, "Not at the same level as graph")
        # Also keep track of the parameter sizes

        # pylint: disable=no-member
        param_sizes = (
            self.partner_selection.get_parameters_sdram_usage_in_bytes())
        for (app_edge, synapse_info) in structural_edges.items():
            if machine_edges_by_app:
                n_sub_edges += len(machine_edges_by_app[app_edge])
            else:
                slices, _ = (
                    app_edge.pre_vertex.splitter.get_out_going_slices())
                n_sub_edges = len(slices)
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
        """ initial connectivity as defined via connector

        :rtype: dict
        """

    @abstractmethod
    def get_seeds(self, app_vertex=None):
        """ Generate a seed for the RNG on chip that is the same for all\
            of the cores that have perform structural updates.

        It should be different between application vertices
        but the same for the same app_vertex.
        It should be different every time called with None.

        :param app_vertex:
        :type app_vertex: ApplicationVertex or None
        :return: list of random seed (4 words), generated randomly
        :rtype: list(int)
        """

    def check_initial_delay(self, max_delay_ms):
        """ Check that delays can be done without delay extensions

        :param float max_delay_ms: The maximum delay supported, in milliseconds
        :raises Exception: if the delay is out of range
        """
        if isinstance(self.initial_delay, collections.Iterable):
            # pylint: disable=unsubscriptable-object
            init_del = self.initial_delay
            if init_del[0] > max_delay_ms or init_del[1] > max_delay_ms:
                raise Exception(
                    "The initial delay {} has one or more values that are"
                    " bigger than {}.  This is not supported in the current"
                    " implementation.".format(
                        self.initial_delay, max_delay_ms))
        elif self.initial_delay > max_delay_ms:
            raise Exception(
                "The initial delay {} is bigger than {}.  This is not"
                " supported in the current implementation".format(
                    self.initial_delay, max_delay_ms))
