from spinnman.connections.abstract_classes.udp_receivers.\
    abstract_udp_eieio_command_receiver import AbstractUDPEIEIOCommandReceiver
from spinnman.connections.abstract_classes.udp_senders.\
    abstract_udp_eieio_command_sender import AbstractUDPEIEIOCommandSender
from spinnman.connections.abstract_classes.abstract_udp_connection\
    import AbstractUDPConnection
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage


class DataBaseMessageConnection(AbstractUDPConnection,
                                AbstractUDPEIEIOCommandReceiver,
                                AbstractUDPEIEIOCommandSender):

    def __init__(self, listen_port, host_to_notify, port_to_notify):
        AbstractUDPConnection.__init__(
            self, local_port=listen_port, remote_host=host_to_notify,
            remote_port=port_to_notify)

    def is_udp_eieio_command_sender(self):
        return True

    def is_udp_eieio_command_receiver(self):
        return True

    def connection_type(self):
        return None

    def supports_sends_message(self, message):
        return isinstance(message, EIEIOCommandMessage)
