# Copyright (c) 2015 The University of Manchester
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
import numpy
from numpy.typing import NDArray
from .spike_source_array import SpikeSourceArray, Spikes
from spynnaker.pyNN.utilities import utility_calls

_inf: Final = float('inf')


class SpikeSourceFromFile(SpikeSourceArray):
    """
    A spike source that works from a file (typically a tab-separated table in
    a text file).
    """

    def __init__(
            self, spike_time_file: str,
            min_atom: float = 0.0, max_atom: float = _inf,
            min_time: float = 0.0, max_time: float = _inf,
            split_value: str = "\t"):
        # pylint: disable=too-many-arguments
        spike_times = utility_calls.read_spikes_from_file(
            spike_time_file, min_atom, max_atom, min_time, max_time,
            split_value)
        super().__init__(spike_times)

    @property
    def spike_times(self) -> NDArray[numpy.integer]:
        """
        The spike times read from the file.

        :rtype: ndarray
        """
        return self._spike_times
