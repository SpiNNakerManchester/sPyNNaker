# Copyright (c) 2022 The University of Manchester
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

from enum import (auto, Enum)


class BufferDataType(Enum):
    """
    Different functions to retrieve the data.

    This class is designed to used internally by NeoBufferDatabase
    """
    NEURON_SPIKES = (auto())
    EIEIO_SPIKES = (auto())
    MULTI_SPIKES = (auto())
    MATRIX = (auto())
    REWIRES = (auto())
    NOT_NEO = (auto())

    def __str__(self):
        return self.name
