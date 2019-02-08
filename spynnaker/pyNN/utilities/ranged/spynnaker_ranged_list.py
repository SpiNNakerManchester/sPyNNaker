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
