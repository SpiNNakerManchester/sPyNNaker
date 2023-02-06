# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
