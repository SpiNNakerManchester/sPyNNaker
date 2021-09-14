# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This contains functions and classes for handling external devices such as the
PushBot (http://spinnakermanchester.github.io/docs/push_bot/).

.. note::
    When using external devices, it is normally important to configure your
    SpiNNaker system to run in real-time mode, which usually reduces numerical
    accuracy to gain performance.
"""
import os
from spinn_utilities.socket_address import SocketAddress
from spinnman.messages.eieio import EIEIOType
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon
from spynnaker.pyNN.external_devices_models import (
    AbstractEthernetController, AbstractEthernetSensor,
    ArbitraryFPGADevice, ExternalCochleaDevice, ExternalFPGARetinaDevice,
    MunichMotorDevice, MunichRetinaDevice, ExternalDeviceLifControl,
    SPIFRetinaDevice, ICUBRetinaDevice)
from spynnaker.pyNN.models.utility_models.spike_injector import (
    SpikeInjector as
    ExternalDeviceSpikeInjector)
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.connections import (
    EthernetCommandConnection, EthernetControlConnection,
    SpynnakerLiveSpikesConnection, SpynnakerPoissonControlConnection)
from spynnaker.pyNN.external_devices_models.push_bot.control import (
    PushBotLifEthernet, PushBotLifSpinnakerLink)
from spynnaker.pyNN.external_devices_models.push_bot.spinnaker_link import (
    PushBotSpiNNakerLinkRetinaDevice,
    PushBotSpiNNakerLinkLaserDevice, PushBotSpiNNakerLinkLEDDevice,
    PushBotSpiNNakerLinkMotorDevice, PushBotSpiNNakerLinkSpeakerDevice)
from spynnaker.pyNN.external_devices_models.push_bot.ethernet import (
    PushBotEthernetLaserDevice, PushBotEthernetLEDDevice,
    PushBotEthernetMotorDevice, PushBotEthernetRetinaDevice,
    PushBotEthernetSpeakerDevice)
from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotLaser, PushBotLED, PushBotMotor, PushBotRetinaResolution,
    PushBotSpeaker, PushBotRetinaViewer)
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.spynnaker_external_device_plugin_manager import (
    SpynnakerExternalDevicePluginManager as
    Plugins)
from spynnaker.pyNN.models.populations import Population

# useful functions
add_database_socket_address = Plugins.add_database_socket_address
activate_live_output_to = Plugins.activate_live_output_to
activate_live_output_for = Plugins.activate_live_output_for
add_poisson_live_rate_control = Plugins.add_poisson_live_rate_control

AbstractSpiNNakerCommon.register_binary_search_path(
    os.path.dirname(model_binaries.__file__))
spynnaker_external_devices = Plugins()

__all__ = [
    "EIEIOType",

    # General Devices
    "ExternalCochleaDevice", "ExternalFPGARetinaDevice",
    "MunichRetinaDevice", "MunichMotorDevice", "ArbitraryFPGADevice",
    "PushBotRetinaViewer", "ExternalDeviceLifControl", "SPIFRetinaDevice",
    "ICUBRetinaDevice",

    # PushBot Parameters
    "MunichIoSpiNNakerLinkProtocol",
    "PushBotLaser", "PushBotLED", "PushBotMotor", "PushBotSpeaker",
    "PushBotRetinaResolution",

    # PushBot Ethernet Parts
    "PushBotLifEthernet", "PushBotEthernetLaserDevice",
    "PushBotEthernetLEDDevice", "PushBotEthernetMotorDevice",
    "PushBotEthernetSpeakerDevice", "PushBotEthernetRetinaDevice",

    # PushBot SpiNNaker Link Parts
    "PushBotLifSpinnakerLink", "PushBotSpiNNakerLinkLaserDevice",
    "PushBotSpiNNakerLinkLEDDevice", "PushBotSpiNNakerLinkMotorDevice",
    "PushBotSpiNNakerLinkSpeakerDevice", "PushBotSpiNNakerLinkRetinaDevice",

    # Connections
    "SpynnakerLiveSpikesConnection",
    "SpynnakerPoissonControlConnection",

    # Provided functions
    "activate_live_output_for",
    "activate_live_output_to",
    "SpikeInjector",
    "register_database_notification_request",
    "run_forever",
    "add_poisson_live_rate_control"
]


def run_forever(sync_time=0):
    """ Supports running forever in PyNN 0.8/0.9 format

    :param sync_time:
        The time in milliseconds after which to pause before the host must
        continue the simulation
    :return: when the application has started running on the SpiNNaker platform
    """
    get_simulator().run(None, sync_time)


def run_sync(run_time, sync_time):
    """ Run in steps of the given number of milliseconds pausing between\
        for a signal to be sent from the host

    :param float run_time: The time in milliseconds to run the simulation for
    :param float sync_time: The time in milliseconds to pause before allowing
    """
    get_simulator().run(run_time, sync_time)


def continue_simulation():
    """ Continue a synchronised simulation
    """
    get_simulator().continue_simulation()


def request_stop():
    """ Request a stop in the simulation without a complete stop.  Will stop\
        after the next auto-pause-and-resume cycle
    """
    get_simulator().stop_run()


def register_database_notification_request(hostname, notify_port, ack_port):
    """ Adds a socket system which is registered with the notification protocol

    :param str hostname: hostname to connect to
    :param int notify_port: port num for the notify command
    :param int ack_port: port num for the acknowledge command
    """
    spynnaker_external_devices.add_socket_address(
        SocketAddress(hostname, notify_port, ack_port))


# Store the connection to be used by multiple users
__ethernet_control_connection = None


def EthernetControlPopulation(
        n_neurons, model, label=None, local_host=None, local_port=None,
        database_notify_port_num=None, database_ack_port_num=None):
    """ Create a PyNN population that can be included in a network to\
        control an external device which is connected to the host

    :param int n_neurons: The number of neurons in the control population
    :param type model:
        Class of a model that creates a vertex of type
        :py:class:`AbstractEthernetController`
    :param label: An optional label for the population
    :type label: str or None
    :param local_host:
        The optional local host IP address to listen on for commands
    :type local_host: str or None
    :param local_port: The optional local port to listen on for commands
    :type local_port: int or None
    :param database_ack_port_num:
        The optional port to which responses to the database notification
        protocol are to be sent
    :type database_ack_port_num: int or None
    :param database_notify_port_num:
        The optional port to which notifications from the database
        notification protocol are to be sent
    :type database_notify_port_num: int or None
    :return:
        A pyNN Population which can be used as the target of a Projection.
        Note that the Population can also be used as the source of a
        Projection, but it might not send spikes.
    :rtype: ~spynnaker.pyNN.models.populations.Population
    :raises Exception: If an invalid model class is used.
    """
    # pylint: disable=protected-access, too-many-arguments, too-many-locals
    population = Population(n_neurons, model, label=label)
    vertex = population._vertex
    if not isinstance(vertex, AbstractEthernetController):
        raise Exception(
            "Vertex must be an instance of AbstractEthernetController")
    translator = vertex.get_message_translator()
    live_packet_gather_label = "EthernetControlReceiver"
    global __ethernet_control_connection
    if __ethernet_control_connection is None:
        __ethernet_control_connection = EthernetControlConnection(
            translator, vertex.label, live_packet_gather_label, local_host,
            local_port)
        Plugins.add_database_socket_address(
            __ethernet_control_connection.local_ip_address,
            __ethernet_control_connection.local_port, database_ack_port_num)
    else:
        __ethernet_control_connection.add_translator(vertex.label, translator)
    devices_with_commands = [
        device for device in vertex.get_external_devices()
        if isinstance(device, AbstractSendMeMulticastCommandsVertex)]
    if devices_with_commands:
        ethernet_command_connection = EthernetCommandConnection(
            translator, devices_with_commands, local_host,
            database_notify_port_num)
        Plugins.add_database_socket_address(
            ethernet_command_connection.local_ip_address,
            ethernet_command_connection.local_port, database_ack_port_num)
    Plugins.update_live_packet_gather_tracker(
        vertex, live_packet_gather_label,
        port=__ethernet_control_connection.local_port,
        hostname=__ethernet_control_connection.local_ip_address,
        message_type=EIEIOType.KEY_PAYLOAD_32_BIT,
        payload_as_time_stamps=False, use_payload_prefix=False,
        partition_ids=vertex.get_outgoing_partition_ids())
    return population


def EthernetSensorPopulation(
        device, local_host=None,
        database_notify_port_num=None, database_ack_port_num=None):
    """ Create a pyNN population which can be included in a network to\
        receive spikes from a device connected to the host

    :param AbstractEthernetSensor device: The sensor model
    :param local_host:
        The optional local host IP address to listen on for database
        notification
    :type local_host: str or None
    :param database_ack_port_num:
        The optional port to which responses to the database notification
        protocol are to be sent
    :type database_ack_port_num: int or None
    :param database_notify_port_num:
        The optional port to which notifications from the database
        notification protocol are to be sent
    :type database_notify_port_num: int or None
    :return:
        A pyNN Population which can be used as the source of a Projection.
        Note that the Population cannot be used as the target of a Projection.
    :rtype: ~spynnaker.pyNN.models.populations.Population
    """
    if not isinstance(device, AbstractEthernetSensor):
        raise Exception("Device must be an instance of AbstractEthernetSensor")
    injector_params = dict(device.get_injector_parameters())

    population = Population(
        device.get_n_neurons(), SpikeInjector(notify=False),
        label=device.get_injector_label(),
        additional_parameters=injector_params)
    if isinstance(device, AbstractSendMeMulticastCommandsVertex):
        cmd_conn = EthernetCommandConnection(
            device.get_translator(), [device], local_host,
            database_notify_port_num)
        Plugins.add_database_socket_address(
            cmd_conn.local_ip_address, cmd_conn.local_port,
            database_ack_port_num)
    db_conn = device.get_database_connection()
    if db_conn is not None:
        Plugins.add_database_socket_address(
            db_conn.local_ip_address, db_conn.local_port,
            database_ack_port_num)
    return population


def SpikeInjector(
        notify=True, database_notify_host=None, database_notify_port_num=None,
        database_ack_port_num=None):
    """ Supports creating a spike injector that can be added to the\
        application graph.

    :param bool notify: Whether to register for notifications
    :param database_notify_host: the hostname for the device which is
        listening to the database notification.
    :type database_notify_host: str or None
    :param database_ack_port_num: the port number to which a external device
        will acknowledge that they have finished reading the database and are
        ready for it to start execution
    :type database_ack_port_num: int or None
    :param database_notify_port_num: The port number to which a external
        device will receive the database is ready command
    :type database_notify_port_num: int or None
    :return: The spike injector model object that can be placed in a pyNN
        :py:class:`~spynnaker.pyNN.models.populations.Population`.
    :rtype: ~spynnaker.pyNN.models.abstract_pynn_model.AbstractPyNNModel
    """
    # pylint: disable=too-many-arguments
    if notify:
        Plugins.add_database_socket_address(
            database_notify_host, database_notify_port_num,
            database_ack_port_num)
    return ExternalDeviceSpikeInjector()
