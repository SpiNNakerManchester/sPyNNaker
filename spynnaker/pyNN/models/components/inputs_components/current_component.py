from spynnaker.pyNN.models.components.inputs_components.\
    abstract_input_type_component import AbstractInputTypeComponent

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
import hashlib

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
        return [hashlib.md5("0").hexdigest()[:8]]

    @abstractmethod
    def is_current_component(self):
        """
        helper emthod for isinstance
        :return:
        """