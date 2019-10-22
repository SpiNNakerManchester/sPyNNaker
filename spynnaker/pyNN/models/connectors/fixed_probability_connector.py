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

from pyNN.connectors import (
    FixedProbabilityConnector as PyNNFixedProbabilityConnector)
from spynnaker.pyNN.models.neural_projections.connectors import (
    FixedProbabilityConnector as CommonFixedProbabilityConnector)


class FixedProbabilityConnector(
        CommonFixedProbabilityConnector, PyNNFixedProbabilityConnector):
    """
    """
    __slots__ = []

    def __init__(
            self, p_connect, allow_self_connections=True, safe=True,
            verbose=False, rng=None, callback=None):
        """ For each pair of pre-post cells, the connection probability is\
            constant.

        :param p_connect: a number between zero and one. Each potential\
            connection is created with this probability.
        :type p_connect: float
        :param allow_self_connections: if the connector is used to connect a\
            Population to itself, this flag determines whether a neuron is\
            allowed to connect to itself, or only to other neurons in the\
            Population.
        :param safe: if True, check that weights and delays have valid\
            values. If False, this check is skipped.
        :param space: a Space object, needed if you wish to specify\
            distance-dependent weights or delays - not implemented
        :param verbose:
        :param rng:
        :param callback:
        """
        # pylint: disable=too-many-arguments
        CommonFixedProbabilityConnector.__init__(
            self, p_connect=p_connect,
            allow_self_connections=allow_self_connections, safe=safe,
            verbose=verbose, rng=rng)
        PyNNFixedProbabilityConnector.__init__(
            self, p_connect=p_connect, callback=callback,
            allow_self_connections=allow_self_connections, rng=rng, safe=safe)

    @property
    def p_connect(self):
        return self._p_connect

    @p_connect.setter
    def p_connect(self, new_value):
        self._p_connect = new_value
