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

import numpy
import math
from pyNN.random import RandomDistribution
from spinn_utilities.overrides import overrides
from spinn_utilities.safe_eval import SafeEval
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
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
    __slots__ = []

    def __init__(self, safe=True, callback=None, verbose=False):
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
    def get_delay_maximum(self, synapse_info):
        return self._get_delay_maximum(
            synapse_info.delays,
            max(synapse_info.n_pre_neurons, synapse_info.n_post_neurons),
            synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info):
        return self._get_delay_minimum(
            synapse_info.delays,
            max(synapse_info.n_pre_neurons, synapse_info.n_post_neurons),
            synapse_info)

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms, synapse_info, min_delay=None,
            max_delay=None):
        # pylint: disable=too-many-arguments
        if min_delay is None or max_delay is None:
            return 1

        delays = synapse_info.delays

        if isinstance(delays, str):
            d = self._get_distances(delays, synapse_info)
            delays = _expr_context.eval(delays, d=d)
            if ((min_delay <= min(delays) <= max_delay) and (
                    min_delay <= max(delays) <= max_delay)):
                return 1
            else:
                return 0
        if numpy.isscalar(delays):
            return int(min_delay <= delays <= max_delay)
        if isinstance(delays, RandomDistribution):
            return 1

        slice_min_delay = min(delays)
        slice_max_delay = max(delays)
        if ((min_delay <= slice_max_delay <= max_delay) or
                (min_delay <= slice_min_delay <= max_delay)):
            return 1

        return 0

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        return 1

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        return self._get_weight_maximum(
            synapse_info.weights,
            max(synapse_info.n_pre_neurons, synapse_info.n_post_neurons),
            synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices, post_vertex_slice, synapse_type, synapse_info):

        max_lo_atom = post_vertex_slice.lo_atom
        min_hi_atom = min(
            synapse_info.n_pre_neurons, post_vertex_slice.hi_atom)

        n_connections = max(0, (min_hi_atom - max_lo_atom) + 1)
        if n_connections <= 0:
            return numpy.zeros(0, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = numpy.arange(max_lo_atom, min_hi_atom + 1)
        block["target"] = numpy.arange(max_lo_atom, min_hi_atom + 1)
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
    def gen_connector_id(self):
        return ConnectorIDs.ONE_TO_ONE_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_params)
    def gen_connector_params(self):
        return numpy.array([], dtype="uint32")

    @property
    @overrides(
        AbstractGenerateConnectorOnMachine.gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return 0

    @overrides(AbstractGenerateConnectorOnMachine.get_connected_vertices)
    def get_connected_vertices(self, s_info, source_vertex, target_vertex):
        pre_lo = 0
        pre_hi = source_vertex.n_atoms - 1
        post_lo = 0
        post_hi = target_vertex.n_atoms - 1
        if s_info.prepop_is_view:
            # pylint: disable=protected-access
            pre_lo = s_info.pre_population._indexes[0]
            pre_hi = s_info.pre_population._indexes[-1]
        if s_info.postpop_is_view:
            # pylint: disable=protected-access
            post_lo = s_info.post_population._indexes[0]
            post_hi = s_info.post_population._indexes[-1]

        src_splitter = source_vertex.splitter
        return [(t_vert,
                 [s_vert for s_vert in src_splitter.get_out_going_vertices(
                              SPIKE_PARTITION_ID)
                  if self.__connects(
                      s_vert, pre_lo, pre_hi, t_vert, post_lo, post_hi)])
                for t_vert in target_vertex.splitter.get_in_coming_vertices(
                    SPIKE_PARTITION_ID)]

    def __connects(self, s_vert, pre_lo, pre_hi, t_vert, post_lo, post_hi):
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
