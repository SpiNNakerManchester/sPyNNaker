from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractReadParametersBeforeSet(object):
    """ A vertex whose parameters must be read before any can be set
    """

    __slots__ = ()

    @abstractmethod
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):
        """ Read the parameters from the machine before any are changed

        :param transceiver: the SpinnMan interface
        :param placement: the placement of a vertex
        :param vertex_slice: the slice of atoms for this vertex
        """
