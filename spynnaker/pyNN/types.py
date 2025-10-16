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

from typing import Final, Iterable, Optional, Sequence, List, Union

import numpy
from numpy.typing import NDArray
from typing_extensions import TypeAlias, TypeGuard

import neo
from pyNN.random import RandomDistribution

#: The type of weights and delays provided by Synapse / SynapseInformation
# Combined types (where value could be either)
WeightsDelays: Final['TypeAlias'] = Optional[Union[
    float, str, RandomDistribution, NDArray[numpy.float64]]]
Weights: Final['TypeAlias'] = Optional[Union[
    float, str, RandomDistribution, NDArray[numpy.float64]]]
Delays: Final['TypeAlias'] = \
    Union[float, str, RandomDistribution, NDArray[numpy.float64]]
# These are the Types we know are coming in.
# Most things that can be considered floats (including int)  will work
WeightsDelysIn: Final['TypeAlias'] = Optional[Union[
    float, str, RandomDistribution, Iterable[float], NDArray[numpy.float64]]]

IoDest: TypeAlias = Union[
    str, neo.baseio.BaseIO, None]  # pylint: disable=no-member

ViewIndices = Union[None, Sequence[int], NDArray[numpy.integer]]
#: :meta private:
Selector: TypeAlias = Union[
    None, int, slice, Sequence[int], List[bool], NDArray[numpy.bool_],
    NDArray[numpy.integer]]

WeightScales: TypeAlias = Union[NDArray[numpy.floating], Sequence[float]]


def is_scalar(value: Weights) -> TypeGuard[Union[int, float]]:
    """
    Are the weights or delays a simple integer or float?

    :returns: True if the type of `value` is a scalar type.
    """
    return numpy.isscalar(value)
