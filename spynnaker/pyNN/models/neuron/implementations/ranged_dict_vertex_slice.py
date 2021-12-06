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

import itertools
import numpy
from spinn_utilities.helpful_functions import is_singleton


class RangedDictVertexSlice(object):
    """ A slice of a ranged dict to be used to update values
    """
    __slots__ = [
        "__ranged_dict", "__vertex_slice"]

    def __init__(self, ranged_dict, vertex_slice):
        """
        :param ~spinn_utilities.ranged.RangeDictionary ranged_dict:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        """
        self.__ranged_dict = ranged_dict
        self.__vertex_slice = vertex_slice

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise KeyError("Key must be a string")
        return _RangedListVertexSlice(
            self.__ranged_dict[key], self.__vertex_slice)

    def __setitem__(self, key, value):
        ranged_list_vertex_slice = _RangedListVertexSlice(
            self.__ranged_dict[key], self.__vertex_slice)
        ranged_list_vertex_slice.set_item(value)


class _RangedListVertexSlice(object):
    """ A slice of ranged list to be used to update values
    """
    __slots__ = [
        "__ranged_list", "__vertex_slice"]

    def __init__(self, ranged_list, vertex_slice):
        self.__ranged_list = ranged_list
        self.__vertex_slice = vertex_slice

    def set_item(self, value):
        if is_singleton(value):
            self.__ranged_list.set_value_by_slice(
                self.__vertex_slice.lo_atom, self.__vertex_slice.hi_atom,
                value)
        else:

            # Find the ranges where the data is the same
            changes = numpy.nonzero(numpy.diff(value))[0] + 1

            # Go through and set the data in ranges
            start_index = 0
            off = self.__vertex_slice.lo_atom
            for end_index in itertools.chain(
                    changes, [self.__vertex_slice.n_atoms]):
                self.__ranged_list.set_value_by_slice(
                    start_index + off, end_index + off, value[start_index])
                start_index = end_index
