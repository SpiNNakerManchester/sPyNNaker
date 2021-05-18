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

import numpy


class MockPopulation(object):

    def __init__(self, size, label):
        self._size = size
        self._label = label

    @property
    def size(self):
        return self._size

    @property
    def label(self):
        return self.label

    def __repr__(self):
        return "Population {}".format(self._label)


class MockSynapseInfo(object):

    def __init__(self, pre_population, post_population, weights, delays):
        self._pre_population = pre_population
        self._post_population = post_population
        self._weights = weights
        self._delays = delays

    @property
    def pre_population(self):
        return self._pre_population

    @property
    def post_population(self):
        return self._post_population

    @property
    def n_pre_neurons(self):
        return self._pre_population.size

    @property
    def n_post_neurons(self):
        return self._post_population.size

    @property
    def weights(self):
        return self._weights

    @property
    def delays(self):
        return self._delays


class MockRNG(object):

    def __init__(self):
        self._rng = numpy.random.RandomState()

    def next(self, n):
        return self._rng.uniform(size=n)

    def __getattr__(self, name):
        return getattr(self._rng, name)
