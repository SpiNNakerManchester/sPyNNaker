from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

from spynnaker.pyNN.models.abstract_models.abstract_tagable_vertex import \
    AbstractTagableVertex


@add_metaclass(ABCMeta)
class AbstractIPTagableVertex(AbstractTagableVertex):

    def __init__(self, tag, port, board_address, address, strip_sdp=False):
        AbstractTagableVertex.__init__(self, tag, port, board_address)
        self._address = address

    @property
    def address(self):
        return self._address

    @abstractmethod
    def is_ip_tagable_vertex(self):
        """ helper method for is instance

        :return:
        """

    def is_tagable_vertex(self):
        return True