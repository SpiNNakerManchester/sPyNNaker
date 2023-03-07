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

import scipy.stats
from spynnaker.pyNN.utilities.random_stats import AbstractRandomStats


class RandomStatsScipyImpl(AbstractRandomStats):
    """ A Random Statistics object that uses scipy directly
    """

    def __init__(self, distribution_type):
        self._scipy_stats = getattr(scipy.stats, distribution_type)

    def cdf(self, dist, v):
        return self._scipy_stats.cdf(v, *dist.parameters)

    def ppf(self, dist, p):
        return self._scipy_stats.ppf(p, *dist.parameters)

    def mean(self, dist):
        return self._scipy_stats.mean(*dist.parameters)

    def std(self, dist):
        return self._scipy_stats.std(*dist.parameters)

    def var(self, dist):
        return self._scipy_stats.var(*dist.parameters)

    def high(self, dist):
        if "high" in dist.parameters:
            return dist.parameters['high']
        return None

    def low(self, dist):
        if "low" in dist.parameters:
            return dist.parameters['low']
        return None
