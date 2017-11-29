from spinn_utilities.ranged.ranged_list import RangedList
from spinn_front_end_common.utilities import globals_variables


class SpynakkerRangedList(RangedList):

    @staticmethod
    def is_list(value, size):
        """ Determines if the value is a list of a given size.
            An exception is raised if value *is* a list but is shorter\
            than size
        """

        if globals_variables.get_simulator().is_a_pynn_random(value):
            return True

        return RangedList.is_list(value, size)

    @staticmethod
    def as_list(value, size):
        """
        Converts if required the value into a list

        Assumes that is_list has been called and returned True
        So does not repeat the checks there unless required

        :param value:
        :return:
        """

        if globals_variables.get_simulator().is_a_pynn_random(value):
            return value.next(n=size)

        return RangedList.as_list(value, size)
