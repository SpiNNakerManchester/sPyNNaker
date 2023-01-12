# Copyright (c) 2022 The University of Manchester
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

from enum import (auto, Enum)


class BufferDataType(Enum):
    """
    Different functions to retrieve the data.

    This class is designed to used internally by NeoBufferDatabase
    """
    Neuron_spikes = (auto())
    EIEIO_spikes = (auto())
    Multi_spike = (auto())
    Matrix = (auto())
    Rewires = (auto())

    def __str__(self):
        return self.name
