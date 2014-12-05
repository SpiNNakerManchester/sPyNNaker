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

    @abstractmethod
    def write_plastic_params(self, spec, machine_time_step, weight_scales,
                             global_weight_scale, num_terms):
        """ method that writes plastic params to a data spec generator

        :param spec:
        :param machine_time_step:
        :param weight_scales:
        :return:
        """

    def is_rule_part(self):
        return True
