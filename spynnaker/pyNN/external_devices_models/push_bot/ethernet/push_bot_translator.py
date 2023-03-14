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
from time import sleep
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.external_devices_models import AbstractEthernetTranslator
from spynnaker.pyNN.protocols import (
    MunichIoEthernetProtocol, munich_io_spinnaker_link_protocol)

logger = FormatAdapter(logging.getLogger(__name__))


def _signed_int(uint_value):
    if uint_value > (2 ** 31):
        return uint_value - (2 ** 32)
    return uint_value


class PushBotTranslator(AbstractEthernetTranslator):
    """ Translates packets between PushBot Multicast packets and PushBot\
        Wi-Fi Commands
    """
    __slots__ = [
        "__protocol",
        "__pushbot_wifi_connection"]

    def __init__(self, protocol, pushbot_wifi_connection):
        """
        :param protocol: The instance of the PushBot protocol to get keys from
        :type protocol: MunichIoEthernetProtocol
        :param pushbot_wifi_connection: A Wi-Fi connection to the PushBot
        :type pushbot_wifi_connection: PushBotWIFIConnection
        """
        self.__protocol = protocol
        self.__pushbot_wifi_connection = pushbot_wifi_connection

    @overrides(AbstractEthernetTranslator.translate_control_packet)
    def translate_control_packet(self, multicast_packet):
        # pylint: disable=too-many-statements, too-many-branches
        key = multicast_packet.key

        # disable retina
        if key == self.__protocol.disable_retina_key:
            logger.debug("Sending retina disable")
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.disable_retina())
            sleep(0.1)

        # set retina key (which doesn't do much for Ethernet)
        elif key == self.__protocol.set_retina_transmission_key:
            logger.debug("Sending retina enable")
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.set_retina_transmission(
                    munich_io_spinnaker_link_protocol.GET_RETINA_PAYLOAD_VALUE(
                        multicast_packet.payload)))
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.enable_retina())

        # motor 0 leaky velocity command
        elif key == self.__protocol.push_bot_motor_0_leaking_towards_zero_key:
            speed = _signed_int(multicast_packet.payload)
            logger.debug("Sending Motor 0 Leaky Velocity = {}", speed)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.motor_0_leaky_velocity(speed))

        # motor 0 permanent velocity command
        elif key == self.__protocol.push_bot_motor_0_permanent_key:
            speed = _signed_int(multicast_packet.payload)
            logger.debug("Sending Motor 0 Velocity = {}", speed)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.motor_0_permanent_velocity(speed))

        # motor 1 leaky velocity command
        elif key == self.__protocol.push_bot_motor_1_leaking_towards_zero_key:
            speed = _signed_int(multicast_packet.payload)
            logger.debug("Sending Motor 1 Leaky Velocity = {}", speed)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.motor_1_leaky_velocity(speed))

        # motor 1 permanent velocity command
        elif key == self.__protocol.push_bot_motor_1_permanent_key:
            speed = _signed_int(multicast_packet.payload)
            logger.debug("Sending Motor 1 Velocity = {}", speed)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.motor_1_permanent_velocity(speed))

        # laser total period command
        elif key == self.__protocol.push_bot_laser_config_total_period_key:
            period = _signed_int(multicast_packet.payload)
            logger.debug("Sending Laser Period = {}", period)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.laser_total_period(period))

        # laser active time
        elif key == self.__protocol.push_bot_laser_config_active_time_key:
            time = _signed_int(multicast_packet.payload)
            logger.debug("Sending Laser Active Time = {}", time)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.laser_active_time(time))

        # laser frequency
        elif key == self.__protocol.push_bot_laser_set_frequency_key:
            frequency = _signed_int(multicast_packet.payload)
            logger.debug("Sending Laser Frequency = {}", frequency)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.laser_frequency(frequency))

        # led total period command
        elif key == self.__protocol.push_bot_led_total_period_key:
            period = _signed_int(multicast_packet.payload)
            logger.debug("Sending LED Period = {}", period)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.led_total_period(period))

        # front led active time
        elif key == self.__protocol.push_bot_led_front_active_time_key:
            time = _signed_int(multicast_packet.payload)
            logger.debug("Sending Front LED Active Time = {}", time)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.led_front_active_time(time))

        # back led active time
        elif key == self.__protocol.push_bot_led_back_active_time_key:
            time = _signed_int(multicast_packet.payload)
            logger.debug("Sending Back LED Active Time = {}", time)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.led_back_active_time(time))

        # led frequency
        elif key == self.__protocol.push_bot_led_set_frequency_key:
            frequency = _signed_int(multicast_packet.payload)
            logger.debug("Sending LED Frequency = {}", frequency)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.led_frequency(frequency))

        # speaker total period
        elif key == self.__protocol.push_bot_speaker_config_total_period_key:
            period = _signed_int(multicast_packet.payload)
            logger.debug("Sending Speaker Period = {}", period)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.speaker_total_period(period))

        # speaker active time
        elif key == self.__protocol.push_bot_speaker_config_active_time_key:
            time = _signed_int(multicast_packet.payload)
            logger.debug("Sending Speaker Active Time = {}", time)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.speaker_active_time(time))

        # speaker frequency
        elif key == self.__protocol.push_bot_speaker_set_tone_key:
            frequency = _signed_int(multicast_packet.payload)
            logger.debug("Sending Speaker Frequency = {}", frequency)
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.speaker_frequency(frequency))

        # motor enable
        elif (key == self.__protocol.enable_disable_motor_key and
              multicast_packet.payload == 1):
            logger.debug("Sending Motor Enable")
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.enable_motor())

        # motor disable
        elif (key == self.__protocol.enable_disable_motor_key and
              multicast_packet.payload == 0):
            logger.debug("Sending Motor Disable")
            self.__pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.disable_motor())

        # detecting set mode (which has no context in Ethernet protocol
        elif key == self.__protocol.set_mode().key:
            logger.debug("Ignoring set mode command")

        # otherwise no idea what command is, so raise warning and ignore
        else:
            logger.warning("Unknown PushBot command: {}", multicast_packet)
