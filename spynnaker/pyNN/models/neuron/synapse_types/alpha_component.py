"""
alpha component
"""

from spynnaker.pyNN.models.components.synapse_shape_components.\
    abstract_synapse_shape_component import \
    AbstractSynapseShapeComponent
from spynnaker.pyNN.utilities import constants

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
import hashlib


@add_metaclass(ABCMeta)
class AlphaComponent(AbstractSynapseShapeComponent):
    """
    alpha component
    """

    def __init__(self):
        pass

    def get_synapse_shape_magic_number(self):
        """
        over ridden from AbstractSynapseShapeComponent
        :return:
        """
        return [hashlib.md5("synapse_types_alpha_impl").hexdigest()[:8]]

    @abstractmethod
    def is_alpha_shaped(self):
        """
        helper method for isinstance
        :return:
        """
