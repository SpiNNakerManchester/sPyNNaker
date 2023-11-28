# Copyright (c) 2015 The University of Manchester
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
from pyNN.random import RandomDistribution
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractRandomStats(object, metaclass=AbstractBase):
    """
    Statistics about PyNN `~spynnaker.pyNN.RandomDistribution` objects.
    """
    __slots__ = ()

    @abstractmethod
    def cdf(self, dist: RandomDistribution, v: float) -> float:
        """
        Return the cumulative distribution function value for the value `v`.
        """
        raise NotImplementedError

    @abstractmethod
    def ppf(self, dist: RandomDistribution, p: float) -> float:
        """
        Return the percent point function value for the probability `p`.
        """
        raise NotImplementedError

    @abstractmethod
    def mean(self, dist: RandomDistribution) -> float:
        """
        Return the mean of the distribution.
        """
        raise NotImplementedError

    @abstractmethod
    def std(self, dist: RandomDistribution) -> float:
        """
        Return the standard deviation of the distribution.
        """
        raise NotImplementedError

    @abstractmethod
    def var(self, dist: RandomDistribution) -> float:
        """
        Return the variance of the distribution.
        """
        raise NotImplementedError

    @abstractmethod
    def high(self, distribution: RandomDistribution) -> Optional[float]:
        """
        Return the high cut-off value of the distribution, or `None` if the
        distribution is unbounded.
        """
        raise NotImplementedError

    @abstractmethod
    def low(self, distribution: RandomDistribution) -> Optional[float]:
        """
        Return the low cut-off value of the distribution, or `None` if the
        distribution is unbounded.
        """
        raise NotImplementedError
