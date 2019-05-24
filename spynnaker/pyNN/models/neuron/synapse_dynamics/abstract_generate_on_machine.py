from enum import Enum
import numpy
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractproperty


class MatrixGeneratorID(Enum):
    STATIC_MATRIX = 0
    STDP_MATRIX = 1


@add_metaclass(AbstractBase)
class AbstractGenerateOnMachine(object):
    """ A synapse dynamics that can be generated on the machine
    """
    __slots__ = []

    def generate_on_machine(self):
        """ Determines if this instance should be generated on the machine.

        Default implementation returns True

        :rtype: bool
        """
        return True

    @abstractproperty
    def gen_matrix_id(self):
        """ The ID of the on-machine matrix generator

        :rtype: int
        """

    @property
    def gen_matrix_params(self):
        """ Any parameters required by the matrix generator

        :rtype: numpy array of uint32
        """
        return numpy.zeros(0, dtype="uint32")

    @property
    def gen_matrix_params_size_in_bytes(self):
        """ The size of the parameters of the matrix generator in bytes

        :rtype: int
        """
        return 0
