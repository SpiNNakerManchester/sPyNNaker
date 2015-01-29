from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from spinnman.model.iptag.iptag import IPTag

@add_metaclass(ABCMeta)
class AbstractReverseIPTagableVertex(object):

    def __init__(self, tag, port):
        self._tag = tag
        self._port = port

    def get_reverse_ip_tag(self):
        return IPTag(
            tag=self._tag, port=self._port, address="")

    def set_reverse_iptag_tag(self, new_tag):
        self._tag = new_tag

    @abstractmethod
    def is_reverse_ip_tagable_vertex(self):
        pass
