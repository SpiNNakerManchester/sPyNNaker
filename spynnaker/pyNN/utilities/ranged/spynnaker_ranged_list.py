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

from typing import Callable, List, Optional, Sequence, Union
from typing_extensions import TypeAlias
from pyNN.random import RandomDistribution
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.ranged_list import RangedList
from spinn_utilities.ranged.abstract_list import IdsType, T

# The type of things we consider to be a list of values
_ListType: TypeAlias = Union[Callable[[int], T], Sequence[T],
                             RandomDistribution]
# The type of value arguments in several places
_ValueType: TypeAlias = Optional[Union[T, _ListType]]


class SpynnakerRangedList(RangedList):
    """
    Adds support for :py:class:`~spynnaker.pyNN.RandomDistribution` to
    :py:class:`~spinn_utilities.ranged.RangedList`.
    """

    @overrides(RangedList.listness_check)
    def listness_check(self, value: _ValueType) -> bool:
        if isinstance(value, RandomDistribution):
            return True

        return super().listness_check(value)

    @overrides(RangedList.as_list)
    def as_list(
            self, value: _ListType, size: int,
            ids: Optional[IdsType] = None) -> List[T]:
        if isinstance(value, RandomDistribution):
            return value.next(n=size)

        return super().as_list(value, size, ids)
