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

import logging
from pyNN.connectors import (
    FixedNumberPostConnector as PyNNFixedNumberPostConnector)
from spynnaker.pyNN.models.neural_projections.connectors import (
    FixedNumberPostConnector as CommonFixedNumberPostConnector)

logger = logging.getLogger(__file__)


class FixedNumberPostConnector(CommonFixedNumberPostConnector,
                               PyNNFixedNumberPostConnector):
    """ PyNN connector that puts a fixed number of connections on each of the\
        post neurons
    """
    __slots__ = []

    def __init__(
            self, n, allow_self_connections=True, safe=True, verbose=False,
            with_replacement=False, rng=None, callback=None):
        """

        :param n: \
            number of random post-synaptic neurons connected to pre-neurons
        :type n: int
        :param allow_self_connections: \
            if the connector is used to connect a Population to itself, this\
            flag determines whether a neuron is allowed to connect to itself,\
            or only to other neurons in the Population.
        :type allow_self_connections: bool
        :param safe: \
            Whether to check that weights and delays have valid values;\
            if False, this check is skipped.
        :type safe: bool
        :param verbose: \
            Whether to output extra information about the connectivity to a\
            CSV file
        :type verbose: bool
        :param with_replacement: \
            if False, once a connection is made, it can't be made again;\
            if True, multiple connections between the same pair of neurons\
            are allowed
        :type with_replacement: bool
        :param rng: random number generator
        :param callback: list of callbacks to run
        """
        # pylint: disable=too-many-arguments
        super(FixedNumberPostConnector, self).__init__(
            n=n, allow_self_connections=allow_self_connections,
            with_replacement=with_replacement, safe=safe, verbose=verbose,
            rng=rng)
