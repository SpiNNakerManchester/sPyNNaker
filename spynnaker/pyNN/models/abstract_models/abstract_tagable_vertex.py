from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractTagableVertex(object):

    def __init__(self):
        pass

    @abstractmethod
    def is_tagable_vertex(self):
        """ helper method for is_instances

        :return:
        """