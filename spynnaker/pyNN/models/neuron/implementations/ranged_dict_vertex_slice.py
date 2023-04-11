# Copyright (c) 2017 The University of Manchester
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

import itertools
import numpy
from spinn_utilities.helpful_functions import is_singleton


class RangedDictVertexSlice(object):
    """
    A slice of a ranged dict to be used to update values.
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
    """
    A slice of ranged list to be used to update values.
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
