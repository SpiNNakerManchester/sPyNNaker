# Copyright (c) 2016 The University of Manchester
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
from typing import (
    Dict, Iterable, List, Sequence, Tuple, Union, TYPE_CHECKING)

import numpy
from numpy.typing import NDArray
from typing_extensions import TypeAlias

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.overrides import overrides

from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.common import Slice

from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationBase)
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION, MICRO_TO_SECOND_CONVERSION,
    BYTES_PER_WORD, BYTES_PER_SHORT)

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

from .abstract_synapse_dynamics_structural import (
    AbstractSynapseDynamicsStructural)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.projection import Projection
    from spynnaker.pyNN.models.neural_projections import (
        SynapseInformation)
    from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
    from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
    from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
        ConnectionsArray)
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge)

    _PopIndexType: TypeAlias = Dict[
        Tuple[PopulationApplicationVertex, SynapseInformation], int]
    _SubpopIndexType: TypeAlias = Dict[
        Tuple[PopulationApplicationVertex, SynapseInformation, int], int]

    #: :meta private:
    ConnectionsInfo: TypeAlias = Dict[
        Tuple[AbstractPopulationVertex, int],
        List[Tuple[ConnectionsArray, ProjectionApplicationEdge,
                   SynapseInformation]]]

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
    """
    Common code for structural synapse dynamics.
    """

    # 8 32-bit numbers (fast; p_rew; s_max; app_no_atoms; machine_no_atoms;
    # low_atom; high_atom; with_replacement) + 2 4-word RNG seeds (shared_seed;
    # local_seed) + 1 32-bit number (no_pre_pops)
    _REWIRING_DATA_SIZE = (
        (8 * BYTES_PER_WORD) + (2 * 4 * BYTES_PER_WORD) + BYTES_PER_WORD)

    # Size excluding key_atom_info (as variable length)
    # 4 16-bit numbers (no_pre_vertices; sp_control; delay_lo; delay_hi)
    # + 3 32-bit numbers (weight; connection_type; total_no_atoms)
    _PRE_POP_INFO_BASE_SIZE = (4 * BYTES_PER_SHORT) + (3 * BYTES_PER_WORD)

    # 6 32-bit numbers (key; mask; n_atoms; n_colour_bits; lo_atom;
    # m_pop_index)
    _KEY_ATOM_INFO_SIZE = (6 * BYTES_PER_WORD)

    # 1 16-bit number (neuron_index)
    # + 2 8-bit numbers (sub_pop_index; pop_index)
    _POST_TO_PRE_ENTRY_SIZE = BYTES_PER_SHORT + (2 * 1)

    PAIR_ERROR = (
        "Only one Projection between each pair of Populations can use "
        "structural plasticity")

    __slots__ = ()

    def get_parameter_names(self) -> Iterable[str]:
        """
        :rtype: list(str)
        """
        yield from [
            'initial_weight', 'initial_delay', 'f_rew', 'p_rew', 's_max',
            'with_replacement']
        # pylint: disable=no-member
        yield from self.partner_selection.get_parameter_names()
        yield from self.formation.get_parameter_names()
        yield from self.elimination.get_parameter_names()

    @property
    def p_rew(self) -> float:
        """
        The period of rewiring.

        :rtype: float
        """
        return 1. / self.f_rew

    @overrides(AbstractSynapseDynamicsStructural.write_structural_parameters)
    def write_structural_parameters(
            self, spec: DataSpecificationBase, region: int,
            weight_scales: NDArray[numpy.floating],
            app_vertex: AbstractPopulationVertex, vertex_slice: Slice,
            synaptic_matrices: SynapticMatrices):
        spec.comment("Writing structural plasticity parameters")
        spec.switch_write_focus(region)

        # Get relevant edges
        structural_projections = self.__get_structural_projections(
            app_vertex.incoming_projections)

        # Write the common part of the rewiring data
        self.__write_common_rewiring_data(
            spec, app_vertex, vertex_slice, len(structural_projections))

        # Write the pre-population info
        pop_index, subpop_index, lo_atom_index = \
            self.__write_prepopulation_info(
                spec, app_vertex, structural_projections,
                weight_scales, synaptic_matrices)

        # Write the post-to-pre table
        self.__write_post_to_pre_table(
            spec, pop_index, subpop_index, lo_atom_index, app_vertex,
            vertex_slice)

        # Write the component parameters
        # pylint: disable=no-member, protected-access
        spec.comment("Writing partner selection parameters")
        self.partner_selection.write_parameters(spec)
        for proj in structural_projections:
            spec.comment(f"Writing formation parameters for {proj.label}")
            dynamics = proj._synapse_information.synapse_dynamics
            dynamics.formation.write_parameters(spec)
        for proj in structural_projections:
            spec.comment(f"Writing elimination parameters for {proj.label}")
            dynamics = proj._synapse_information.synapse_dynamics
            dynamics.elimination.write_parameters(
                spec, weight_scales[proj._synapse_information.synapse_type])

    def __get_structural_projections(
            self, incoming_projections: Iterable[Projection]
            ) -> List[Projection]:
        """
        :param list(Projection) incoming_projections:
            Projections to filter to structural only
        :rtype: list(Projection)
        """
        structural_projections = list()
        seen_app_edges = set()
        for proj in incoming_projections:
            # pylint: disable=protected-access
            app_edge = proj._projection_edge
            for synapse_info in app_edge.synapse_information:
                if isinstance(synapse_info.synapse_dynamics,
                              AbstractSynapseDynamicsStructural):
                    if app_edge in seen_app_edges:
                        raise SynapticConfigurationException(self.PAIR_ERROR)
                    seen_app_edges.add(app_edge)
                    structural_projections.append(proj)
        return structural_projections

    def __write_common_rewiring_data(
            self, spec: DataSpecificationBase,
            app_vertex: AbstractPopulationVertex, vertex_slice: Slice,
            n_pre_pops: int):
        """
        Write the non-sub-population synapse parameters to the spec.

        :param ~data_specification.DataSpecificationGenerator spec:
            the data spec
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            The application vertex being generated
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the target vertex to generate for
        :param int n_pre_pops: the number of pre-populations
        """
        time_step_us = SpynnakerDataView.get_simulation_time_step_us()
        spec.comment("Writing common rewiring data")
        if (self.p_rew * MICRO_TO_MILLISECOND_CONVERSION <
                time_step_us / MICRO_TO_MILLISECOND_CONVERSION):
            # Fast rewiring
            spec.write_value(data=1)
            spec.write_value(data=int(
                time_step_us / (
                    self.p_rew * MICRO_TO_SECOND_CONVERSION)))
        else:
            # Slow rewiring
            spec.write_value(data=0)
            spec.write_value(data=int((
                self.p_rew * MICRO_TO_SECOND_CONVERSION) /
                time_step_us))
        # write s_max
        spec.write_value(data=int(self.s_max))
        # write total number of atoms in the application vertex
        spec.write_value(data=app_vertex.n_atoms)
        # write local low, high and number of atoms
        spec.write_value(data=vertex_slice.n_atoms)
        spec.write_value(data=vertex_slice.lo_atom)
        spec.write_value(data=vertex_slice.hi_atom)
        # write with_replacement
        spec.write_value(data=self.with_replacement)

        # write app level seeds
        spec.write_array(self._get_seeds(app_vertex))

        # write local seed (4 words), generated randomly!
        # Note that in case of a reset, these need a key to ensure subsequent
        # runs match the first run
        spec.write_array(self._get_seeds(vertex_slice))

        # write the number of pre-populations
        spec.write_value(data=n_pre_pops)

    def __write_prepopulation_info(
            self, spec: DataSpecificationBase,
            app_vertex: ApplicationVertex,
            structural_projections: Iterable[Projection],
            weight_scales: NDArray[numpy.floating],
            synaptic_matrices: SynapticMatrices) -> Tuple[
                _PopIndexType, _SubpopIndexType, _SubpopIndexType]:
        """
        :param ~data_specification.DataSpecificationGenerator spec:
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            the vertex for which data specs are being prepared
        :param structural_projections: Projections that are structural
        :param machine_edges_by_app:
            map of application edge to associated machine edges
        :type machine_edges_by_app:
            dict(~pacman.model.graphs.application.ApplicationEdge,
            list(~pacman.model.graphs.machine.MachineEdge))
        :param dict(int,float) weight_scales:
        :param SynapticMatrices synaptic_matrices:
        :rtype: dict(tuple(AbstractPopulationVertex,SynapseInformation),int)
        """
        spec.comment("Writing pre-population info")
        pop_index: _PopIndexType = dict()
        routing_info = SpynnakerDataView.get_routing_infos()
        subpop_index: _SubpopIndexType = dict()
        lo_atom_index: _SubpopIndexType = dict()
        index = 0
        for proj in structural_projections:
            spec.comment(f"Writing pre-population info for {proj.label}")
            # pylint: disable=protected-access
            app_edge = proj._projection_edge
            synapse_info = proj._synapse_information
            pop_index[app_edge.pre_vertex, synapse_info] = index
            index += 1
            dynamics = synapse_info.synapse_dynamics

            # Number of incoming vertices
            out_verts = app_edge.pre_vertex.splitter.get_out_going_vertices(
                SPIKE_PARTITION_ID)
            spec.write_value(len(out_verts), data_type=DataType.UINT16)

            # Controls - currently just if this is a self connection or not
            self_connected = app_vertex == app_edge.pre_vertex
            spec.write_value(int(self_connected), data_type=DataType.UINT16)
            # Delay
            delay_scale = SpynnakerDataView.get_simulation_time_step_per_ms()
            if isinstance(dynamics.initial_delay, tuple):
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
            for sub, m_vertex in enumerate(out_verts):
                r_info = routing_info.get_routing_info_from_pre_vertex(
                    m_vertex, SPIKE_PARTITION_ID)
                assert r_info is not None
                vertex_slice = m_vertex.vertex_slice
                spec.write_value(r_info.key)
                spec.write_value(r_info.mask)
                out_app = m_vertex.app_vertex
                assert isinstance(out_app, PopulationApplicationVertex)
                spec.write_value(out_app.n_colour_bits)
                spec.write_value(vertex_slice.n_atoms)
                spec.write_value(vertex_slice.lo_atom)
                spec.write_value(synaptic_matrices.get_index(
                    app_edge, synapse_info))
                lo = vertex_slice.lo_atom
                for i in range(lo, vertex_slice.hi_atom + 1):
                    subpop_index[app_edge.pre_vertex, synapse_info, i] = sub
                    lo_atom_index[app_edge.pre_vertex, synapse_info, i] = lo
        return pop_index, subpop_index, lo_atom_index

    def __write_post_to_pre_table(
            self, spec: DataSpecificationBase, pop_index: _PopIndexType,
            subpop_index: _SubpopIndexType, lo_atom_index: _SubpopIndexType,
            app_vertex: AbstractPopulationVertex, vertex_slice: Slice):
        """
        Post to pre table is basically the transpose of the synaptic matrix.

        :param ~data_specification.DataSpecificationGenerator spec:
        :param pop_index:
        :type pop_index:
            dict(tuple(AbstractPopulationVertex,SynapseInformation), int)
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            the vertex for which data specs are being prepared
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The target slice
        """
        # pylint: disable=unsubscriptable-object
        # Get connections for this post slice
        slice_conns = self.connections[app_vertex, vertex_slice.lo_atom]
        # Make a single large array of connections
        connections = numpy.concatenate(
            [conn for (conn, _, _) in slice_conns])
        # Make a single large array of population index
        conn_lens = [len(conn) for (conn, _, _) in slice_conns]
        for (_, a_edge, s_info) in slice_conns:
            if (a_edge.pre_vertex, s_info) not in pop_index:
                print("Help!")
        pop_indices = numpy.repeat(
            [pop_index[a_edge.pre_vertex, s_info]
             for (_, a_edge, s_info) in slice_conns], conn_lens)
        # Make a single large array of sub-population index
        subpop_indices = numpy.array([
            subpop_index[a_edge.pre_vertex, s_info, c["source"]]
            for (conns, a_edge, s_info) in slice_conns for c in conns])
        # Get the low atom for each source and subtract
        lo_atoms = numpy.array([
            lo_atom_index[a_edge.pre_vertex, s_info, c["source"]]
            for (conns, a_edge, s_info) in slice_conns for c in conns])
        connections["source"] = connections["source"] - lo_atoms

        # Make an array of all data required
        conn_data = numpy.dstack(
            (pop_indices, subpop_indices, connections["source"]))[0]

        # Break data into rows based on target and strip target out
        rows = [conn_data[connections["target"] == i]
                for i in range(0, vertex_slice.n_atoms)]

        if any(len(row) > self.s_max for row in rows):
            raise ValueError(
                "Too many initial connections per incoming neuron")

        # Make each row the required length through padding with 0xFFFF
        padded_rows = [numpy.pad(row, [(self.s_max - len(row), 0), (0, 0)],
                                 "constant", constant_values=0xFFFF)
                       for row in rows]

        # Finally make the table and write it out
        post_to_pre = numpy.rec.fromarrays(
            numpy.concatenate(padded_rows).T, formats="u1, u1, u2").view("u4")
        if len(post_to_pre) != vertex_slice.n_atoms * self.s_max:
            raise ValueError(
                f"Wrong size of pre-to-pop tables: {len(post_to_pre)} "
                f"Found, {vertex_slice.n_atoms * self.s_max} Expected")
        spec.comment(
            "Writing post-to-pre table of "
            f"{vertex_slice.n_atoms * self.s_max} words")
        spec.write_array(post_to_pre)

    @overrides(AbstractSynapseDynamicsStructural.
               get_structural_parameters_sdram_usage_in_bytes)
    def get_structural_parameters_sdram_usage_in_bytes(
            self, incoming_projections: Iterable[Projection],
            n_neurons: int) -> int:
        # Work out how many sub-edges we will end up with, as this is used
        # for key_atom_info
        # pylint: disable=no-member
        param_sizes = (
            self.partner_selection.get_parameters_sdram_usage_in_bytes())
        n_sub_edges = 0
        structural_projections = self.__get_structural_projections(
            incoming_projections)
        for proj in structural_projections:
            # pylint: disable=protected-access
            dynamics = proj._synapse_information.synapse_dynamics
            app_edge = proj._projection_edge
            n_sub_edges += len(
                app_edge.pre_vertex.splitter.get_out_going_slices())
            param_sizes += dynamics.formation\
                .get_parameters_sdram_usage_in_bytes()
            param_sizes += dynamics.elimination\
                .get_parameters_sdram_usage_in_bytes()

        return int(
            self._REWIRING_DATA_SIZE +
            (self._PRE_POP_INFO_BASE_SIZE * len(structural_projections)) +
            (self._KEY_ATOM_INFO_SIZE * n_sub_edges) +
            (self._POST_TO_PRE_ENTRY_SIZE * n_neurons * self.s_max) +
            param_sizes)

    def get_vertex_executable_suffix(self) -> str:
        """
        :rtype: str
        """
        name = "_structural"
        # pylint: disable=no-member
        name += self.partner_selection.vertex_executable_suffix
        name += self.formation.vertex_executable_suffix
        name += self.elimination.vertex_executable_suffix
        return name

    def is_same_as(
            self, synapse_dynamics: AbstractSynapseDynamicsStructural) -> bool:
        """
        :param SynapseDynamicsStructuralCommon synapse_dynamics:
        :rtype: bool
        """
        # Note noqa:E721  because exact type comparison is required here
        return (
            self.s_max == synapse_dynamics.s_max and
            self.f_rew == synapse_dynamics.f_rew and
            self.initial_weight == synapse_dynamics.initial_weight and
            self.initial_delay == synapse_dynamics.initial_delay and
            # pylint: disable=unidiomatic-typecheck
            (type(self.partner_selection) ==  # noqa: E721
             type(synapse_dynamics.partner_selection)) and
            (type(self.formation) ==
             type(synapse_dynamics.formation)) and
            (type(self.elimination) ==
             type(synapse_dynamics.elimination)))

    @property
    @abstractmethod
    def connections(self) -> ConnectionsInfo:
        """
        Initial connectivity as defined via connector.

        :rtype: dict
        """
        raise NotImplementedError

    @abstractmethod
    def _get_seeds(
            self, app_vertex: Union[None, ApplicationVertex, Slice] = None
            ) -> Sequence[int]:
        """
        Generate a seed for the RNG on chip that is the same for all
        of the cores that have perform structural updates.

        It should be different between application vertices
        but the same for the same app_vertex.
        It should be different every time called with `None`.

        :param app_vertex:
        :type app_vertex:
            ~pacman.model.graphs.application.ApplicationVertex or None
        :return: list of random seed (4 words), generated randomly
        :rtype: list(int)
        """
        raise NotImplementedError

    def check_initial_delay(self, max_delay_ms: float):
        """
        Check that delays can be done without delay extensions.

        :param float max_delay_ms: The maximum delay supported, in milliseconds
        :raises ValueError: if the delay is out of range
        """
        if isinstance(self.initial_delay, tuple):
            # pylint: disable=unsubscriptable-object
            init_del = self.initial_delay
            if init_del[0] > max_delay_ms or init_del[1] > max_delay_ms:
                raise ValueError(
                    f"The initial delay {self.initial_delay} has one or more "
                    f"values that are bigger than {max_delay_ms}.")
        elif self.initial_delay > max_delay_ms:
            raise ValueError(
                f"The initial delay {self.initial_delay} "
                f"is bigger than {max_delay_ms}.")

    def get_max_rewires_per_ts(self) -> int:
        max_rewires_per_ts = 1
        if (self.p_rew * MICRO_TO_MILLISECOND_CONVERSION <
                SpynnakerDataView.get_simulation_time_step_ms()):
            # fast rewiring, so need to set max_rewires_per_ts
            max_rewires_per_ts = int(
                SpynnakerDataView.get_simulation_time_step_us() / (
                        self.p_rew * MICRO_TO_SECOND_CONVERSION))

        return max_rewires_per_ts
