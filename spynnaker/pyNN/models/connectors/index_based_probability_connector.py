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

from spynnaker.pyNN.models.neural_projections.connectors import (
    IndexBasedProbabilityConnector as CommonIndexBasedProbabilityConnector)


class IndexBasedProbabilityConnector(CommonIndexBasedProbabilityConnector):
    """
    Create an index-based probability connector.
    The index_expression must depend on the indices i, j of the populations.

    :param index_expression: a function of the indices of the populations
        An expression
    :type index_expression: str
    :param allow_self_connections: allow a neuron to connect to itself
    :type allow_self_connections: bool
    """
    __slots__ = []

    def __init__(
            self, index_expression, allow_self_connections=True, rng=None,
            safe=True, callback=None, verbose=False):
        # pylint: disable=too-many-arguments
        super(IndexBasedProbabilityConnector, self).__init__(
            index_expression=index_expression,
            allow_self_connections=allow_self_connections, rng=rng,
            safe=safe, callback=callback, verbose=verbose)
