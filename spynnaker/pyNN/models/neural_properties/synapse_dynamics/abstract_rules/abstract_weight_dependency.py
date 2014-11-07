from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_rule_part import AbstractRulePart


@add_metaclass(ABCMeta)
class AbstractWeightDependency(AbstractRulePart):

    #noinspection PyPep8Naming
    def __init__(self, w_min, w_max, A_plus, A_minus):
        AbstractRulePart.__init__(self)
        self._w_min = w_min
        self._w_max = w_max
        self._A_plus = A_plus
        self._A_minus = A_minus

    @property
    def w_min(self):
        return self._w_min

    @property
    def w_max(self):
        return self._w_max

    #noinspection PyPep8Naming
    @property
    def A_plus(self):
        return self.A_plus

    #noinspection PyPep8Naming
    @property
    def A_minus(self):
        return self._A_minus

    def is_rule_part(self):
        return True
    
    @abstractmethod
    def is_weight_dependance_rule_part(self):
        """helper method for is instance
        
        :return:
        """