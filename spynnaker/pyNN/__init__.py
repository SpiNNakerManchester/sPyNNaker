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

from spynnaker._version import __version__  # NOQA
from spynnaker._version import __version_name__  # NOQA
from spynnaker._version import __version_month__  # NOQA
from spynnaker._version import __version_year__  # NOQA

# pynn imports
from pyNN.common import control as _pynn_control  # NOQA
from pyNN.recording import get_io  # NOQA
from pyNN.random import (NumpyRNG,
                         RandomDistribution as _PynnRandomDistribution)  # NOQA
from pyNN.space import \
    Space, Line, Grid2D, Grid3D, Cuboid, Sphere, RandomStructure  # NOQA
from pyNN.space import distance as _pynn_distance  # NOQA
import pyNN.common as pynn_common  # NOQA
