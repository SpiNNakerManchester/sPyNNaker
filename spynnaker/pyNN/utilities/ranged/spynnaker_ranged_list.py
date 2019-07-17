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

from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.ranged_list import RangedList
from spinn_front_end_common.utilities import globals_variables


class SpynnakerRangedList(RangedList):

    @staticmethod
    @overrides(RangedList.is_list)
    def is_list(value, size):

        if globals_variables.get_simulator().is_a_pynn_random(value):
            return True

        return RangedList.is_list(value, size)

    @staticmethod
    @overrides(RangedList.as_list)
    def as_list(value, size, ids=None):

        if globals_variables.get_simulator().is_a_pynn_random(value):
            return value.next(n=size)

        return RangedList.as_list(value, size, ids)
