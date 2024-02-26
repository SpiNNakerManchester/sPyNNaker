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

from typing import Iterable, Optional, Union

import numpy
from numpy.typing import NDArray
from typing_extensions import TypeAlias, TypeGuard

from pyNN.random import RandomDistribution

#: The type of weights and delays provided by Synapse / SynapseInformation
# Combined types (where value could be either)
Weight_Delay_Types: TypeAlias = Optional[Union[
    int, float, str, RandomDistribution, NDArray[numpy.float64]]]
Weight_Types: TypeAlias = Optional[Union[
    int, float, str, RandomDistribution, NDArray[numpy.float64]]]
Delay_Types: TypeAlias = \
    Union[float, str, RandomDistribution, NDArray[numpy.float64]]
# These are the Types we know are coming in.
# Most things that can be considered floats (including int)  will work
Weight_Delay_In_Types: TypeAlias = Optional[Union[
    int, float, str, RandomDistribution, Iterable[int], Iterable[float]]]


def is_scalar(value: Weight_Delay_Types) -> TypeGuard[Union[int, float]]:
    """
    Are the weights or delays a simple integer or float?
    """
    return numpy.isscalar(value)
