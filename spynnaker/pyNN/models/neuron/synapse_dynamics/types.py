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

from typing import Final
from numpy import dtype, float64, uint32, void
from numpy.typing import NDArray
from typing_extensions import TypeAlias

#: Type model of the basic configuration data of a connector
NUMPY_CONNECTORS_DTYPE: Final = dtype(
    [("source", uint32), ("target", uint32),
     ("weight", float64), ("delay", float64)])

#: Type of connections. The dtype is actually
#: :py:const:`NUMPY_CONNECTORS_DTYPE` but we cannot currently express that in
#: the overall array type due to Numpy typing limitations.
ConnectionsArray: TypeAlias = NDArray[void]
