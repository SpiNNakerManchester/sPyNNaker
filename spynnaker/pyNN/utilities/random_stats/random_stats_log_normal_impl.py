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

from scipy.stats import lognorm
from spynnaker.pyNN.utilities.random_stats import AbstractRandomStats


class RandomStatsLogNormalImpl(AbstractRandomStats):
    """ An implementation of AbstractRandomStats for log normal distributions
    """

    def _get_params(self, dist):
        return [dist.parameters['mu'], dist.parameters['sigma']]

    def cdf(self, dist, v):
        return lognorm.cdf(v, *self._get_params(dist))

    def ppf(self, dist, p):
        return lognorm.ppf(p, *self._get_params(dist))

    def mean(self, dist):
        return lognorm.mean(*self._get_params(dist))

    def std(self, dist):
        return lognorm.std(*self._get_params(dist))

    def var(self, dist):
        return lognorm.var(*self._get_params(dist))

    def high(self, dist):
        """ Return the variance of the distribution
        """
        return None

    def low(self, dist):
        """ Return the variance of the distribution
        """
        return None
