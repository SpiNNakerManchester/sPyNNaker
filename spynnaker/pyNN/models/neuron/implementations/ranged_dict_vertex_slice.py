from spinn_utilities.helpful_functions import is_singleton
import numpy
import itertools


class RangedDictVertexSlice(object):
    """ A slice of a ranged dict to be used to update values
    """

    def __init__(self, ranged_dict, vertex_slice):
        self._ranged_dict = ranged_dict
        self._vertex_slice = vertex_slice

    def __getitem__(self, key):
        if not isinstance(key, "str"):
            raise KeyError("Key must be a string")
        return _RangedListVertexSlice(
            self._ranged_dict[key], self._vertex_slice)

    def __setitem__(self, key, value):
        ranged_list_vertex_slice = _RangedListVertexSlice(
            self._ranged_dict[key], self._vertex_slice)
        ranged_list_vertex_slice.__setitem__(value)


class _RangedListVertexSlice(object):
    """ A slice of ranged list to be used to update values
    """

    def __init__(self, ranged_list, vertex_slice):
        self._ranged_list = ranged_list
        self._vertex_slice = vertex_slice

    def __setitem__(self, value):

        if is_singleton(value):
            self._ranged_list.set_value_by_slice(
                self._vertex_slice.lo_atom, self._vertex_slice.hi_atom, value)
        else:

            # Find the ranges where the data is the same
            changes = numpy.nonzero(numpy.diff(value))[0] + 1

            # Go through and set the data in ranges
            start_index = 0
            for end_index in itertools.chain(
                    changes, [self._vertex_slice.n_atoms]):
                self._ranged_list.set_value_by_slice(
                    start_index, end_index, value[start_index])
                start_index = end_index
