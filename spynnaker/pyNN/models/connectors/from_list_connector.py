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

from spynnaker.pyNN.models.neural_projections.connectors import (
    FromListConnector as CommonFromListConnector)


class FromListConnector(CommonFromListConnector):
    """ Make connections according to a list.
    """
    __slots__ = []

    def __init__(
            self, conn_list, safe=True, verbose=False, column_names=None,
            callback=None):
        """
        :param conn_list: \
            a list of tuples, one tuple for each connection. Each tuple\
            should contain: `(pre_idx, post_idx, p1, p2, ..., pn)` where\
            `pre_idx` is the index (i.e. order in the Population, not the ID)\
            of the presynaptic neuron, `post_idx` is the index of the\
            postsynaptic neuron, and `p1`, `p2`, etc. are the synaptic\
            parameters (e.g., weight, delay, plasticity parameters).
        :param column_names: \
            the names of the parameters p1, p2, etc. If not provided, it is\
            assumed the parameters are weight, delay (for\
            backwards compatibility).
        :param safe: \
            if True, check that weights and delays have valid values. If\
            False, this check is skipped.
        :param callback: \
            if given, a callable that display a progress bar on the terminal.
        """
        CommonFromListConnector.__init__(
            self, conn_list=conn_list, safe=safe, verbose=verbose,
            column_names=column_names, callback=callback)
