from multiprocessing.pool import ThreadPool

from spinnman.connections.udp_packet_connections.eieio_command_connection import \
    EieioCommandConnection
from spinnman.connections.udp_packet_connections.stripped_iptag_connection \
    import StrippedIPTagConnection
from spinnman.connections.listeners.queuers.callback_worker import \
    CallbackWorker
from spinnman import constants


class SpynnakerVisualisationConnection(object):

    def packet_translater(self, packet):
        self._thread_pool.apply_async(CallbackWorker.call_callback,
                                      args=[self._receive_spinnaker_function,
                                            packet])

    def __init__(
            self, receive_handshake_function,
            receive_spinnaker_packet_function,
            hand_shake_local_port=19999, hand_shake_remote_port=19998,
            hand_shake_remote_host="localhost", no_threads=5,
            spinnaker_packets_local_port=None):

        self._receive_spinnaker_function = receive_spinnaker_packet_function

        # create connections and register listeners
        self._database_handshake_connection =\
            EieioCommandConnection(
                hand_shake_local_port, hand_shake_remote_host,
                hand_shake_remote_port)
        self._database_handshake_connection.\
            register_callback(receive_handshake_function)
        self._spinnaker_data_connection = \
            StrippedIPTagConnection(local_port=spinnaker_packets_local_port)
        self._spinnaker_data_connection.\
            register_callback(self.packet_translater,
                              constants.TRAFFIC_TYPE.EIEIO_DATA)
        self._thread_pool = ThreadPool(processes=no_threads)
