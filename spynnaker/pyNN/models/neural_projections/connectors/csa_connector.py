# Copyright (c) 2017 The University of Manchester
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
import numpy
from numpy.typing import NDArray
from typing import List, Optional, Tuple, TYPE_CHECKING, Sequence
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import Slice
from .abstract_connector import AbstractConnector
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)
try:
    import csa  # type: ignore[import]
    _csa_import_error: Optional[ImportError] = None
except ImportError as __ex:
    # Importing csa causes problems with readthedocs so allowing it to fail
    _csa_import_error = __ex
if TYPE_CHECKING:
    from csa.connset import CSet  # type: ignore[import]
    from spynnaker.pyNN.models.neural_projections import SynapseInformation


class CSAConnector(AbstractConnector, AbstractGenerateConnectorOnHost):
    """
    Make connections using a Connection Set Algebra (Djurfeldt 2012)
    description between the neurons in the pre- and post-populations.

    .. note::
        If you get TypeError in Python 3 see:
        https://github.com/INCF/csa/issues/10
    """

    __slots__ = (
        "__cset",
        "__full_connection_set",
        "__full_cset")

    def __init__(self, cset: CSet, safe=True, callback=None, verbose=False):
        """
        :param csa.connset.CSet cset:
            A description of the connection set between populations
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
        :raises ImportError:
            if the `csa` library isn't present; it's tricky to install in
            some environments so we don't force it to be present unless you
            want to actually use this class.
        """
        super().__init__(safe, callback, verbose)
        if _csa_import_error:
            raise _csa_import_error
        self.__cset = cset

        # Storage for full connection sets
        self.__full_connection_set: Optional[List[CSet]] = None
        self.__full_cset: Optional[List[CSet]] = None

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info: SynapseInformation) -> float:
        n_conns_max = synapse_info.n_pre_neurons * synapse_info.n_post_neurons
        # we can probably look at the array and do better than this?
        return self._get_delay_maximum(
            synapse_info.delays, n_conns_max, synapse_info)

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(self, synapse_info: SynapseInformation) -> float:
        n_conns_max = synapse_info.n_pre_neurons * synapse_info.n_post_neurons
        # we can probably look at the array and do better than this?
        return self._get_delay_minimum(
            synapse_info.delays, n_conns_max, synapse_info)

    def _get_n_connections(
            self, post_vertex_slice: Slice,
            synapse_info: SynapseInformation) -> Tuple[int, CSet]:
        """
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param SynapseInformation synapse_info:
        :rtype: tuple(int, cset.connset.CSet)
        """
        # do the work from self._cset in here

        # this is where the magic needs to happen somehow
        if self.__full_cset is None:
            self.__full_cset = [x for x in csa.cross(
                range(synapse_info.n_pre_neurons),
                range(synapse_info.n_post_neurons)) * self.__cset]

        # use CSA to cross the range of this vertex's neurons with the cset
        pair_list = (
            csa.cross(
                range(synapse_info.n_pre_neurons),
                list(int(x) for x in post_vertex_slice.get_raster_ids()))
            * self.__full_cset)

        if self.verbose:
            print('full cset: ', self.__full_cset)
            print('this vertex pair_list: ', pair_list)
            print('this vertex pre_neurons: ', [x[0] for x in pair_list])
            print('this vertex post_neurons: ', [x[1] for x in pair_list])

        n_connections = len(pair_list)  # size of the array created
        return n_connections, pair_list

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        if min_delay is None or max_delay is None:
            raise ValueError("min_delay and max_delay must be supplied")
        n_connections_max = n_post_atoms
        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections_max, min_delay, max_delay, synapse_info)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        n_connections_max = synapse_info.n_pre_neurons
        return n_connections_max

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        n_conns_max = synapse_info.n_pre_neurons * synapse_info.n_post_neurons
        return self._get_weight_maximum(
            synapse_info.weights, n_conns_max, synapse_info)

    @overrides(AbstractGenerateConnectorOnHost.create_synaptic_block)
    def create_synaptic_block(
            self, post_slices: Sequence[Slice], post_vertex_slice: Slice,
            synapse_type: int, synapse_info: SynapseInformation) -> NDArray:
        n_connections, pair_list = self._get_n_connections(
            post_vertex_slice, synapse_info)

        # Use whatever has been set up in _get_n_connections here
        # to send into the block structure
        # TO DO: not sure this works with repeated connector, but
        #        what does a repeated connector mean in this context?
        if self.__full_connection_set is None:
            self.__full_connection_set = [x for x in pair_list]
        else:
            self.__full_connection_set += [x for x in pair_list]

        block = numpy.zeros(
            n_connections, dtype=AbstractConnector.NUMPY_SYNAPSES_DTYPE)
        # source and target are the pre_neurons and post_neurons in pair_list
        block["source"] = synapse_info.pre_vertex.get_key_ordered_indices(
            numpy.array([x[0] for x in pair_list]))
        block["target"] = post_vertex_slice.get_relative_indices(
            numpy.array([x[1] for x in pair_list]))
        block["weight"] = self._generate_weights(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            block["source"], block["target"], n_connections, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def show_connection_set(self, n_pre_neurons: int, n_post_neurons: int):
        """
        :param int n_pre_neurons:
        :param int n_post_neurons:
        """
        # Yuck; this was supposed to be available to the user from scripts...
        csa.show(self.__full_connection_set, n_pre_neurons, n_post_neurons)

    def __repr__(self):
        return f"CSAConnector({self.__full_cset})"
