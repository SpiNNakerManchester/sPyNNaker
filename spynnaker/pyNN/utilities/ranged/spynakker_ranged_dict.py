from spinn_utilities.ranged.range_dictionary import RangeDictionary
from .spynakker_ranged_list import SpynakkerRangedList


class SpynakkerRangeDictionary(RangeDictionary):

    def list_factory(self, size=None, value=None, key=None):
        """
        Defines which class or subclass of RangedList to use

        Main purpose is for subclasses to use a subclass or RangedList
        All parameters are pass through ones to the List constructor

        :param size: Fixed length of the list
        :param value: value to given to all elements in the list
        :param key: The dict key this list covers.
        :return: AbstractList in this case a RangedList
        """
        return SpynakkerRangedList(size, value, key)
