# Copyright (c) 2025 The University of Manchester
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

from spinn_utilities.abstract_base import abstractmethod
from pacman.model.graphs.application import ApplicationVertex


class ColouredApplicationVertex(ApplicationVertex):
    """
    Indicates an application vertex that implements n_colour_bits.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def n_colour_bits(self) -> int:
        """
        The number of colour bits sent by this vertex.

        Assumed 0 unless overridden
        """
        raise NotImplementedError
