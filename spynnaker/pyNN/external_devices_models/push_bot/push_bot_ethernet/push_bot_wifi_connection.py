import logging
import platform
import select
import socket
import subprocess
from six import raise_from
from spinnman.connections.abstract_classes import Listenable, Connection
from spinnman.exceptions import SpinnmanIOException, SpinnmanTimeoutException

logger = logging.getLogger(__name__)
# A set of connections that have already been made
_existing_connections = dict()


def get_pushbot_wifi_connection(remote_host, remote_port=56000):
    """ Get an existing connection to a PushBot, or make a new one.

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
    """ A connection to a PushBot via Wi-Fi.
    """
    __slots__ = [
        "__local_ip_address",
        "__local_port",
        "__remote_ip_address",
        "__remote_port",
        "__socket"]

    def __init__(self, remote_host, remote_port=56000):
        """
        :param remote_host: The IP address of the PushBot
        :type remote_host: str
        :param remote_port: The port number of the PushBot (default 56000)
        :type remote_port: int
        :raise spinnman.exceptions.SpinnmanIOException: \
            If there is an error setting up the communication channel
        """
        try:
            # Create a TCP Socket
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            raise_from(SpinnmanIOException(
                "Error setting up socket: {}".format(e)), e)

        # Get the port to connect to
        self.__remote_port = int(remote_port)

        # Get the host to connect to
        self.__remote_ip_address = socket.gethostbyname(remote_host)

        try:
            logger.info("Trying to connect to the PushBot via Wi-Fi")
            # Connect the socket
            self.__socket.connect(
                (self.__remote_ip_address, self.__remote_port))
            logger.info("Succeeded in connecting to PushBot via Wi-Fi")

        except Exception as e:
            raise_from(SpinnmanIOException(
                "Error binding socket to {}:{}: {}".format(
                    self.__remote_ip_address, self.__remote_port, e)), e)

        # Get the details of where the socket is connected
        try:
            self.__local_ip_address, self.__local_port =\
                self.__socket.getsockname()

            # Ensure that a standard address is used for the INADDR_ANY
            # hostname
            if (self.__local_ip_address is None
                    or self.__local_ip_address == ""):
                self.__local_ip_address = "0.0.0.0"
        except Exception as e:
            raise_from(SpinnmanIOException(
                "Error querying socket: {}".format(e)), e)

        # Set a general timeout on the socket
        self.__socket.settimeout(0)

    def is_connected(self):
        """ See\
            :py:meth:`spinnman.connections.Connection.is_connected`
        """
        if platform.platform().lower().startswith("windows"):
            cmd_args = "-n 1 -w 1"
        else:
            cmd_args = "-c 1 -W 1"

        # check if machine is active and on the network
        for _ in range(5):  # Try up to five times...
            # Start a ping process
            process = subprocess.Popen(
                "ping " + cmd_args + " " + self.__remote_ip_address,
                shell=True, stdout=subprocess.PIPE)
            process.wait()
            if process.returncode == 0:
                # ping worked
                return True

        # If the ping fails this number of times, the host cannot be contacted
        return False

    @property
    def local_ip_address(self):
        """ The local IP address to which the connection is bound.

        :return: The local IP address as a dotted string, e.g. `0.0.0.0`
        :rtype: str
        :raise None: No known exceptions are thrown
        """
        return self.__local_ip_address

    @property
    def local_port(self):
        """ The local port to which the connection is bound.

        :return: The local port number
        :rtype: int
        :raise None: No known exceptions are thrown
        """
        return self.__local_port

    @property
    def remote_ip_address(self):
        """ The remote IP address to which the connection is connected.

        :return: The remote IP address as a dotted string, or None if not\
            connected remotely
        :rtype: str
        """
        return self.__remote_ip_address

    @property
    def remote_port(self):
        """ The remote port to which the connection is connected.

        :return: The remote port, or None if not connected remotely
        :rtype: int
        """
        return self.__remote_port

    def receive(self, timeout=None):
        """ Receive data from the connection

        :param timeout: The timeout, or None to wait forever
        :type timeout: float or None
        :return: The data received
        :rtype: bytestring
        :raise SpinnmanTimeoutException: \
            If a timeout occurs before any data is received
        :raise SpinnmanIOException: If an error occurs receiving the data
        """
        try:
            self.__socket.settimeout(timeout)
            return self.__socket.recv(1024)
        except socket.timeout:
            raise SpinnmanTimeoutException("receive", timeout)
        except Exception as e:
            raise_from(SpinnmanIOException(str(e)), e)

    def send(self, data):
        """ Send data down this connection

        :param data: The data to be sent
        :type data: bytestring
        :raise SpinnmanIOException: If there is an error sending the data
        """
        try:
            self.__socket.send(data)
        except Exception as e:
            raise_from(SpinnmanIOException(str(e)), e)

    def close(self):
        """ See\
            :py:meth:`spinnman.connections.Connection.close`
        """
        try:
            self.__socket.shutdown(socket.SHUT_WR)
        except Exception:
            pass
        self.__socket.close()

    def is_ready_to_receive(self, timeout=0):
        return bool(select.select([self.__socket], [], [], timeout)[0])

    def get_receive_method(self):
        return self.receive
