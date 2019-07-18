from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


@add_metaclass(AbstractBase)
class AbstractPartnerSelection(object):
    """ A partner selection rule
    """

    __slots__ = ()

    @abstractmethod
    def is_same_as(self, other):
        """ Determine if this partner selection is the same as another
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self):
        """ Get the amount of SDRAM used by the parameters of this rule
        """

    @abstractmethod
    def write_parameters(self, spec):
        """ Write the parameters of the rule to the spec
        """

    @abstractmethod
    def get_parameter_names(self):
        """ Return the names of the parameters supported by this rule

        :rtype: iterable(str)
        """
