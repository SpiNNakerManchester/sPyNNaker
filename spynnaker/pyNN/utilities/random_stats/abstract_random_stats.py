from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractRandomStats(object):
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
