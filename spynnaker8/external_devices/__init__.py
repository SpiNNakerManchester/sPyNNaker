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
from spinnman.messages.eieio import EIEIOType
from spynnaker.pyNN.external_devices_models import (
    ArbitraryFPGADevice, ExternalCochleaDevice, ExternalFPGARetinaDevice,
    MunichMotorDevice, MunichRetinaDevice, ExternalDeviceLifControl)
from spynnaker.pyNN.connections import (
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
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6

import spynnaker.pyNN.external_devices as moved_code

# useful functions
add_database_socket_address = moved_code.add_database_socket_address
activate_live_output_to = moved_code.activate_live_output_to
activate_live_output_for = moved_code.activate_live_output_for
add_poisson_live_rate_control = moved_code.add_poisson_live_rate_control

__all__ = [
    "EIEIOType",

    # General Devices
    "ExternalCochleaDevice", "ExternalFPGARetinaDevice",
    "MunichRetinaDevice", "MunichMotorDevice", "ArbitraryFPGADevice",
    "PushBotRetinaViewer", "ExternalDeviceLifControl",

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

moved_in_v6("spynnaker8.external_devices",
            "spynnaker.pyNN.external_devices")


def run_forever(sync_time=0):
    """ Supports running forever in PyNN 0.8/0.9 format

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.external_devices` instead.
    """
    moved_in_v6("spynnaker8.external_devices",
                "spynnaker.pyNN.external_devices")
    moved_code.run_forever(sync_time)


def run_sync(run_time, sync_time):
    """ Run in steps of the given number of milliseconds pausing between\
        for a signal to be sent from the host

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.external_devices` instead.
    """
    moved_in_v6("spynnaker8.external_devices",
                "spynnaker.pyNN.external_devices")
    moved_code.run_sync(run_time, sync_time)


def continue_simulation():
    """ Continue a synchronised simulation

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.external_devices` instead.
    """
    moved_in_v6("spynnaker8.external_devices",
                "spynnaker.pyNN.external_devices")
    moved_code.continue_simulation()


def request_stop():
    """ Request a stop in the simulation without a complete stop.  Will stop\
        after the next auto-pause-and-resume cycle

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.external_devices` instead.
    """
    moved_in_v6("spynnaker8.external_devices",
                "spynnaker.pyNN.external_devices")
    moved_code.request_stop()


def register_database_notification_request(hostname, notify_port, ack_port):
    """ Adds a socket system which is registered with the notification protocol

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.external_devices` instead.
    """
    moved_in_v6("spynnaker8.external_devices",
                "spynnaker.pyNN.external_devices")
    moved_code.register_database_notification_request(
        hostname, notify_port, ack_port)


# Store the connection to be used by multiple users
__ethernet_control_connection = None


def EthernetControlPopulation(
        n_neurons, model, label=None, local_host=None, local_port=None,
        database_notify_port_num=None, database_ack_port_num=None):
    """ Create a PyNN population that can be included in a network to\
        control an external device which is connected to the host

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.external_devices` instead.
    """
    moved_in_v6("spynnaker8.external_devices",
                "spynnaker.pyNN.external_devices")
    return moved_code.EthernetControlPopulation(
        n_neurons, model, label, local_host, local_port,
        database_notify_port_num, database_ack_port_num)


def EthernetSensorPopulation(
        device, local_host=None,
        database_notify_port_num=None, database_ack_port_num=None):
    """ Create a pyNN population which can be included in a network to\
        receive spikes from a device connected to the host

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.external_devices` instead.
    """
    moved_in_v6("spynnaker8.external_devices",
                "spynnaker.pyNN.external_devices")
    return moved_code.EthernetSensorPopulation(
        device, local_host, database_notify_port_num, database_ack_port_num)


def SpikeInjector(
        notify=True, database_notify_host=None, database_notify_port_num=None,
        database_ack_port_num=None):
    """ Supports creating a spike injector that can be added to the\
        application graph.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.external_devices` instead.
    """
    # pylint: disable=too-many-arguments
    moved_in_v6("spynnaker8.external_devices",
                "spynnaker.pyNN.external_devices")
    return moved_code.SpikeInjector(
        notify, database_notify_host, database_notify_port_num,
        database_ack_port_num)
