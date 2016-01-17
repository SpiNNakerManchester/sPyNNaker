from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractMappable(object):
    """ An item that, changes to which might cause a need for mapping to be\
        performed before and in between calls to the PyNN run function
    """

    @abstractproperty
    def requires_mapping(self):
        """ True if changes that have been made require that mapping be\
            performed.  Note that this should return True the first time it\
            is called, as the vertex must require mapping as it has been\
            created!
        """

    @abstractmethod
    def mark_no_changes(self):
        """ Marks the point after which changes are reported.  Immediately\
            after calling this method, requires_mapping should return False.
        """
