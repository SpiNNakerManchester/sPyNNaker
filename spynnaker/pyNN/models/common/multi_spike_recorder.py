# Copyright (c) 2016 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import logging
import struct
from pacman.model.resources.constant_sdram import ConstantSDRAM
from spinn_utilities.log import FormatAdapter
from pacman.model.resources.variable_sdram import VariableSDRAM
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BITS_PER_WORD)

logger = FormatAdapter(logging.getLogger(__name__))
_TWO_WORDS = struct.Struct("<II")


class MultiSpikeRecorder(object):
    __slots__ = [
        "__record"]

    def __init__(self):
        self.__record = False

    @property
    def record(self):
        """
        :rtype: bool
        """
        return self.__record

    @record.setter
    def record(self, record):
        self.__record = record

    def get_sdram_usage_in_bytes(self, n_neurons, spikes_per_timestep):
        """
        :rtype: ~pacman.model.resources.AbstractSDRAM
        """
        if not self.__record:
            return ConstantSDRAM(0)

        out_spike_bytes = (
            int(math.ceil(n_neurons / BITS_PER_WORD)) * BYTES_PER_WORD)
        return VariableSDRAM(0, (2 * BYTES_PER_WORD) + (
            out_spike_bytes * spikes_per_timestep))
