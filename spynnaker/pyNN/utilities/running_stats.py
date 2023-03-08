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

import math


class RunningStats(object):
    """ Keeps running statistics.
        From: http://www.johndcook.com/blog/skewness_kurtosis/
    """
    __slots__ = ["__mean", "__mean_2", "__n_items"]

    def __init__(self):
        self.__mean = 0.0
        self.__mean_2 = 0.0
        self.__n_items = 0

    def add_item(self, x):
        """ Adds an item to the running statistics.

        :param x: The item to add
        :type x: int or float
        """
        old_n_items = self.__n_items
        self.__n_items += 1

        delta = x - self.__mean
        delta_n = delta / self.__n_items
        term_1 = delta * delta_n * old_n_items

        self.__mean += delta_n
        self.__mean_2 += term_1

    def add_items(self, mean, variance, n_items):
        """ Add a bunch of items (via their statistics).

        :param float mean: The mean of the items to add.
        :param float variance: The variance of the items to add.
        :param int n_items: The number of items represented.
        """
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
        """ The number of items seen.

        :rtype: int
        """
        return self.__n_items

    @property
    def mean(self):
        """ The mean of the items seen.

        :rtype: float
        """
        return self.__mean

    @property
    def variance(self):
        """ The variance of the items seen.

        :rtype: float
        """
        if self.__n_items <= 1:
            return 0.0
        return self.__mean_2 / (self.__n_items - 1.0)

    @property
    def standard_deviation(self):
        """ The population standard deviation of the items seen.

        :rtype: float
        """
        return math.sqrt(self.variance)
