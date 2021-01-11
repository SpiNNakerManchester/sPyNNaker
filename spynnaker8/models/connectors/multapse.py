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

import numpy
from spynnaker.pyNN.models.neural_projections.connectors import (
    MultapseConnector as
    _BaseClass)
from spinn_utilities.overrides import overrides


class MultapseConnector(_BaseClass):
    """
    Create a multapse connector. The size of the source and destination\
    populations are obtained when the projection is connected. The number of\
    synapses is specified. when instantiated, the required number of synapses\
    is created by selecting at random from the source and target populations\
    _with replacement_ (by default). Uniform selection probability is assumed.
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
            Bool. When selecting, allow a neuron to be re-selected or not.
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If False, this check is skipped.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        :param rng: random number generator
        :type rng: ~pyNN.random.NumpyRNG or None
        """
        super(MultapseConnector, self).__init__(
            num_synapses=n, allow_self_connections=allow_self_connections,
            with_replacement=with_replacement, safe=safe, verbose=verbose,
            rng=rng)

    @overrides(_BaseClass.get_rng_next)
    def get_rng_next(self, num_synapses, prob_connect):
        # Below is how numpy does multinomial internally...
        size = len(prob_connect)
        multinomial = numpy.zeros(size, int)
        total = 1.0
        dn = num_synapses
        for j in range(0, size - 1):
            multinomial[j] = self._rng.next(
                1, distribution="binomial",
                parameters={'n': dn, 'p': prob_connect[j] / total})
            dn = dn - multinomial[j]
            if dn <= 0:
                break
            total = total - prob_connect[j]
        if dn > 0:
            multinomial[size - 1] = dn

        return multinomial
