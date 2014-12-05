from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod, abstractproperty
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_rule_part import AbstractRulePart


@add_metaclass(ABCMeta)
class AbstractTimeDependency(AbstractRulePart):

    def __init__(self):
        AbstractRulePart.__init__(self)

    def is_rule_part(self):
        return True

    @abstractmethod
    def is_time_dependance_rule_part(self):
        """helper method for is instance

        :return:
        """

    @abstractmethod
    def write_plastic_params(self, spec, machine_time_step, weight_scales,
                             global_weight_scale):
        """ method that writes plastic params to a data spec generator

        :param spec:
        :param machine_time_step:
        :param weight_scales:
        :return:
        """

    @abstractmethod
    def create_synapse_row_io(
            self, synaptic_row_header_words, dendritic_delay_fraction):
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
