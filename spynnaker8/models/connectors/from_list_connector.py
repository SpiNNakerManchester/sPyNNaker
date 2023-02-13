# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
