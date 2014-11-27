from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_rule_part import AbstractRulePart


@add_metaclass(ABCMeta)
class AbstractVoltageDependency(AbstractRulePart):

    def __init__(self):
        AbstractRulePart.__init__(self)
        pass

    @abstractmethod
    def is_voltage_dependency(self):
        """ helper method for is instance

        :return:
        """

    def is_rule_part(self):
        return True