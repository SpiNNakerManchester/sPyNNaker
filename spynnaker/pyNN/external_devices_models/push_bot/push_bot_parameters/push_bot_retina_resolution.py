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

from enum import Enum
from spynnaker.pyNN.protocols import RetinaKey


class PushBotRetinaResolution(Enum):
    """ Resolutions supported by the pushbot retina device
    """

    NATIVE_128_X_128 = RetinaKey.NATIVE_128_X_128
    DOWNSAMPLE_64_X_64 = RetinaKey.DOWNSAMPLE_64_X_64
    DOWNSAMPLE_32_X_32 = RetinaKey.DOWNSAMPLE_32_X_32
    DOWNSAMPLE_16_X_16 = RetinaKey.DOWNSAMPLE_16_X_16
