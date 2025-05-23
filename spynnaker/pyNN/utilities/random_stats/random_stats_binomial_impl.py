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

from typing import List, Optional
from scipy.stats import binom
from pyNN.random import RandomDistribution
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities.random_stats import AbstractRandomStats


class RandomStatsBinomialImpl(AbstractRandomStats):
    """
    An implementation of AbstractRandomStats for binomial distributions.
    """

    def _get_params(self, dist: RandomDistribution) -> List[float]:
        return [dist.parameters['n'], dist.parameters['p']]

    @overrides(AbstractRandomStats.cdf)
    def cdf(self, dist: RandomDistribution, v: float) -> float:
        return binom.cdf(v, *self._get_params(dist))

    @overrides(AbstractRandomStats.ppf)
    def ppf(self, dist: RandomDistribution, p: float) -> float:
        return binom.ppf(p, *self._get_params(dist))

    @overrides(AbstractRandomStats.mean)
    def mean(self, dist: RandomDistribution) -> float:
        return binom.mean(*self._get_params(dist))

    @overrides(AbstractRandomStats.std)
    def std(self, dist: RandomDistribution) -> float:
        return binom.std(*self._get_params(dist))

    @overrides(AbstractRandomStats.var)
    def var(self, dist: RandomDistribution) -> float:
        return binom.var(*self._get_params(dist))

    @overrides(AbstractRandomStats.high)
    def high(self, distribution: RandomDistribution) -> Optional[float]:
        return None

    @overrides(AbstractRandomStats.low)
    def low(self, distribution: RandomDistribution) -> Optional[float]:
        return None
