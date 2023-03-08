# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import select
import socket
from spinn_utilities.log import FormatAdapter
from spinn_utilities.ping import Ping
from spinnman.connections.abstract_classes import Listenable, Connection
from spinnman.utilities.socket_utils import (
    get_tcp_socket, connect_socket, get_socket_address, resolve_host,
    receive_message, send_message)
from spinn_front_end_common.utilities.constants import BYTES_PER_KB

logger = FormatAdapter(logging.getLogger(__name__))
# A set of connections that have already been made
_existing_connections = dict()


def get_pushbot_wifi_connection(remote_host, remote_port=56000):
    """ Get an existing connection to a PushBot, or make a new one.

    :param str remote_host: The IP address of the PushBot
    :param int remote_port: The port number of the PushBot (default 56000)
    """
    key = (remote_host, remote_port)
    if key not in _existing_connections:
        _existing_connections[key] = \
            PushBotWIFIConnection(remote_host, remote_port)
    return _existing_connections[key]


class PushBotWIFIConnection(Connection, Listenable):
    """ A connection to a PushBot via Wi-Fi.
    """
    __slots__ = [
        "__local_ip_address",
        "__local_port",
        "__remote_ip_address",
        "__remote_port",
        "__socket"]

    RECV_SIZE = 1 * BYTES_PER_KB

    def __init__(self, remote_host, remote_port=56000):
        """
        :param str remote_host: The IP address of the PushBot
        :param int remote_port: The port number of the PushBot (default 56000)
        :raise SpinnmanIOException:
            If there is an error setting up the communication channel
        """
        # Create a TCP Socket
        self.__socket = get_tcp_socket()

        # Get the port to connect to
        self.__remote_port = int(remote_port)

        # Get the host to connect to
        self.__remote_ip_address = resolve_host(remote_host)

        logger.info("Trying to connect to the PushBot via Wi-Fi")
        # Connect the socket
        connect_socket(
            self.__socket, self.__remote_ip_address, self.__remote_port)
        logger.info("Succeeded in connecting to PushBot via Wi-Fi")

        # Get the details of where the socket is connected
        self.__local_ip_address, self.__local_port = get_socket_address(
            self.__socket)

    def is_connected(self):
        """ See\
            :py:meth:`~spinnman.connections.Connection.is_connected`
        """
        # check if machine is active and on the network
        for _ in range(5):  # Try up to five times...
            # ping the remote address
            if Ping.ping(self.__remote_ip_address) == 0:
                # ping worked
                return True

        # If the ping fails this number of times, the host cannot be contacted
        return False

    @property
    def local_ip_address(self):
        """ The local IP address to which the connection is bound, \
            as a dotted string, e.g. `0.0.0.0`

        :rtype: str
        """
        return self.__local_ip_address

    @property
    def local_port(self):
        """ The local port to which the connection is bound.

        :rtype: int
        """
        return self.__local_port

    @property
    def remote_ip_address(self):
        """ The remote IP address to which the connection is connected, \
            as a dotted string, or None if not connected remotely

        :rtype: str or None
        """
        return self.__remote_ip_address

    @property
    def remote_port(self):
        """ The remote port to which the connection is connected, \
            or None if not connected remotely

        :rtype: int or None
        """
        return self.__remote_port

    def receive(self, timeout=None):
        """ Receive data from the connection

        :param timeout: The timeout, or None to wait forever
        :type timeout: float or None
        :return: The data received
        :rtype: bytes
        :raise SpinnmanTimeoutException:
            If a timeout occurs before any data is received
        :raise SpinnmanIOException: If an error occurs receiving the data
        """
        return receive_message(self.__socket, timeout, self.RECV_SIZE)

    def send(self, data):
        """ Send data down this connection

        :param bytearray data: The data to be sent
        :raise SpinnmanIOException: If there is an error sending the data
        """
        send_message(self.__socket, data)

    def close(self):
        """ See\
            :py:meth:`spinnman.connections.Connection.close`
        """
        try:
            self.__socket.shutdown(socket.SHUT_WR)
        except Exception:  # pylint: disable=broad-except
            pass
        self.__socket.close()

    def is_ready_to_receive(self, timeout=0):
        return bool(select.select([self.__socket], [], [], timeout)[0])

    def get_receive_method(self):
        return self.receive
