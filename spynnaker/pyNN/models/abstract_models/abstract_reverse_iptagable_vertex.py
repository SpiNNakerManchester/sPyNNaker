from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
#from spinnman.model.reverse_iptag import ReverseIPTag

@add_metaclass(ABCMeta)
class AbstractReverseIPTagableVertex(object):

    def __init__(self, tag, port, address):
        self._tag = tag
        self._port = port
        self._address = address

    def get_reverse_ip_tag(self):
        #return ReverseIPTag(tag=self._tag, port=self._port,
        #                   address=self._hostname)
        return None

    @abstractmethod
    def is_reverse_ip_tagable_vertex(self):
        pass
