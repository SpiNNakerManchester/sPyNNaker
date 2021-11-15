# Copyright (c) 2017-2021 The University of Manchester
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
from spynnaker.pyNN.models.neural_projections.connectors import (
    FromListConnector as _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class FromListConnector(_BaseClass):
    """ Make connections according to a list.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.FromListConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, conn_list, safe=True, verbose=False, column_names=None,
            callback=None):
        """
        :param conn_list:
            a list of tuples, one tuple for each connection. Each tuple should
            contain: `(pre_idx, post_idx, p1, p2, ..., pn)` where `pre_idx` is
            the index (i.e. order in the Population, not the ID) of the
            presynaptic neuron, `post_idx` is the index of the postsynaptic
            neuron, and `p1`, `p2`, etc. are the synaptic parameters (e.g.,
            weight, delay, plasticity parameters).
        :type conn_list: list(tuple(int,int,...)) or ~numpy.ndarray
        :param bool safe:
            if True, check that weights and delays have valid values.
            If False, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param column_names:
            the names of the parameters `p1`, `p2`, etc. If not provided, it
            is assumed the parameters are `weight, delay` (for backwards
            compatibility).
        :type column_names: tuple(str) or list(str) or None
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        moved_in_v6("spynnaker8.models.connectors.FromListConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".FromListConnector")
        _BaseClass.__init__(
            self, conn_list=conn_list, safe=safe, verbose=verbose,
            column_names=column_names, callback=callback)
