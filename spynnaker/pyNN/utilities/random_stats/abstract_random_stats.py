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
