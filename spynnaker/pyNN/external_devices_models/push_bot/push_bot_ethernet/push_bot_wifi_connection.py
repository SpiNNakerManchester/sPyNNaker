from spinnman.connections.abstract_classes import Listenable
from spinnman.connections.abstract_classes import Connection
from spinnman.exceptions import SpinnmanIOException
from spinnman.exceptions import SpinnmanTimeoutException

import platform
import subprocess
import socket
import select
import logging

logger = logging.getLogger(__name__)

# A set of connections that have already been made
_existing_connections = dict()


def get_pushbot_wifi_connection(remote_host, remote_port=56000):
    """ Get an existing connection to a PushBot, or make a new one

    :param remote_host: The IP address of the PushBot
    :type remote_host: str
    :param remote_port: The port number of the PushBot (default 56000)
    :type remote_port: int
    """
    if (remote_host, remote_port) not in _existing_connections:
        _existing_connections[(remote_host, remote_port)] = \
            PushBotWIFIConnection(remote_host, remote_port)
    return _existing_connections[(remote_host, remote_port)]


class PushBotWIFIConnection(Connection, Listenable):
    """ A connection to a pushbot via WiFi
    """

    def __init__(self, remote_host, remote_port=56000):
        """

        :param remote_host: The IP address of the PushBot
        :type remote_host: str
        :param remote_port: The port number of the PushBot (default 56000)
        :type remote_port: int
        :raise spinnman.exceptions.SpinnmanIOException: If there is an error\
                    setting up the communication channel
        """

        self._socket = None
        try:

            # Create a TCP Socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        except Exception as exception:
            raise SpinnmanIOException(
                "Error setting up socket: {}".format(exception))

        # Get the port to connect to
        self._remote_port = int(remote_port)

        # Get the host to connect to
        self._remote_ip_address = socket.gethostbyname(remote_host)

        try:
            logger.info("Trying to connect to the push bot via WIFI")
            # Connect the socket
            self._socket.connect((self._remote_ip_address, self._remote_port))
            logger.info("Succeeded in connecting to push bot via WIFI")

        except Exception as exception:
            raise SpinnmanIOException(
                "Error binding socket to {}:{}: {}".format(
                    self._remote_ip_address, self._remote_port, exception))

        # Get the details of where the socket is connected
        self._local_ip_address = None
        self._local_port = None
        try:
            self._local_ip_address, self._local_port =\
                self._socket.getsockname()

            # Ensure that a standard address is used for the INADDR_ANY
            # hostname
            if self._local_ip_address is None or self._local_ip_address == "":
                self._local_ip_address = "0.0.0.0"
        except Exception as exception:
            raise SpinnmanIOException("Error querying socket: {}".format(
                exception))

        # Set a general timeout on the socket
        self._socket.settimeout(0)

    def is_connected(self):
        """ See\
            :py:meth:`spinnman.connections.Connection.is_connected`
        """

        # check if machine is active and on the network
        ping_timeout = 5
        while ping_timeout > 0:

            # Start a ping process
            process = None
            if platform.platform().lower().startswith("windows"):
                process = subprocess.Popen(
                    "ping -n 1 -w 1 " + self._remote_ip_address,
                    shell=True, stdout=subprocess.PIPE)
            else:
                process = subprocess.Popen(
                    "ping -c 1 -W 1 " + self._remote_ip_address,
                    shell=True, stdout=subprocess.PIPE)
            process.wait()

            if process.returncode == 0:

                # ping worked
                return True
            else:
                ping_timeout -= 1

        # If the ping fails this number of times, the host cannot be contacted
        return False

    @property
    def local_ip_address(self):
        """ The local IP address to which the connection is bound.

        :return: The local ip address as a dotted string e.g. 0.0.0.0
        :rtype: str
        :raise None: No known exceptions are thrown
        """
        return self._local_ip_address

    @property
    def local_port(self):
        """ The local port to which the connection is bound.

        :return: The local port number
        :rtype: int
        :raise None: No known exceptions are thrown
        """
        return self._local_port

    @property
    def remote_ip_address(self):
        """ The remote ip address to which the connection is connected.

        :return: The remote ip address as a dotted string, or None if not\
                    connected remotely
        :rtype: str
        """
        return self._remote_ip_address

    @property
    def remote_port(self):
        """ The remote port to which the connection is connected.

        :return: The remote port, or None if not connected remotely
        :rtype: int
        """
        return self._remote_port

    def receive(self, timeout=None):
        """ Receive data from the connection

        :param timeout: The timeout, or None to wait forever
        :type timeout: None
        :return: The data received
        :rtype: bytestring
        :raise SpinnmanTimeoutException: If a timeout occurs before any data\
                    is received
        :raise SpinnmanIOException: If an error occurs receiving the data
        """
        try:
            self._socket.settimeout(timeout)
            return self._socket.recv(1024)
        except socket.timeout:
            raise SpinnmanTimeoutException("receive", timeout)
        except Exception as e:
            raise SpinnmanIOException(str(e))

    def send(self, data):
        """ Send data down this connection

        :param data: The data to be sent
        :type data: bytestring
        :raise SpinnmanIOException: If there is an error sending the data
        """
        try:
            self._socket.send(data)
        except Exception as e:
            raise SpinnmanIOException(str(e))

    def close(self):
        """ See\
            :py:meth:`spinnman.connections.Connection.close`
        """
        try:
            self._socket.shutdown(socket.SHUT_WR)
        except Exception:
            pass
        self._socket.close()

    def is_ready_to_receive(self, timeout=0):
        return len(select.select([self._socket], [], [], timeout)[0]) == 1

    def get_receive_method(self):
        return self.receive
