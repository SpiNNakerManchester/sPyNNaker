from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod, abstractproperty

@add_metaclass(ABCMeta)
class AbstractRulePart(object):

    def __init__(self):
        pass

    @abstractmethod
    def is_rule_part(self):
        """ helper for is instance

        :return:
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """

        :return:
        """
