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
    FixedProbabilityConnector as _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class FixedProbabilityConnector(_BaseClass):
    """ For each pair of pre-post cells, the connection probability is \
        constant.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.FixedProbabilityConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, p_connect, allow_self_connections=True, safe=True,
            verbose=False, rng=None, callback=None):
        """
        :param float p_connect: a number between zero and one. Each potential
            connection is created with this probability.
        :param bool allow_self_connections: if the connector is used to
            connect a Population to itself, this flag determines whether a
            neuron is allowed to connect to itself, or only to other neurons
            in the Population.
        :param bool safe: if True, check that weights and delays have valid
            values. If False, this check is skipped.
        :param ~pyNN.space.Space space: a Space object, needed if you wish to
            specify distance-dependent weights or delays - not implemented
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param rng: random number generator
        :type rng: ~pyNN.random.NumpyRNG or None
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.connectors",
                    "spynnaker.pyNN.models.neural_projections.connectors")
        _BaseClass.__init__(
            self, p_connect=p_connect,
            allow_self_connections=allow_self_connections, safe=safe,
            verbose=verbose, rng=rng, callback=callback)
