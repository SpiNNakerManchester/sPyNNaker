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

from spinn_utilities.abstract_base import abstractmethod
from spinn_utilities.overrides import overrides
from pacman.model.graphs import AbstractSupportsSDRAMEdges
from pacman.model.graphs.machine import SDRAMMachineEdge


class SendsSynapticInputsOverSDRAM(AbstractSupportsSDRAMEdges):
    """
    A marker interface for an object that sends synaptic inputs over SDRAM.
    """

    @abstractmethod
    @overrides(AbstractSupportsSDRAMEdges.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge: SDRAMMachineEdge) -> int:
        raise NotImplementedError
