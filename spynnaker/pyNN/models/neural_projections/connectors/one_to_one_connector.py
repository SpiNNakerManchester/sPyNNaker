# Copyright (c) 2014 The University of Manchester
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
import math
from typing import Optional, Sequence, Tuple, TYPE_CHECKING

import numpy
from numpy import integer, floating, uint32
from numpy.typing import NDArray

from pyNN.random import RandomDistribution

from spinn_utilities.overrides import overrides
from spinn_utilities.safe_eval import SafeEval

from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice

from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import SynapseInformation

_expr_context = SafeEval(
    math, numpy, numpy.arccos, numpy.arcsin, numpy.arctan, numpy.arctan2,
    numpy.ceil, numpy.cos, numpy.cosh, numpy.exp, numpy.fabs, numpy.floor,
    numpy.fmod, numpy.hypot, numpy.ldexp, numpy.log, numpy.log10, numpy.modf,
    numpy.power, numpy.sin, numpy.sinh, numpy.sqrt, numpy.tan, numpy.tanh,
    numpy.maximum, numpy.minimum, e=numpy.e, pi=numpy.pi)


class OneToOneConnector(AbstractGenerateConnectorOnMachine,
                        AbstractGenerateConnectorOnHost):
    """
    Where the pre- and postsynaptic populations have the same size,
    connect cell *i* in the presynaptic population to cell *i* in
    the postsynaptic population, for all *i*.
    """
    __slots__ = ()

    def __init__(self, safe=True, callback=None, verbose=False) -> None:
        """
        :param bool safe:
            If ``True``, check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        # pylint: disable=useless-super-delegation
        super().__init__(safe, callback, verbose)

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        return self._get_delay_maximum(
            synapse_info.delays,
            max(synapse_info.n_pre_neurons, synapse_info.n_post_neurons),
            synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        return self._get_delay_minimum(
            synapse_info.delays,
            max(synapse_info.n_pre_neurons, synapse_info.n_post_neurons),
            synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        delays = synapse_info.delays

        if min_delay is None or max_delay is None or delays is None:
            return 1

        if isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            delays = _expr_context.eval(delays, d=d)
            if ((min_delay <= min(delays) <= max_delay) and (
                    min_delay <= max(delays) <= max_delay)):
                return 1
            else:
                return 0
        if isinstance(delays, (int, float, integer, floating)):
            return int(min_delay <= delays <= max_delay)
        if isinstance(delays, RandomDistribution):
            return 1

        slice_min_delay = min(delays)
        slice_max_delay = max(delays)
        return int((min_delay <= slice_max_delay <= max_delay) or
                   (min_delay <= slice_min_delay <= max_delay))

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        return 1

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        return self._get_weight_maximum(
            synapse_info.weights,
            max(synapse_info.n_pre_neurons, synapse_info.n_post_neurons),
            synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        # Get each pre_vertex id for each post_vertex id
        post_atoms = post_vertex_slice.get_raster_ids()
        pre_atoms = numpy.array(post_atoms)

        # Filter out things where there isn't a cross over
        atom_filter = numpy.ones(len(post_atoms), dtype=numpy.bool_)
        if synapse_info.prepop_is_view or synapse_info.postpop_is_view:
            # If a view, we only keep things that are in the view
            if synapse_info.prepop_is_view:
                # pylint: disable=protected-access
                pre_lo, pre_hi = synapse_info.pre_population._view_range
                atom_filter &= (pre_atoms <= pre_hi & pre_atoms >= pre_lo)
            if synapse_info.postpop_is_view:
                # pylint: disable=protected-access
                post_lo, post_hi = synapse_info.post_population._view_range
                atom_filter &= (post_atoms <= post_hi & post_atoms >= post_lo)
        else:
            # If not a view we only keep things that are in the pre-population
            atom_filter &= (pre_atoms <= synapse_info.pre_population.size)
        post_atoms = post_atoms[atom_filter]
        pre_atoms = pre_atoms[atom_filter]

        # Convert to the correct coordinates
        post_atoms = post_vertex_slice.get_relative_indices(post_atoms)
        pre_atoms = synapse_info.pre_vertex.get_key_ordered_indices(pre_atoms)

        n_connections = len(post_atoms)
        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = pre_atoms
        block["target"] = post_atoms
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "OneToOneConnector()"

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self) -> int:
        return ConnectorIDs.ONE_TO_ONE_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(
            self, synapse_info: SynapseInformation) -> NDArray[uint32]:
        return numpy.array([], dtype="uint32")

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self) -> int:
        return 0

    @overrides(AbstractGenerateConnectorOnMachine.get_connected_vertices)
    def get_connected_vertices(
            self, s_info: SynapseInformation, source_vertex: ApplicationVertex,
            target_vertex: ApplicationVertex) -> Sequence[
                Tuple[MachineVertex, Sequence[MachineVertex]]]:
        src_vtxs = source_vertex.splitter.get_out_going_vertices(
            SPIKE_PARTITION_ID)
        tgt_vtxs = target_vertex.splitter.get_in_coming_vertices(
            SPIKE_PARTITION_ID)

        # If doing a view, we must be single dimensional, so use old method
        if s_info.prepop_is_view or s_info.postpop_is_view:

            # Check again here in case the rules change elsewhere
            if (len(s_info.pre_vertex.atoms_shape) > 1 or
                    len(s_info.post_vertex.atoms_shape) > 1):
                raise ConfigurationException(
                    "The OneToOneConnector does not support PopulationView "
                    "connections between vertices with more than 1 dimension")

            pre_lo = 0
            pre_hi = source_vertex.n_atoms - 1
            post_lo = 0
            post_hi = target_vertex.n_atoms - 1
            if s_info.prepop_is_view:
                # pylint: disable=protected-access
                pre_lo, pre_hi = s_info.pre_population._view_range
            if s_info.postpop_is_view:
                # pylint: disable=protected-access
                post_lo, post_hi = s_info.post_population._view_range

            return [(t_vert,
                     [s_vert for s_vert in src_vtxs if self.__connects(
                          s_vert, pre_lo, pre_hi, t_vert, post_lo, post_hi)])
                    for t_vert in tgt_vtxs]

        # Check for cross over of pre- and post- rasters, as that is how the
        # connector works
        return [(t_vert,
                 [s_vert for s_vert in src_vtxs if any(numpy.isin(
                     s_vert.vertex_slice.get_raster_ids(),
                     t_vert.vertex_slice.get_raster_ids()))])
                for t_vert in tgt_vtxs]

    def __connects(
            self, s_vert: MachineVertex, pre_lo: int, pre_hi: int,
            t_vert: MachineVertex, post_lo: int, post_hi: int) -> bool:
        pre_slice = s_vert.vertex_slice
        post_slice = t_vert.vertex_slice

        # Check range of slices
        if pre_slice.hi_atom < pre_lo:
            return False
        if post_slice.hi_atom < post_lo:
            return False
        if pre_slice.lo_atom > pre_hi:
            return False
        if post_slice.lo_atom > post_hi:
            return False

        # Get slice range relative to view
        pre_s_hi = pre_slice.hi_atom - pre_lo
        post_s_hi = post_slice.hi_atom - post_lo
        pre_s_lo = pre_slice.lo_atom - pre_lo
        post_s_lo = post_slice.lo_atom - post_lo

        if pre_s_hi < post_s_lo:
            return False
        if pre_s_lo > post_s_hi:
            return False

        return True

    @overrides(AbstractGenerateConnectorOnMachine.generate_on_machine)
    def generate_on_machine(self, synapse_info: SynapseInformation) -> bool:
        # If we are doing a 1:1 connector and the pre or post vertex is
        # multi-dimensional and have different dimensions
        pre = synapse_info.pre_vertex
        post = synapse_info.post_vertex
        if len(pre.atoms_shape) > 1 or len(post.atoms_shape) > 1:
            if (pre.atoms_shape != post.atoms_shape):
                print("Not generating on core!")
                return False
            if (pre.get_max_atoms_per_dimension_per_core() !=
                    post.get_max_atoms_per_dimension_per_core()):
                print("Not generating on core!")
                return False
        return super(OneToOneConnector, self).generate_on_machine(synapse_info)
