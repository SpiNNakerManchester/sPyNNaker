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
from spynnaker.pyNN.models.neural_projections.connectors import (
    IndexBasedProbabilityConnector as _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class IndexBasedProbabilityConnector(_BaseClass):
    """
    Create an index-based probability connector.
    The `index_expression` must depend on the indices `i`, `j` of the
    populations.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.IndexBasedProbabilityConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, index_expression, allow_self_connections=True, rng=None,
            safe=True, callback=None, verbose=False):
        """
        :param str index_expression: A function of the indices of the
            populations, written as a Python expression; the indices will be
            given as variables ``i`` and ``j`` when the expression is
            evaluated.
        :param bool allow_self_connections:
            allow a neuron to connect to itself
        :param rng: random number generator
        :type rng: ~pyNN.random.NumpyRNG or None
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If False, this check is skipped.
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.connectors"
                    ".IndexBasedProbabilityConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".IndexBasedProbabilityConnector")
        super().__init__(
            index_expression=index_expression,
            allow_self_connections=allow_self_connections, rng=rng,
            safe=safe, callback=callback, verbose=verbose)
