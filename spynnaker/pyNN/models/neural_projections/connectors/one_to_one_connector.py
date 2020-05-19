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

import logging
import numpy
from spinn_utilities.overrides import overrides
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_machine import (
    AbstractGenerateConnectorOnMachine, ConnectorIDs)
from .abstract_connector_supports_views_on_machine import (
    AbstractConnectorSupportsViewsOnMachine)

logger = logging.getLogger(__name__)


class OneToOneConnector(AbstractGenerateConnectorOnMachine,
                        AbstractConnectorSupportsViewsOnMachine):
    """ Where the pre- and postsynaptic populations have the same size,\
        connect cell i in the presynaptic pynn_population.py to cell i in the\
        postsynaptic pynn_population.py for all i.
    """
    __slots__ = ["__random_number_class"]

    def __init__(self, random_number_class,
                 safe=True, callback=None, verbose=False):
        """
        """
        self.__random_number_class = random_number_class
        super(OneToOneConnector, self).__init__(safe, callback, verbose)

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        return self._get_delay_maximum(
            synapse_info.delays,
            max((synapse_info.n_pre_neurons, synapse_info.n_post_neurons)))

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        # pylint: disable=too-many-arguments
        if min_delay is None or max_delay is None:
            return 1

        delays = synapse_info.delays

        if numpy.isscalar(delays):
            if delays >= min_delay and delays <= max_delay:
                return 1
            return 0
        if isinstance(delays, self.__random_number_class):
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
            max((synapse_info.n_pre_neurons, synapse_info.n_post_neurons)))

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        # pylint: disable=too-many-arguments
        pre_lo, post_lo, pre_hi, post_hi = self._get_pre_post_limits(
            pre_vertex_slice, post_vertex_slice, synapse_info)

        max_lo_atom = max((pre_lo, post_lo))
        min_hi_atom = min((pre_hi, post_hi))

        n_connections = max((0, (min_hi_atom - max_lo_atom) + 1))
        if n_connections <= 0:
            return numpy.zeros(0, dtype=self.NUMPY_SYNAPSES_DTYPE)
        connection_slice = slice(max_lo_atom, min_hi_atom + 1)
        block = numpy.zeros(n_connections, dtype=self.NUMPY_SYNAPSES_DTYPE)
        block["source"] = numpy.arange(max_lo_atom, min_hi_atom + 1)
        block["target"] = numpy.arange(max_lo_atom, min_hi_atom + 1)
        block["weight"] = self._generate_weights(
            n_connections, [connection_slice], pre_vertex_slice,
            post_vertex_slice, synapse_info)
        block["delay"] = self._generate_delays(
            n_connections, [connection_slice], pre_vertex_slice,
            post_vertex_slice, synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def __repr__(self):
        return "OneToOneConnector()"

    def _get_pre_post_limits(
            self, pre_vertex_slice, post_vertex_slice, synapse_info):
        if synapse_info.prepop_is_view:
            # work out which atoms are on this pre-slice
            view_lo, view_hi = self.get_view_lo_hi(
                synapse_info.pre_population._indexes)
            if ((view_lo > pre_vertex_slice.lo_atom) and
                    (view_lo < pre_vertex_slice.hi_atom)):
                pre_lo = view_lo
            else:
                pre_lo = pre_vertex_slice.lo_atom
            if ((view_hi > pre_vertex_slice.lo_atom) and
                    (view_hi < pre_vertex_slice.hi_atom)):
                pre_hi = view_hi
            else:
                pre_hi = pre_vertex_slice.hi_atom
        else:
            pre_lo = pre_vertex_slice.lo_atom
            pre_hi = pre_vertex_slice.hi_atom

        if synapse_info.postpop_is_view:
            # work out which atoms are on this post-slice
            view_lo, view_hi = self.get_view_lo_hi(
                synapse_info.post_population._indexes)
            if ((view_lo > post_vertex_slice.lo_atom) and
                    (view_lo < post_vertex_slice.hi_atom)):
                post_lo = view_lo
            else:
                post_lo = post_vertex_slice.lo_atom
            if ((view_hi > post_vertex_slice.lo_atom) and
                    (view_hi < post_vertex_slice.hi_atom)):
                post_hi = view_hi
            else:
                post_hi = post_vertex_slice.hi_atom
        else:
            post_lo = post_vertex_slice.lo_atom
            post_hi = post_vertex_slice.hi_atom

        return pre_lo, post_lo, pre_hi, post_hi

    @overrides(AbstractConnector.use_direct_matrix)
    def use_direct_matrix(self, synapse_info):
        if synapse_info.prepop_is_view or synapse_info.postpop_is_view:
            return False
        return True

    @property
    @overrides(AbstractGenerateConnectorOnMachine.gen_connector_id)
    def gen_connector_id(self):
        return ConnectorIDs.ONE_TO_ONE_CONNECTOR.value

    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params)
    def gen_connector_params(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        params = self._basic_connector_params(synapse_info)
        return numpy.array(params, dtype="uint32")

    @property
    @overrides(AbstractGenerateConnectorOnMachine.
               gen_connector_params_size_in_bytes)
    def gen_connector_params_size_in_bytes(self):
        return self._view_params_bytes
