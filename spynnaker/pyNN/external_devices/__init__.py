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
"""
This contains functions and classes for handling external devices such as the
PushBot (https://spinnakermanchester.github.io/docs/push_bot/).

.. note::
    When using external devices, it is normally important to configure your
    SpiNNaker system to run in real-time mode, which usually reduces numerical
    accuracy to gain performance.
"""
import os
from typing import Optional
from spinn_utilities.socket_address import SocketAddress
from spinnman.messages.eieio import EIEIOType
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utilities.utility_objs import (
    LivePacketGatherParameters)
from spynnaker.pyNN.external_devices_models import (
    AbstractEthernetController, AbstractEthernetSensor,
    ArbitraryFPGADevice, ExternalCochleaDevice, ExternalFPGARetinaDevice,
    MunichMotorDevice, MunichRetinaDevice, ExternalDeviceLifControl,
    SPIFRetinaDevice, ICUBRetinaDevice, SPIFOutputDevice)
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.connections import (
    EthernetCommandConnection, EthernetControlConnection,
    SpynnakerLiveSpikesConnection, SpynnakerPoissonControlConnection,
    SPIFLiveSpikesConnection)
from spynnaker.pyNN.data import SpynnakerDataView
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
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.populations.population import (
    Population, _CellTypeArg)
from spynnaker.pyNN.models.utility_models.spike_injector import (
    SpikeInjector as ExternalDeviceSpikeInjector)
from spynnaker.pyNN import protocols
from spynnaker.pyNN.spinnaker import SpiNNaker


# useful functions
add_database_socket_address = Plugins.add_database_socket_address
activate_live_output_to = Plugins.activate_live_output_to
activate_live_output_for = Plugins.activate_live_output_for
add_poisson_live_rate_control = Plugins.add_poisson_live_rate_control

SpynnakerDataView.register_binary_search_path(
    os.path.dirname(model_binaries.__file__))
spynnaker_external_devices = Plugins()

__all__ = [
    "EIEIOType",

    # General Devices
    "ExternalCochleaDevice", "ExternalFPGARetinaDevice",
    "MunichRetinaDevice", "MunichMotorDevice", "ArbitraryFPGADevice",
    "PushBotRetinaViewer", "ExternalDeviceLifControl", "SPIFRetinaDevice",
    "ICUBRetinaDevice", "SPIFOutputDevice",

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
    "SPIFLiveSpikesConnection",

    # Provided functions
    "activate_live_output_for",
    "activate_live_output_to",
    "SpikeInjector",
    "register_database_notification_request",
    "run_forever",
    "add_poisson_live_rate_control",
    "protocols"
]
# Cache of the simulator provided by pyNN/__init__py
__simulator: Optional[SpiNNaker] = None


def run_forever(sync_time: float = 0.0):
    """
    Supports running forever in PyNN 0.8/0.9 format.

    :param sync_time:
        The time in milliseconds after which to pause before the host must
        continue the simulation.
    :return:
        Only when the application has started running on the SpiNNaker
        platform; no value is returned.
    """
    SpynnakerDataView.check_user_can_act()
    assert __simulator is not None, "no simulator set up"
    __simulator.run(None, sync_time)


def run_sync(run_time: float, sync_time: float):
    """
    Run in steps of the given number of milliseconds pausing between
    for a signal to be sent from the host.

    :param float run_time: The time in milliseconds to run the simulation for
    :param float sync_time: The time in milliseconds to pause before allowing
    """
    SpynnakerDataView.check_user_can_act()
    assert __simulator is not None, "no simulator set up"
    __simulator.run(run_time, sync_time)


def continue_simulation() -> None:
    """
    Continue a synchronised simulation.
    """
    SpynnakerDataView.check_valid_simulator()
    assert __simulator is not None, "no simulator set up"
    __simulator.continue_simulation()


def request_stop() -> None:
    """
    Request a stop in the simulation without a complete stop.  Will stop
    after the next auto-pause-and-resume cycle.
    """
    SpynnakerDataView.check_valid_simulator()
    assert __simulator is not None, "no simulator set up"
    __simulator.stop_run()


def register_database_notification_request(
        hostname: str, notify_port: int, ack_port: int):
    """
    Adds a socket system which is registered with the notification protocol.

    :param str hostname: hostname to connect to
    :param int notify_port: UDP port number for the notify command
    :param int ack_port: UDP port number for the acknowledge command
    """
    SpynnakerDataView.add_database_socket_address(
        SocketAddress(hostname, notify_port, ack_port))


# Store the connection to be used by multiple users
__ethernet_control_connection: Optional[EthernetControlConnection] = None


def EthernetControlPopulation(
        n_neurons: int, model: _CellTypeArg, label: Optional[str] = None,
        local_host: Optional[str] = None, local_port: Optional[int] = None,
        database_notify_port_num: Optional[int] = None,
        database_ack_port_num: Optional[int] = None) -> Population:
    """
    Create a PyNN population that can be included in a network to
    control an external device which is connected to the host.

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

        .. note::
            The Population can also be used as the source of a
            Projection, but it might not send spikes.
    :rtype: ~spynnaker.pyNN.models.populations.Population
    :raises TypeError: If an invalid model class is used.
    """
    # pylint: disable=protected-access, too-many-arguments, global-statement
    population = Population(n_neurons, model, label=label)
    vertex = population._apv
    aec = vertex
    if not isinstance(aec, AbstractEthernetController):
        raise TypeError(
            "Vertex must be an instance of AbstractEthernetController")
    translator = aec.get_message_translator()
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
    params = LivePacketGatherParameters(
        port=__ethernet_control_connection.local_port,
        hostname=__ethernet_control_connection.local_ip_address,
        message_type=EIEIOType.KEY_PAYLOAD_32_BIT,
        payload_as_time_stamps=False, use_payload_prefix=False,
        label=live_packet_gather_label)
    Plugins.update_live_packet_gather_tracker(
        vertex, params, vertex.get_outgoing_partition_ids())
    return population


def EthernetSensorPopulation(
        device: AbstractEthernetSensor, local_host: Optional[str] = None,
        database_notify_port_num: Optional[int] = None,
        database_ack_port_num: Optional[int] = None) -> Population:
    """
    Create a pyNN population which can be included in a network to
    receive spikes from a device connected to the host.

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

        .. note::
            The Population cannot be used as the target of a Projection.
    :rtype: ~spynnaker.pyNN.models.populations.Population
    :raises TypeError: If an invalid model class is used.
    """
    if not isinstance(device, AbstractEthernetSensor):
        raise TypeError(
            "Device must be an instance of AbstractEthernetSensor")
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
        notify: bool = True, database_notify_host: Optional[str] = None,
        database_notify_port_num: Optional[int] = None,
        database_ack_port_num: Optional[int] = None) -> AbstractPyNNModel:
    """
    Supports creating a spike injector that can be added to the
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
    :rtype: AbstractPyNNModel
    """
    if notify:
        Plugins.add_database_socket_address(
            database_notify_host, database_notify_port_num,
            database_ack_port_num)
    return ExternalDeviceSpikeInjector()


def _set_simulator(simulator: SpiNNaker):
    """
    Should only be called by pyNN/__init__py setup method.

    Any other uses is not supported.

    :param spynnaker.pyNN.spinnaker.SpiNNaker simulator:
    """
    global __simulator  # pylint: disable=global-statement
    __simulator = simulator
