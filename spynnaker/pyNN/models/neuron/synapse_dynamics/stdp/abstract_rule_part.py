from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod, abstractproperty
from spynnaker.pyNN.models.common_objects.\
    abstract_requires_component_magic_number import \
    AbstractRequiresComponentMagicNumber


@add_metaclass(ABCMeta)
class AbstractRulePart(AbstractRequiresComponentMagicNumber):

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