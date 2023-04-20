# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from scipy.stats import vonmises
from spynnaker.pyNN.utilities.random_stats import AbstractRandomStats


class RandomStatsVonmisesImpl(AbstractRandomStats):
    """
    An implementation of AbstractRandomStats for von Mises distributions.
    """

    def _get_params(self, dist):
        return [dist.parameters['mu'], dist.parameters['kappa']]

    def cdf(self, dist, v):
        return vonmises.cdf(v, *self._get_params(dist))

    def ppf(self, dist, p):
        return vonmises.ppf(p, *self._get_params(dist))

    def mean(self, dist):
        return vonmises.mean(*self._get_params(dist))

    def std(self, dist):
        return vonmises.std(*self._get_params(dist))

    def var(self, dist):
        return vonmises.var(*self._get_params(dist))

    def high(self, distribution):
        return None

    def low(self, distribution):
        return None
