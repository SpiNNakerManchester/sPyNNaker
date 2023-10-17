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

from pyNN.random import RandomDistribution
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.ranged_list import RangedList


class SpynnakerRangedList(RangedList):
    """
    Adds support for :py:class:`~spynnaker.pyNN.RandomDistribution` to
    :py:class:`~spinn_utilities.ranged.RangedList`.
    """

    @overrides(RangedList.listness_check)
    def listness_check(self, value):
        if isinstance(value, RandomDistribution):
            return True

        return super().listness_check(value)

    @staticmethod
    @overrides(RangedList.as_list)
    def as_list(value, size, ids=None):

        if isinstance(value, RandomDistribution):
            return value.next(n=size)

        return RangedList.as_list(value, size, ids)
