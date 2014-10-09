from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from spinnman.model.iptag.iptag import IPTag

@add_metaclass(ABCMeta)
class AbstractIPTagableVertex(object):

    def __init__(self, tag, port, address):
        self._tag = tag
        self._port = port
        self._address = address

    def set_tag(self, new_tag):
        self._tag = new_tag

    def get_ip_tag(self):
        return IPTag(tag=self._tag, port=self._port, address=self._hostname)

    @abstractmethod
    def is_ip_tagable_vertex(self):
        pass
