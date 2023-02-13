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

from scipy.stats import truncnorm
from spynnaker.pyNN.utilities.random_stats import AbstractRandomStats


class RandomStatsNormalClippedImpl(AbstractRandomStats):
    """ An implementation of AbstractRandomStats for normal distributions that\
        are clipped to a boundary (redrawn)
    """

    def _get_params(self, dist):
        low = ((dist.parameters['low'] - dist.parameters['mu']) /
               dist.parameters['sigma'])
        high = ((dist.parameters['high'] - dist.parameters['mu']) /
                dist.parameters['sigma'])
        return [low, high,
                dist.parameters['mu'], dist.parameters['sigma']]

    def cdf(self, dist, v):
        return truncnorm.cdf(v, *self._get_params(dist))

    def ppf(self, dist, p):
        return truncnorm.ppf(p, *self._get_params(dist))

    def mean(self, dist):
        return truncnorm.mean(*self._get_params(dist))

    def std(self, dist):
        return truncnorm.std(*self._get_params(dist))

    def var(self, dist):
        return truncnorm.var(*self._get_params(dist))

    def high(self, dist):
        return dist.parameters['high']

    def low(self, dist):
        return dist.parameters['low']
