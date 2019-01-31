import math


class RunningStats(object):
    """ Keeps running statistics
        From: http://www.johndcook.com/blog/skewness_kurtosis/
    """
    __slots__ = ["__mean", "__mean_2", "__n_items"]

    def __init__(self):
        self.__mean = 0.0
        self.__mean_2 = 0.0
        self.__n_items = 0

    def add_item(self, x):
        old_n_items = self.__n_items
        self.__n_items += 1

        delta = x - self.__mean
        delta_n = delta / self.__n_items
        term_1 = delta * delta_n * old_n_items

        self.__mean += delta_n
        self.__mean_2 += term_1

    def add_items(self, mean, variance, n_items):
        if n_items > 0:
            new_n_items = self.__n_items + n_items
            mean_2 = variance * (n_items - 1.0)

            delta = mean - self.__mean
            delta_2 = delta * delta
            new_mean = (((self.__n_items * self.__mean) + (n_items * mean)) /
                        new_n_items)
            new_mean_2 = (self.__mean_2 + mean_2 +
                          (delta_2 * self.__n_items * n_items) / new_n_items)

            self.__n_items = new_n_items
            self.__mean = new_mean
            self.__mean_2 = new_mean_2

    @property
    def n_items(self):
        return self.__n_items

    @property
    def mean(self):
        return self.__mean

    @property
    def variance(self):
        if self.__n_items <= 1:
            return 0.0
        return self.__mean_2 / (self.__n_items - 1.0)

    @property
    def standard_deviation(self):
        return math.sqrt(self.variance)
