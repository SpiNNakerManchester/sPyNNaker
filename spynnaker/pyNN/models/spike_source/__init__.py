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

from .spike_source_array import SpikeSourceArray
from .spike_source_from_file import SpikeSourceFromFile
from .spike_source_poisson import SpikeSourcePoisson
from .rate_source_array import RateSourceArray
from .rate_source_live import RateSourceLive
from .rate_live_teacher import RateLiveTeacher
from .rate_source_multiple import RateSourceMultiple

__all__ = ["SpikeSourceArray", "SpikeSourceFromFile",
        "SpikeSourcePoisson", "RateSourceArray",
        "RateSourceLive", "RateLiveTeacher",
        "RateSourceMultiple"]
