from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_reverse_iptag_constraint import \
    TagAllocatorRequireReverseIptagConstraint

from spynnaker.pyNN.models.abstract_models.abstract_tagable_vertex import \
    AbstractTagableVertex

import socket
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractReverseIPTagableVertex(AbstractTagableVertex):

    def __init__(self, tag, port, board_address, port_num):
        AbstractTagableVertex.__init__(self)
        #convert board address into a ip address (may already be in this state)
        board_address = socket.gethostbyname(board_address)
        self.add_constraint(TagAllocatorRequireReverseIptagConstraint(
            tag_id=tag, board_address=board_address, port=port,
            port_num=port_num))

    @abstractmethod
    def is_reverse_ip_tagable_vertex(self):
        """ helper method for is_instance

        :return:
        """

    def is_tagable_vertex(self):
        return True

