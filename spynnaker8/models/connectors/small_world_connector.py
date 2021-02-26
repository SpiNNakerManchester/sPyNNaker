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
    SmallWorldConnector as
    _BaseClass)
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class SmallWorldConnector(_BaseClass):
    """ Create a connector that uses connection statistics based on the\
        Small World network connectivity model. Note that this is typically\
        used from a population to itself.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.neural_projections.connectors.SmallWorldConnector`
        instead.
    """
    __slots__ = []

    def __init__(
            self, degree, rewiring, allow_self_connections=True,
            n_connections=None, rng=None, safe=True, callback=None,
            verbose=False):
        """
        :param float degree:
            the region length where nodes will be connected locally
        :param float rewiring: the probability of rewiring each edge
        :param bool allow_self_connections:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
        :param n_connections:
            if specified, the number of efferent synaptic connections per
            neuron
        :type n_connections: int or None
        :param rng: random number generator
        :type rng: ~pyNN.random.NumpyRNG or None
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If False, this check is skipped.
        :param callable callback: For PyNN compatibility only.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.connectors.SmallWorldConnector",
                    "spynnaker.pyNN.models.neural_projections.connectors."
                    "SmallWorldConnector")
        super(SmallWorldConnector, self).__init__(
            degree=degree, rewiring=rewiring,
            allow_self_connections=allow_self_connections,
            n_connections=n_connections, rng=rng, safe=safe, callback=callback,
            verbose=verbose)
