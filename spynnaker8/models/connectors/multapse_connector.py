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
    MultapseConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class MultapseConnector(_BaseClass):
    """
    Create a multapse connector. The size of the source and destination\
    populations are obtained when the projection is connected. The number of\
    synapses is specified. when instantiated, the required number of synapses\
    is created by selecting at random from the source and target populations\
    *with replacement* (by default). Uniform selection probability is assumed.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.MultapseConnector`
        instead.
    """
    __slots__ = []

    def __init__(self, n, allow_self_connections=True,
                 with_replacement=True, safe=True, verbose=False,
                 rng=None):
        """
        :param int n: This is the total number of synapses in the connection.
        :param bool allow_self_connections:
            Allow a neuron to connect to itself or not.
        :param bool with_replacement:
            When selecting, allow a neuron to be re-selected or not.
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If False, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param rng: random number generator
        :type rng: ~pyNN.random.NumpyRNG or None
        """
        moved_in_v6("spynnaker8.models.connectors.MultapseConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors."
                    "MultapseConnector")
        super(MultapseConnector, self).__init__(
            n=n, allow_self_connections=allow_self_connections,
            with_replacement=with_replacement, safe=safe, verbose=verbose,
            rng=rng)
