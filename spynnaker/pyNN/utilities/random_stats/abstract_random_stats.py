# Copyright (c) 2015-2023 The University of Manchester
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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractRandomStats(object, metaclass=AbstractBase):
    """ Statistics about PyNN RandomDistribution objects
    """
    __slots__ = ()

    @abstractmethod
    def cdf(self, dist, v):
        """ Return the cumulative distribution function value for the value v
        """

    @abstractmethod
    def ppf(self, dist, p):
        """ Return the percent point function value for the probability p
        """

    @abstractmethod
    def mean(self, dist):
        """ Return the mean of the distribution
        """

    @abstractmethod
    def std(self, dist):
        """ Return the standard deviation of the distribution
        """

    @abstractmethod
    def var(self, dist):
        """ Return the variance of the distribution
        """

    @abstractmethod
    def high(self, dist):
        """ Return the high cutoff value of the distribution, or None if the\
            distribution is unbounded
        """

    @abstractmethod
    def low(self, dist):
        """ Return the low cutoff value of the distribution, or None if the\
            distribution is unbounded
        """
