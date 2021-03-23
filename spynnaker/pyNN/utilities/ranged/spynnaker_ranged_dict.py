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

from spinn_utilities.ranged.range_dictionary import RangeDictionary
from .spynnaker_ranged_list import SpynnakerRangedList


class SpynnakerRangeDictionary(RangeDictionary):

    def list_factory(self, size, value, key):
        """ Defines which class or subclass of RangedList to use

        Main purpose is for subclasses to use a subclass or RangedList
        All parameters are pass through ones to the List constructor

        :param int size: Fixed length of the list
        :param value: value to given to all elements in the list
        :param key: The dict key this list covers.
        :return: AbstractList in this case a RangedList
        :rtype: SpynnakerRangedList
        """
        return SpynnakerRangedList(size, value, key)
