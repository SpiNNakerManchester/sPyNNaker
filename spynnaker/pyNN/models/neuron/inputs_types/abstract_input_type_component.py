"""
"""

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractInputTypeComponent(object):
    """ Represents something that provides parameters for the input into a \
        neural model
    """

    def __init(self):
        pass

    @abstractmethod
    def get_n_input_parameters(self):
        """ Get the number of parameters that are used by this input type
        """

    @abstractmethod
    def get_input_component_source_name(self):
        """ Get the name of the input component source code
        """

    @abstractmethod
    def get_input_weight_scale(self):
        """ A number to multiply the weights by to keep values large enough\
            to be handled accurately enough in the input buffers.  This should\
            be reversed at the other side.
        """
