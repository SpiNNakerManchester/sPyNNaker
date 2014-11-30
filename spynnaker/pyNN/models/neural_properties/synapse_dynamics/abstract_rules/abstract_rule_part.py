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

    @abstractmethod
    def write_plastic_params(self, spec, machine_time_step, weight_scale):
        """ method that writes plastic params to a data spec generator

        :param spec:
        :param machine_time_step:
        :param weight_scale:
        :return:
        """

    @abstractmethod
    def get_params_size_bytes(self):
        """

        :return:
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """

        :return:
        """
