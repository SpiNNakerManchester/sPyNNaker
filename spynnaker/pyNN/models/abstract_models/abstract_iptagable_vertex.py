from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint

from spynnaker.pyNN.models.abstract_models.abstract_tagable_vertex import \
    AbstractTagableVertex

import socket


@add_metaclass(ABCMeta)
class AbstractIPTagableVertex(AbstractTagableVertex):

    def __init__(self, tag, port, address, board_address, strip_sdp=False):
        AbstractTagableVertex.__init__(self)
        self._address = address
        #convert board address into a ip address (may already be in this state)
        board_address = socket.gethostbyname(board_address)
        self.add_constraint(TagAllocatorRequireIptagConstraint(
            address=address, port=port, tag_id=tag, strip_sdp=strip_sdp,
            board_address=board_address))

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