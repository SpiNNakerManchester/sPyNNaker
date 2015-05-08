"""
delta component
"""

from spynnaker.pyNN.models.components.synapse_shape_components.\
    abstract_synapse_shape_component import \
    AbstractSynapseShapeComponent
from spynnaker.pyNN.utilities import constants

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class DeltaComponent(AbstractSynapseShapeComponent):
    """
    delta component
    """

    def __init__(self):
        pass

    def get_synapse_shape_magic_number(self):
        """
        over ridden from AbstractSynapseShapeComponent
        :return:
        """
        return constants.SYNAPSE_SHAPING_DELTA_MAGIC_NUMBER

    @abstractmethod
    def is_delta_shaped(self):
        """
        helper method for isinstance
        :return:
        """