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
    FixedNumberPreConnector as _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class FixedNumberPreConnector(_BaseClass):
    """ Connects a fixed number of pre-synaptic neurons selected at random,\
        to all post-synaptic neurons.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.FixedNumberPreConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, n, allow_self_connections=True, safe=True, verbose=False,
            with_replacement=False, rng=None, callback=None):
        """
        :param int n:
            number of random pre-synaptic neurons connected to post-neurons
        :param bool allow_self_connections:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If False, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param bool with_replacement:
            if False, once a connection is made, it can't be made again; if
            True, multiple connections between the same pair of neurons are
            allowed
        :param rng: random number generator
        :type rng: ~pyNN.random.NumpyRNG or None
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.connectors.FixedNumberPreConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors"
                    ".FixedNumberPreConnector")
        super(FixedNumberPreConnector, self).__init__(
            n=n, allow_self_connections=allow_self_connections,
            with_replacement=with_replacement, safe=safe, verbose=verbose,
            rng=rng)
