

class SocketAddress(object):

    def __init__(self, notify_host_name, notify_port_no, listen_port):
        self._notify_host_name = notify_host_name
        self._notify_port_no = notify_port_no
        self._listen_port = listen_port

    @property
    def notify_host_name(self):
        return self._notify_host_name

    @property
    def notify_port_no(self):
        return self._notify_port_no

    @property
    def listen_port(self):
        return self._listen_port

    def __eq__(self, other):
        """
        over rides the standard equal
        :return:
        """
        if isinstance(other, SocketAddress):
            if self.__hash__() == other.__hash__():
                return True
            else:
                return False
        else:
            return False

    def __hash__(self):
        """
        over rides the standard hash
        :return:
        """
        return (hash(self._listen_port) + hash(self._notify_host_name) +
                hash(self._notify_port_no))

