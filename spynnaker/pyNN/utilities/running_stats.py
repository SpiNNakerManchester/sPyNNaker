import math


class RunningStats(object):
    """ Keeps running statistics
        From: http://www.johndcook.com/blog/skewness_kurtosis/
    """

    def __init__(self):
        self._mean = 0.0
        self._mean_2 = 0.0
        self._n_items = 0

    def add_item(self, x):
        old_n_items = self._n_items
        self._n_items += 1

        delta = x - self._mean
        delta_n = delta / self._n_items
        term_1 = delta * delta_n * old_n_items

        self._mean += delta_n
        self._mean_2 += term_1

    def add_items(self, mean, variance, n_items):
        if n_items > 0:
            new_n_items = self._n_items + n_items
            mean_2 = variance * (n_items - 1.0)

            delta = mean - self._mean
            delta_2 = delta * delta
            new_mean = (((self._n_items * self._mean) + (n_items * mean)) /
                        new_n_items)
            new_mean_2 = (self._mean_2 + mean_2 +
                          (delta_2 * self._n_items * n_items) / new_n_items)

            self._n_items = new_n_items
            self._mean = new_mean
            self._mean_2 = new_mean_2

    @property
    def n_items(self):
        return self._n_items

    @property
    def mean(self):
        return self._mean

    @property
    def variance(self):
        if self._n_items <= 1:
            return 0.0
        return self._mean_2 / (self._n_items - 1.0)

    @property
    def standard_deviation(self):
        return math.sqrt(self.variance)
