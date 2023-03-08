# Copyright (c) 2017 The University of Manchester
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
