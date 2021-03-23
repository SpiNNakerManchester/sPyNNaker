# Copyright (c) 2020-2021 The University of Manchester
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

from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay
from .spynnaker_splitter_partitioner import SpynnakerSplitterPartitioner
from .spynnaker_splitter_selector import SpynnakerSplitterSelector
from .splitter_abstract_pop_vertex_slice import (
    SplitterAbstractPopulationVertexSlice)
from .splitter_delay_vertex_slice import SplitterDelayVertexSlice
from .spynnaker_splitter_slice_legacy import SpynnakerSplitterSliceLegacy

__all__ = [
    'AbstractSpynnakerSplitterDelay', 'SplitterAbstractPopulationVertexSlice',
    'SplitterDelayVertexSlice',
    'SpynnakerSplitterPartitioner', 'SpynnakerSplitterSelector',
    'SpynnakerSplitterSliceLegacy']
