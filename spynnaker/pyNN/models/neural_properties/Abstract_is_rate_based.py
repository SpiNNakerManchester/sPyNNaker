from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractIsRateBased(object):

    __slots__ = ()

    @abstractmethod
    def get_rate_lut(self):
        """ Generate the lut for the output rate to be written as DataSpecification

        :rtype: list
        """