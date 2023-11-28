# Copyright (c) 2016 The University of Manchester
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

import math
import struct
from pacman.model.resources import (
    AbstractSDRAM, ConstantSDRAM, VariableSDRAM)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)

_TWO_WORDS = struct.Struct("<II")


class MultiSpikeRecorder(object):
    __slots__ = ("__record", )

    def __init__(self) -> None:
        self.__record = False

    @property
    def record(self) -> bool:
        """
        :rtype: bool
        """
        return self.__record

    @record.setter
    def record(self, record: bool):
        self.__record = bool(record)

    def get_sdram_usage_in_bytes(
            self, n_neurons: int, spikes_per_timestep: float) -> AbstractSDRAM:
        """
        :param int n_neurons:
        :param float spikes_per_timestep:
        :rtype: ~pacman.model.resources.AbstractSDRAM
        """
        if not self.__record:
            return ConstantSDRAM(0)

        out_spike_bytes = (
            int(math.ceil(n_neurons / BITS_PER_WORD)) * BYTES_PER_WORD)
        return VariableSDRAM(0, (2 * BYTES_PER_WORD) + (
            out_spike_bytes * spikes_per_timestep))
