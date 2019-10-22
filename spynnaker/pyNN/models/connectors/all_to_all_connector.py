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
from pyNN.connectors import AllToAllConnector as PyNNAllToAllConnector
from spynnaker.pyNN.models.neural_projections.connectors import (
    AllToAllConnector as CommonAllToAllConnector)

logger = logging.getLogger(__file__)


class AllToAllConnector(CommonAllToAllConnector, PyNNAllToAllConnector):
    """ Connects all cells in the presynaptic population to all cells in \
        the postsynaptic population
    """
    __slots__ = []

    def __init__(
            self, allow_self_connections=True, safe=True,
            verbose=None, callbacks=None):
        """
        :param allow_self_connections: \
            if the connector is used to connect a Population to itself, this\
            flag determines whether a neuron is allowed to connect to itself,\
            or only to other neurons in the Population.
        :type allow_self_connections: bool
        :param safe: if True, check that weights and delays have valid\
            values. If False, this check is skipped.
        :param verbose:
        :param callbacks:
        """
        CommonAllToAllConnector.__init__(
            self, allow_self_connections=allow_self_connections,
            safe=safe, verbose=verbose)
        PyNNAllToAllConnector.__init__(
            self, allow_self_connections=allow_self_connections, safe=safe,
            callback=callbacks)
