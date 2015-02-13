from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

from spynnaker.pyNN.models.abstract_models.abstract_tagable_vertex import \
    AbstractTagableVertex


@add_metaclass(ABCMeta)
class AbstractReverseIPTagableVertex(AbstractTagableVertex):

    def __init__(self, tag, port, board_address):
        AbstractTagableVertex.__init__(self, tag, port, board_address)

    @abstractmethod
    def is_reverse_ip_tagable_vertex(self):
        """ helper method for is_instance

        :return:
        """

    def is_tagable_vertex(self):
        return True

