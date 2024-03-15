# Copyright (c) 2020 The University of Manchester
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
from typing import List, Sequence, Tuple, Union

import numpy
from numpy.typing import NDArray
from typing_extensions import TypeAlias

from spynnaker.pyNN.random_distribution import RandomDistribution

#: Type of names of parameters and state variables.
Names: TypeAlias = Union[str, List[str], Tuple[str, ...]]

#: Type of normal values of parameters and state variables.
Values: TypeAlias = Union[
    float, Sequence[float], NDArray[numpy.floating], RandomDistribution]

#: Type of spikes in spike sources.
Spikes: TypeAlias = Union[
    # Can be floating point values (will round)
    Values,
    # Can be integer values, or lists of such
    int, Sequence[int], Sequence[Sequence[int]], NDArray[numpy.integer]]
