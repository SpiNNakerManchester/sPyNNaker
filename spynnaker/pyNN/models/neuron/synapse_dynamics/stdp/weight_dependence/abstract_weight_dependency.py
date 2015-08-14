from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.abstract_rules.\
    abstract_rule_part import AbstractRulePart


@add_metaclass(ABCMeta)
class AbstractWeightDependency(AbstractRulePart):

    # noinspection PyPep8Naming
    def __init__(self, w_min, w_max, A_plus, A_minus, A3_plus=None,
                 A3_minus=None):
        AbstractRulePart.__init__(self)
        self._w_min = w_min
        self._w_max = w_max
        self._A_plus = A_plus
        self._A_minus = A_minus
        self._A3_plus = A3_plus
        self._A3_minus = A3_minus

    @property
    def w_min(self):
        return self._w_min

    @property
    def w_max(self):
        return self._w_max

    # noinspection PyPep8Naming
    @property
    def A_plus(self):
        return self._A_plus

    # noinspection PyPep8Naming
    @property
    def A_minus(self):
        return self._A_minus

    # noinspection PyPep8Naming
    @property
    def A3_plus(self):
        return self._A3_plus

    # noinspection PyPep8Naming
    @property
    def A3_minus(self):
        return self._A3_minus

    def is_rule_part(self):
        return True

    @abstractmethod
    def is_weight_dependance_rule_part(self):
        """helper method for is instance

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

    @abstractmethod
    def get_params_size_bytes(self, num_synapse_types, num_terms):
        """

        :return:
        """
