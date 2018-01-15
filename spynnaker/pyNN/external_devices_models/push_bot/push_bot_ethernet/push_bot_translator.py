from pacman.model.decorators import overrides

from spynnaker.pyNN.external_devices_models import AbstractEthernetTranslator
from spynnaker.pyNN.protocols import MunichIoEthernetProtocol
from spynnaker.pyNN.protocols import munich_io_spinnaker_link_protocol


from time import sleep
import logging
logger = logging.getLogger(__name__)


def _signed_int(uint_value):
    if uint_value > (2 ** 31):
        return uint_value - (2 ** 32)
    return uint_value


class PushBotTranslator(AbstractEthernetTranslator):
    """ Translates packets between PushBot Multicast packets and PushBot\
        WiFi Commands
    """
    __slots__ = [
        "_protocol",
        "_pushbot_wifi_connection"]

    def __init__(self, protocol, pushbot_wifi_connection):
        """

        :param protocol: The instance of the PushBot protocol to get keys from
        :param pushbot_wifi_connection: A WiFi connection to the PushBot
        """
        self._protocol = protocol
        self._pushbot_wifi_connection = pushbot_wifi_connection

    @overrides(AbstractEthernetTranslator.translate_control_packet)
    def translate_control_packet(self, multicast_packet):
        # pylint: disable=too-many-statements, too-many-branches
        key = multicast_packet.key

        # disable retina
        if key == self._protocol.disable_retina_key:
            logger.debug("Sending retina disable")
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.disable_retina())
            sleep(0.1)

        # set retina key (which doesn't do much for Ethernet)
        elif key == self._protocol.set_retina_transmission_key:
            logger.debug("Sending retina enable")
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.set_retina_transmission(
                    munich_io_spinnaker_link_protocol.GET_RETINA_PAYLOAD_VALUE(
                        multicast_packet.payload)))
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.enable_retina())

        # motor 0 leaky velocity command
        elif key == self._protocol.push_bot_motor_0_leaking_towards_zero_key:
            speed = _signed_int(multicast_packet.payload)
            logger.debug("Sending Motor 0 Leaky Velocity = %d", speed)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.motor_0_leaky_velocity(speed))

        # motor 0 permanent velocity command
        elif key == self._protocol.push_bot_motor_0_permanent_key:
            speed = _signed_int(multicast_packet.payload)
            logger.debug("Sending Motor 0 Velocity = %d", speed)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.motor_0_permanent_velocity(speed))

        # motor 1 leaky velocity command
        elif key == self._protocol.push_bot_motor_1_leaking_towards_zero_key:
            speed = _signed_int(multicast_packet.payload)
            logger.debug("Sending Motor 1 Leaky Velocity = %d", speed)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.motor_1_leaky_velocity(speed))

        # motor 1 permanent velocity command
        elif key == self._protocol.push_bot_motor_1_permanent_key:
            speed = _signed_int(multicast_packet.payload)
            logger.debug("Sending Motor 1 Velocity = %d", speed)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.motor_1_permanent_velocity(speed))

        # laser total period command
        elif key == self._protocol.push_bot_laser_config_total_period_key:
            period = _signed_int(multicast_packet.payload)
            logger.debug("Sending Laser Period = %d", period)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.laser_total_period(period))

        # laser active time
        elif key == self._protocol.push_bot_laser_config_active_time_key:
            time = _signed_int(multicast_packet.payload)
            logger.debug("Sending Laser Active Time = %d", time)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.laser_active_time(time))

        # laser frequency
        elif key == self._protocol.push_bot_laser_set_frequency_key:
            frequency = _signed_int(multicast_packet.payload)
            logger.debug("Sending Laser Frequency = %d", frequency)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.laser_frequency(frequency))

        # led total period command
        elif key == self._protocol.push_bot_led_total_period_key:
            period = _signed_int(multicast_packet.payload)
            logger.debug("Sending LED Period = %d", period)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.led_total_period(period))

        # front led active time
        elif key == self._protocol.push_bot_led_front_active_time_key:
            time = _signed_int(multicast_packet.payload)
            logger.debug("Sending Front LED Active Time = %d", time)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.led_front_active_time(time))

        # back led active time
        elif key == self._protocol.push_bot_led_back_active_time_key:
            time = _signed_int(multicast_packet.payload)
            logger.debug("Sending Back LED Active Time = %d", time)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.led_back_active_time(time))

        # led frequency
        elif key == self._protocol.push_bot_led_set_frequency_key:
            frequency = _signed_int(multicast_packet.payload)
            logger.debug("Sending LED Frequency = %d", frequency)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.led_frequency(frequency))

        # speaker total period
        elif key == self._protocol.push_bot_speaker_config_total_period_key:
            period = _signed_int(multicast_packet.payload)
            logger.debug("Sending Speaker Period = %d", period)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.speaker_total_period(period))

        # speaker active time
        elif key == self._protocol.push_bot_speaker_config_active_time_key:
            time = _signed_int(multicast_packet.payload)
            logger.debug("Sending Speaker Active Time = %d", time)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.speaker_active_time(time))

        # speaker frequency
        elif key == self._protocol.push_bot_speaker_set_tone_key:
            frequency = _signed_int(multicast_packet.payload)
            logger.debug("Sending Speaker Frequency = %d", frequency)
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.speaker_frequency(frequency))

        # motor enable
        elif (key == self._protocol.enable_disable_motor_key and
              multicast_packet.payload == 1):
            logger.debug("Sending Motor Enable")
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.enable_motor())

        # motor disable
        elif (key == self._protocol.enable_disable_motor_key and
              multicast_packet.payload == 0):
            logger.debug("Sending Motor Disable")
            self._pushbot_wifi_connection.send(
                MunichIoEthernetProtocol.disable_motor())

        # detecting set mode (which has no context in Ethernet protocol
        elif key == self._protocol.set_mode().key:
            logger.debug("Ignoring set mode command")

        # otherwise no idea what command is, so raise warning and ignore
        else:
            logger.warn("Unknown Pushbot command: %s", multicast_packet)
