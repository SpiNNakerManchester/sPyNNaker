from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod)


@add_metaclass(AbstractBase)
class AbstractSendsOutgoingSynapses(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_out_going_size(self):
        """ return how many atoms are to be considered in outgoing projections

        :return: 
        """
