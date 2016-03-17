from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractRandomStats(object):
    """ Statistics about PyNN RandomDistribution objects
    """

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
