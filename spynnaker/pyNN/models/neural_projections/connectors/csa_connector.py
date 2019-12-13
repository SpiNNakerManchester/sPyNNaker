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
try:
    import csa
    _csa_found = (True, ImportError)
except ImportError as _ex:  # noqa: F821
    # Importing csa causes problems with readthedocs so allowing it to fail
    _csa_found = (False, _ex)

logger = logging.getLogger(__name__)


class CSAConnector(AbstractConnector):
    """ Make connections using a Connection Set Algebra (Djurfeldt 2012)\
        description between the neurons in the pre- and post-populations.
        If you get TypeError in Python 3 see:
        https://github.com/INCF/csa/issues/10
    """

    __slots = [
        "__cset", "__full_connection_set", "__full_cset"]

    def __init__(self, cset, safe=True, callback=None, verbose=False):
        """
        :param '?' cset:
            A description of the connection set between populations
        """
        super(CSAConnector, self).__init__(safe, callback, verbose)
        found, ex = _csa_found
        if not found:
            raise ex
        self.__cset = cset

        # Storage for full connection sets
        self.__full_connection_set = None
        self.__full_cset = None

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(self, synapse_info):
        n_conns_max = synapse_info.n_pre_neurons * synapse_info.n_post_neurons
        # we can probably look at the array and do better than this?
        return self._get_delay_maximum(synapse_info.delays, n_conns_max)

    def _get_n_connections(self, pre_vertex_slice, post_vertex_slice,
                           synapse_info):
        # do the work from self._cset in here
        # get the values for this slice
        pre_lo = pre_vertex_slice.lo_atom
        pre_hi = pre_vertex_slice.hi_atom
        post_lo = post_vertex_slice.lo_atom
        post_hi = post_vertex_slice.hi_atom

        # this is where the magic needs to happen somehow
        if self.__full_cset is None:
            self.__full_cset = [x for x in csa.cross(
                range(synapse_info.n_pre_neurons),
                range(synapse_info.n_post_neurons)) * self.__cset]

        # use CSA to cross the range of this vertex's neurons with the cset
        pair_list = csa.cross(
            range(pre_lo, pre_hi+1),
            range(post_lo, post_hi+1)) * self.__full_cset

        if self.verbose:
            print('full cset: ', self.__full_cset)
            print('this vertex pair_list: ', pair_list)
            print('this vertex pre_neurons: ',
                  [x[0] for x in pair_list])
            print('this vertex post_neurons: ',
                  [x[1] for x in pair_list])

        n_connections = len(pair_list)  # size of the array created
        return n_connections, pair_list

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, post_vertex_slice, synapse_info, min_delay=None,
            max_delay=None):
        n_connections_max = post_vertex_slice.n_atoms

        return self._get_n_connections_from_pre_vertex_with_delay_maximum(
            synapse_info.delays,
            synapse_info.n_pre_neurons * synapse_info.n_post_neurons,
            n_connections_max, min_delay, max_delay)

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        n_connections_max = synapse_info.n_pre_neurons
        return n_connections_max

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info):
        n_conns_max = synapse_info.n_pre_neurons * synapse_info.n_post_neurons
        return self._get_weight_maximum(synapse_info.weights, n_conns_max)

    @overrides(AbstractConnector.create_synaptic_block)
    def create_synaptic_block(
            self, pre_slices, pre_slice_index, post_slices,
            post_slice_index, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        n_connections, pair_list = self._get_n_connections(
            pre_vertex_slice, post_vertex_slice, synapse_info)

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
        block["source"] = [x[0] for x in pair_list]
        block["target"] = [x[1] for x in pair_list]
        block["weight"] = self._generate_weights(
            n_connections, None, pre_vertex_slice, post_vertex_slice,
            synapse_info)
        block["delay"] = self._generate_delays(
            n_connections, None, pre_vertex_slice, post_vertex_slice,
            synapse_info)
        block["synapse_type"] = synapse_type
        return block

    def show_connection_set(self, n_pre_neurons, n_post_neurons):
        # Yuck; this was supposed to be available to the user from scripts...
        csa.show(self.__full_connection_set, n_pre_neurons, n_post_neurons)

    def __repr__(self):
        return "CSAConnector({})".format(
            self.__full_cset)
