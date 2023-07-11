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
from typing import Sequence
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from pacman.model.graphs import AbstractSupportsSDRAMEdges
from spinn_front_end_common.utilities.constants import BYTES_PER_SHORT


class ReceivesSynapticInputsOverSDRAM(
        AbstractSupportsSDRAMEdges, metaclass=AbstractBase):
    """
    An object that receives synaptic inputs over SDRAM.

    The number of neurons to be sent per synapse type is rounded up to be
    a power of 2.  A sender must send N_BYTES_PER_INPUT of data for each
    synapse type for each neuron, formatted as all the data for each neuron
    for the first synapse type, followed by all the data for each neuron
    for the second, and so on for each synapse type.  Each input is an
    accumulated weight value for the timestep, scaled with the given weight
    scales.
    """

    # The size of each input in bytes
    N_BYTES_PER_INPUT = BYTES_PER_SHORT

    @property
    @abstractmethod
    def weight_scales(self) -> Sequence[int]:
        """
        A list of scale factors to be applied to weights that get passed
        over SDRAM, one for each synapse type.

        :rtype: list(int)
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def n_bytes_for_transfer(self) -> int:
        """
        The number of bytes to be sent over the channel.  This will be
        calculated using the above numbers, but also rounded up to a number
        of words, and with the number of neurons rounded up to a power of 2.

        :rtype: int
        """
        raise NotImplementedError
