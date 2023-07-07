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
    DistanceDependentProbabilityConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class DistanceDependentProbabilityConnector(_BaseClass):
    """
    Make connections using a distribution which varies with distance.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.DistanceDependentProbabilityConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, d_expression, allow_self_connections=True, safe=True,
            verbose=False, n_connections=None, rng=None, callback=None):
        """
        :param str d_expression:
            the right-hand side of a valid python expression for
            probability, involving `d`, e.g. ``"exp(-abs(d))"``, or ``"d<3"``,
            that can be parsed by :py:func:`eval`, that computes the distance
            dependent distribution
        :param bool allow_self_connections:
            if the connector is used to connect a
            Population to itself, this flag determines whether a neuron is
            allowed to connect to itself, or only to other neurons in the
            Population.
        :param bool safe: if True, check that weights and delays have valid
            values. If False, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param int n_connections:
            The number of efferent synaptic connections per neuron.
        :param ~pyNN.random.NumpyRNG rng: random number generator
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.connectors"
                    ".DistanceDependentProbabilityConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".DistanceDependentProbabilityConnector")
        _BaseClass.__init__(
            self, d_expression=d_expression,
            allow_self_connections=allow_self_connections,
            safe=safe, verbose=verbose, n_connections=n_connections)
