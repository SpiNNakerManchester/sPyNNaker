from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod, abstractproperty
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_rule_part import AbstractRulePart


@add_metaclass(ABCMeta)
class AbstractTimeDependency(AbstractRulePart):
    
    def __init__(self, tau_plus, tau_minus):
        AbstractRulePart.__init__(self)
        self._tau_plus = tau_plus
        self._tau_minus = tau_minus

    def is_rule_part(self):
        return True

    @property
    def tau_plus(self):
        return self._tau_plus

    @property
    def tau_minus(self):
        return self._tau_minus
    
    @abstractmethod
    def is_time_dependance_rule_part(self):
        """helper method for is instance

        :return:
        """

    @abstractmethod
    def create_synapse_row_io(self, synaptic_row_header_words, dendritic_delay_fraction):
        """

        :return:
        """
    
    @abstractmethod
    def get_params_size_bytes(self):
        """

        :return:
        """
        
    @abstractproperty
    def num_terms(self):
        """

        :return:
        """
        
    @abstractproperty
    def pre_trace_size_bytes(self):
        """

        :return:
        """