# Copyright (c) 2023 The University of Manchester
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

"""
Types (and related) that are useful for implementing connectors.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Final, Iterable, Sequence

import neo
import numpy
from numpy.typing import NDArray
from pyNN.random import RandomDistribution
from typing_extensions import TypeAlias, TypeGuard

#: The type of weights and delays provided by Synapse / SynapseInformation
# Combined types (where value could be either)
WeightsDelays: Final['TypeAlias'] = (float | str | RandomDistribution |
                                     NDArray[numpy.float64] | None)
Weights: Final['TypeAlias'] = (float | str | RandomDistribution |
                               NDArray[numpy.float64] | None)
Delays: Final['TypeAlias'] = \
    float | str | RandomDistribution | NDArray[numpy.float64]
# These are the Types we know are coming in.
# Most things that can be considered floats (including int)  will work
WeightsDelysIn: Final['TypeAlias'] = (float | str | RandomDistribution |
                                      Iterable[float] |
                                      NDArray[numpy.float64] | None)

ViewIndices = None | Sequence[int] | NDArray[numpy.integer]
#: :meta private:
Selector: TypeAlias = (None | int | slice | Sequence[int] | list[bool] |
                       NDArray[numpy.bool_] | NDArray[numpy.integer])

WeightScales: TypeAlias = NDArray[numpy.floating] | Sequence[float]

if TYPE_CHECKING:
    IoDest: TypeAlias = (  # pylint: disable=no-member
            str | neo.baseio.BaseIO | None)


def is_scalar(value: Weights) -> TypeGuard[int | float]:
    """
    Are the weights or delays a simple integer or float?

    :returns: True if the type of `value` is a scalar type.
    """
    return numpy.isscalar(value)
