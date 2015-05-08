from spynnaker.pyNN.models.components.inputs_components.\
    abstract_input_type_component import AbstractInputTypeComponent
from spynnaker.pyNN.utilities import constants

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class CurrentComponent(AbstractInputTypeComponent):
    """
    AbstractCurrentComponent
    """

    def __init__(self):
        pass

    def get_input_magic_number(self):
        """
        over ridden from AbstractInputTypeComponent
        :return:
        """
        return constants.INPUT_CURRENT_COMPONENT_MAGIC_NUMBER

    @abstractmethod
    def is_current_component(self):
        """
        helper emthod for isinstance
        :return:
        """