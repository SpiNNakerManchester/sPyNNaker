"""
AbstractSynapseShapeComponent
"""

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSynapseShapeComponent(object):
    """
    AbstractSynapseShapeComponent which supports the getting of the input magic
    number
    """

    def __init(self):
        pass

    @abstractmethod
    def get_synapse_shape_magic_number(self):
        """
        method for getting the magic number
        :return:
        """