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

from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.populations import Population


class MockPopulation(object):

    def __init__(self, size, label):
        self._size = size
        self._label = label

    @property
    @overrides(Population.size)
    def size(self):
        return self._size

    @property
    @overrides(Population.label)
    def label(self):
        return self.label

    def __repr__(self):
        return "Population {}".format(self._label)
