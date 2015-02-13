from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractTagableVertex(object):

    def __init__(self, tag, port, board_address):
        self._tag = tag
        self._port = port
        self._board_address = board_address

    @property
    def tag(self):
        return self._tag

    @property
    def port(self):
        return self._port

    @property
    def board_address(self):
        return self._board_address

    @board_address.setter
    def board_address(self, board_address):
        self._board_address = board_address

    @tag.setter
    def tag(self, tag):
        self._tag = tag

    @abstractmethod
    def is_tagable_vertex(self):
        """ helper method for is_instances

        :return:
        """