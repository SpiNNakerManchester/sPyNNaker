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
from pacman.model.graphs import AbstractSupportsSDRAMEdges
from pacman.model.graphs.machine import (
    SourceSegmentedSDRAMMachinePartition)
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


# pylint: disable=abstract-method
class SendsSynapticInputsOverSDRAM(
        AbstractSupportsSDRAMEdges, metaclass=AbstractBase):
    """
    An object that sends synaptic inputs over SDRAM.
    """

    @abstractmethod
    def set_sdram_partition(
            self,
            sdram_partition: SourceSegmentedSDRAMMachinePartition) -> None:
        """
        Set the SDRAM partition.  Must only be called once per instance.

        :param sdram_partition:
            The SDRAM partition to receive synapses from
        """
        raise NotImplementedError
