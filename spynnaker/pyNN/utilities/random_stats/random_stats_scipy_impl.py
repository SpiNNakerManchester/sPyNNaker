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

from typing import Optional
import scipy.stats
from spinn_utilities.overrides import overrides
from pyNN.random import RandomDistribution
from spynnaker.pyNN.utilities.random_stats import AbstractRandomStats


class RandomStatsScipyImpl(AbstractRandomStats):
    """
    A Random Statistics object that uses scipy directly.
    """

    def __init__(self, distribution_type: str):
        """
        :param distribution_type: Name of the distribution type.
        """
        self._scipy_stats = getattr(scipy.stats, distribution_type)

    @overrides(AbstractRandomStats.cdf)
    def cdf(self, dist: RandomDistribution, v: float) -> float:
        return self._scipy_stats.cdf(v, *dist.parameters)

    @overrides(AbstractRandomStats.ppf)
    def ppf(self, dist: RandomDistribution, p: float) -> float:
        return self._scipy_stats.ppf(p, *dist.parameters)

    @overrides(AbstractRandomStats.mean)
    def mean(self, dist: RandomDistribution) -> float:
        return self._scipy_stats.mean(*dist.parameters)

    @overrides(AbstractRandomStats.std)
    def std(self, dist: RandomDistribution) -> float:
        return self._scipy_stats.std(*dist.parameters)

    @overrides(AbstractRandomStats.var)
    def var(self, dist: RandomDistribution) -> float:
        return self._scipy_stats.var(*dist.parameters)

    @overrides(AbstractRandomStats.high)
    def high(self, distribution: RandomDistribution) -> Optional[float]:
        if "high" in distribution.parameters:
            return distribution.parameters['high']
        return None

    @overrides(AbstractRandomStats.low)
    def low(self, distribution: RandomDistribution) -> Optional[float]:
        if "low" in distribution.parameters:
            return distribution.parameters['low']
        return None
