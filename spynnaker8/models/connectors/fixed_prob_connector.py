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
