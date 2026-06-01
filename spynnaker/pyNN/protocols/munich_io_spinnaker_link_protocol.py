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

from enum import Enum
from typing import Optional
from spinn_front_end_common.utility_models import MultiCastCommand
from spinn_front_end_common.utilities.exceptions import ConfigurationException

# structure of command is KKKKKKKKKKKKKKKKKKKKK-IIIIIII-F-DDD
# K = ignored key at the top of the command
# I = instruction
# F = format
# D = device
_OFFSET_TO_IGNORED_KEY = 11
_OFFSET_TO_I = 4
_OFFSET_TO_F = 3
_OFFSET_TO_D = 0
_KEY_MASK = 0xFFFFF800
_I_MASK = 0x7F0
_F_MASK = 0x8
_D_MASK = 0x7


# UART masks and shifts
RETINA_UART_SHIFT = 3 + _OFFSET_TO_I
RETINA_WITHOUT_UART_MASK = 0x670
PUSH_BOT_LASER_LED_SPEAKER_FREQUENCY_UART_SHIFT = 1 + _OFFSET_TO_D
PUSH_BOT_MOTOR_WITHOUT_UART_MASK = 0x7C0
PUSH_BOT_MOTOR_UART_SHIFT = 0 + _OFFSET_TO_I


def _munich_key(instr_id: int, dim: int = 0, format_bit: int = 0) -> int:
    return ((instr_id << _OFFSET_TO_I) | (format_bit << _OFFSET_TO_F) |
            (dim << _OFFSET_TO_D))


def get_munich_i(key: int) -> int:
    """
    :param key:
    :returns: Get the instruction field from the key.
    """
    return key & _I_MASK


def get_munich_f(key: int) -> int:
    """
    :returns: The format field from the key.
    """
    return key & _F_MASK


def get_munich_d(key: int) -> int:
    """
    :returns: The device field from the key.
    """
    return key & _D_MASK


def get_retina_i(key: int) -> int:
    """
    :param key:
    :returns: The key with the UART mask.

    """
    return key & RETINA_WITHOUT_UART_MASK


def get_push_bot_laser_led_speaker_frequency_i(key: int) -> int:
    """
    :param key:
    :returns: The instruction field from the key with the I mask.
    """
    return get_munich_i(key)


def get_push_bot_motor_i(key: int) -> int:
    """
    :returns:
       The key without the universal asynchronous receiver/transmitter mask.
    """

    return key & PUSH_BOT_MOTOR_WITHOUT_UART_MASK


# Specific fields in the key
_SENSOR_OUTGOING_OFFSET_TO_D = 2
_SENSOR_OUTGOING_OFFSET_TO_I = 7

# Payload fields
_PAYLOAD_RETINA_PAYLOAD_OFFSET = 29
_PAYLOAD_RETINA_PAYLOAD_MASK = 0xE0000000
_PAYLOAD_RETINA_KEY_OFFSET = 26
_PAYLOAD_RETINA_KEY_MASK = 0x1C000000
_PAYLOAD_SENSOR_ID_OFFSET = 27
_PAYLOAD_OFFSET_FOR_SENSOR_TIME = 0


def GET_RETINA_KEY_VALUE(payload: int) -> int:
    # pylint: disable=invalid-name
    """
    :param payload:
    :returns: The payload with the retina key mask and offset.
    """
    return (payload & _PAYLOAD_RETINA_KEY_MASK) >> _PAYLOAD_RETINA_KEY_OFFSET


def GET_RETINA_PAYLOAD_VALUE(payload: int) -> int:
    # pylint: disable=invalid-name
    """
    :param payload:
    :returns: The payload with the retina payload mask and offset.
    """
    return (
        (payload & _PAYLOAD_RETINA_PAYLOAD_MASK) >>
        _PAYLOAD_RETINA_PAYLOAD_OFFSET
    )


#: command key for setting up the master key of the board
CONFIGURE_MASTER_KEY = _munich_key(127, 0)

#: command key for setting up what mode of device running on the board
CHANGE_MODE = _munich_key(127, 1)

#: command for turning off retina output
DISABLE_RETINA_EVENT_STREAMING = _munich_key(0, 0)

#: command for retina where payload is events
ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION = _munich_key(0, 1)

#: command for retina where events are the key
ACTIVE_RETINA_EVENT_STREAMING_SET_KEY = _munich_key(0, 2)

#: set timer / counter for timestamps
SET_TIMER_COUNTER_FOR_TIMESTAMPS = _munich_key(0, 3)

#: handle master / slave time sync
MASTER_SLAVE_KEY = _munich_key(0, 4)

#: command for setting bias (whatever the check that is)
BIAS_KEY = _munich_key(0, 5)

#: reset retina key.
RESET_RETINA_KEY = _munich_key(0, 7)

#: request on-board sensor data
SENSOR_REPORTING_OFF_KEY = _munich_key(1, 0)

#: poll sensors once
POLL_SENSORS_ONCE_KEY = _munich_key(1, 1)

#: poll sensors continuously
POLL_SENSORS_CONTINUOUSLY_KEY = _munich_key(1, 2)

#: disable motor
ENABLE_DISABLE_MOTOR_KEY = _munich_key(2, 0)

#: run motor for total period
MOTOR_RUN_FOR_PERIOD_KEY = _munich_key(2, 1)

#: raw output for motor 0 (permanent)
MOTOR_0_RAW_PERM_KEY = _munich_key(2, 4)

#: raw output for motor 1 (permanent)
MOTOR_1_RAW_PERM_KEY = _munich_key(2, 5)

#: raw output for motor 0 (leak towards 0)
MOTOR_0_RAW_LEAK_KEY = _munich_key(2, 6)

#: raw output for motor 1 (leak towards 0)
MOTOR_1_RAW_LEAK_KEY = _munich_key(2, 7)

#: motor output duration timer period
MOTOR_TIMER_A_TOTAL_PERIOD_KEY = _munich_key(3, 0)
#: motor output duration timer period
MOTOR_TIMER_B_TOTAL_PERIOD_KEY = _munich_key(3, 2)
#: motor output duration timer period
MOTOR_TIMER_C_TOTAL_PERIOD_KEY = _munich_key(3, 4)

#: motor output ratio active period
MOTOR_TIMER_A_CHANNEL_0_ACTIVE_PERIOD_KEY = _munich_key(4, 0)
#: motor output ratio active period
MOTOR_TIMER_A_CHANNEL_1_ACTIVE_PERIOD_KEY = _munich_key(4, 1)
#: motor output ratio active period
MOTOR_TIMER_B_CHANNEL_0_ACTIVE_PERIOD_KEY = _munich_key(4, 2)
#: motor output ratio active period
MOTOR_TIMER_B_CHANNEL_1_ACTIVE_PERIOD_KEY = _munich_key(4, 3)
#: motor output ratio active period
MOTOR_TIMER_C_CHANNEL_0_ACTIVE_PERIOD_KEY = _munich_key(4, 4)
#: motor output ratio active period
MOTOR_TIMER_C_CHANNEL_1_ACTIVE_PERIOD_KEY = _munich_key(4, 5)

#: digital IO Signals
QUERY_STATES_LINES_KEY = _munich_key(5, 0)

#: set output pattern to payload
SET_OUTPUT_PATTERN_KEY = _munich_key(5, 1)

#: add payload (logic or (payload)) to current output
ADD_PAYLOAD_TO_CURRENT_OUTPUT_KEY = _munich_key(5, 2)

#: remove payload (logic or (payload)) to current output from current output
REMOVE_PAYLOAD_TO_CURRENT_OUTPUT_KEY = _munich_key(5, 3)

#: set payload pins to high impedance
SET_PAYLOAD_TO_HIGH_IMPEDANCE_KEY = _munich_key(5, 4)

#: set laser params for PushBot
PUSH_BOT_LASER_CONFIG_TOTAL_PERIOD = _munich_key(3, 0)
#: set laser params for PushBot
PUSH_BOT_LASER_CONFIG_ACTIVE_TIME = _munich_key(4, 0)
#: set laser params for PushBot
PUSH_BOT_LASER_FREQUENCY = _munich_key(37, 1)

#: set led params for PushBot
PUSH_BOT_LED_CONFIG_TOTAL_PERIOD = _munich_key(3, 4)
#: set led params for PushBot
PUSH_BOT_LED_BACK_CONFIG_ACTIVE_TIME = _munich_key(4, 4)
#: set led params for PushBot
PUSH_BOT_LED_FRONT_CONFIG_ACTIVE_TIME = _munich_key(4, 5)
#: set led params for PushBot
PUSH_BOT_LED_FREQUENCY = _munich_key(37, 0)

#: set speaker params for PushBot
PUSH_BOT_SPEAKER_CONFIG_TOTAL_PERIOD = _munich_key(3, 2)
#: set speaker params for PushBot
PUSH_BOT_SPEAKER_CONFIG_ACTIVE_TIME = _munich_key(4, 2)
#: set speaker params for PushBot
PUSH_BOT_SPEAKER_TONE_BEEP = _munich_key(36, 0)
#: set speaker params for PushBot
PUSH_BOT_SPEAKER_TONE_MELODY = _munich_key(36, 1)

#: PushBot motor control
PUSH_BOT_MOTOR_0_PERMANENT_VELOCITY = _munich_key(32, 0)
#: PushBot motor control
PUSH_BOT_MOTOR_1_PERMANENT_VELOCITY = _munich_key(32, 1)
#: PushBot motor control
PUSH_BOT_MOTOR_0_LEAKY_VELOCITY = _munich_key(32, 2)
#: PushBot motor control
PUSH_BOT_MOTOR_1_LEAKY_VELOCITY = _munich_key(32, 3)

# payload for master slave
_PAYLOAD_MASTER_SLAVE_USE_INTERNAL_COUNTER = 0
_PAYLOAD_MASTER_SLAVE_SET_SLAVE = 1
_PAYLOAD_MASTER_SLAVE_SET_MASTER_CLOCK_NOT_STARTED = 2
_PAYLOAD_MASTER_SLAVE_SET_MASTER_CLOCK_ACTIVE = 4


class RetinaKey(Enum):
    """
    The identification, pixels and bits per coordinate for each retina action.
    """
    FIXED_KEY = (0, 128, 7)
    NATIVE_128_X_128 = (1, 128, 7)
    DOWNSAMPLE_64_X_64 = (2, 64, 6)
    DOWNSAMPLE_32_X_32 = (3, 32, 5)
    DOWNSAMPLE_16_X_16 = (4, 16, 4)

    def __init__(self, ident: int, pixels: int, bits_per_coordinate: int):
        # pylint: disable=wrong-spelling-in-docstring
        """
        :param ident: The ID of the enum
        :param pixels: number of pixels per retina dimension
        :param bits_per_coordinate:  number of bits per retina dimension
        """
        self.__ident = ident << _PAYLOAD_RETINA_KEY_OFFSET
        self.__pixels = pixels
        self.__bits_per_coordinate = bits_per_coordinate

    @property
    def ident(self) -> int:
        # pylint: disable=wrong-spelling-in-docstring
        """
        The identification passed into the init.
        """
        return self.__ident

    @property
    def n_neurons(self) -> int:
        """
        The number of neurons passed into the init.
        """
        return 2 * (self.__pixels ** 2)

    @property
    def pixels(self) -> int:
        """
        The pixels passed into the init.
        """
        return self.__pixels

    @property
    def bits_per_coordinate(self) -> int:
        """
        The bits per coordinate passed into the init.
        """
        return self.__bits_per_coordinate


class RetinaPayload(Enum):
    """
    The indent and number of payload bytes for retina actions.
    """
    NO_PAYLOAD = (0, 0)
    EVENTS_IN_PAYLOAD = (0, 4)
    DELTA_TIMESTAMPS = (1, 4)
    ABSOLUTE_2_BYTE_TIMESTAMPS = (2, 2)
    ABSOLUTE_3_BYTE_TIMESTAMPS = (3, 3)
    ABSOLUTE_4_BYTE_TIMESTAMPS = (4, 4)

    def __init__(self, ident: int, n_payload_bytes: int):
        # pylint: disable=wrong-spelling-in-docstring
        """
        :param ident: ID for the enum
        :param n_payload_bytes: number of payload bytes for retina actions.
        """
        self.__ident = ident << _PAYLOAD_RETINA_PAYLOAD_OFFSET
        self.__n_payload_bytes = n_payload_bytes

    @property
    def ident(self) -> int:
        """
        The indent passed into the init.
        """
        return self.__ident

    @property
    def n_payload_bytes(self) -> int:
        """
        The n_payload_bytes passed into the init.
        """
        return self.__n_payload_bytes


class MUNICH_MODES(Enum):
    # pylint: disable=invalid-name
    """
    Types of modes supported by this protocol.
    """
    RESET_TO_DEFAULT = 0
    PUSH_BOT = 1
    SPOMNIBOT = 2
    BALL_BALANCER = 3
    MY_ORO_BOTICS = 4
    FREE = 5


class MunichIoSpiNNakerLinkProtocol(object):
    """
    Provides Multicast commands for the Munich SpiNNaker-Link protocol.
    """
    __slots__ = (
        "__instance_key",
        "__mode",
        "__uart_id")

    # The instance of the protocol in use, to ensure that each vertex that is
    # to send commands to the PushBot uses a different outgoing key; the top
    # part of the key is ignored, so this works out!
    _protocol_instance = 0

    # Keeps track of whether the mode has been configured already
    __sent_mode_command = False

    def __init__(self, mode: MUNICH_MODES, instance_key: Optional[int] = None,
                 uart_id: int = 0):
        """
        :param mode: The mode of operation of the protocol
        :param instance_key: The optional instance key to use
        :param uart_id: The ID of the UART when needed
        """
        self.__mode = mode

        # Create a key for this instance of the protocol
        # - see above for reasoning
        if instance_key is None:
            self.__instance_key = (
                MunichIoSpiNNakerLinkProtocol._protocol_instance <<
                _OFFSET_TO_IGNORED_KEY)
            MunichIoSpiNNakerLinkProtocol._protocol_instance += 1
        else:
            self.__instance_key = instance_key

        self.__uart_id = uart_id

    @property
    def mode(self) -> MUNICH_MODES:
        """
        spynnaker.pyNN.protocols.MUNICH_MODES
        """
        return self.__mode

    @property
    def uart_id(self) -> int:
        """
        The ID of the UART when needed
        """
        return self.__uart_id

    @property
    def instance_key(self) -> int:
        """
        The instance key to use
        """
        return self.__instance_key

    @staticmethod
    def sent_mode_command() -> bool:
        """
        :returns:
           True if the mode command has ever been requested by any instance.
        """
        return MunichIoSpiNNakerLinkProtocol.__sent_mode_command

    def _get_key(self, command: int,
                 offset_to_uart_id: Optional[int] = None) -> int:
        if offset_to_uart_id is None:
            return command | self.__instance_key
        return (
            command | self.__instance_key |
            (self.__uart_id << offset_to_uart_id))

    def configure_master_key(self, new_key: int,
                             time: Optional[int] = None) -> MultiCastCommand:
        """
        :param new_key:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to configure master key.
        """
        return MultiCastCommand(
            self._get_key(CONFIGURE_MASTER_KEY), payload=new_key, time=time)

    def set_mode(self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: The set mode. And records it was provided.
        """
        MunichIoSpiNNakerLinkProtocol.__sent_mode_command = True
        return MultiCastCommand(
            self._get_key(CHANGE_MODE), payload=self.__mode.value, time=time)

    @property
    def set_retina_key_key(self) -> int:
        """
        Key to set retina key.
        """
        return self._get_key(
            ACTIVE_RETINA_EVENT_STREAMING_SET_KEY, RETINA_UART_SHIFT)

    def set_retina_key(self, new_key: int,
                       time: Optional[int] = None) -> MultiCastCommand:
        """
        :param new_key:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set retina key.
        """
        return MultiCastCommand(
            self.set_retina_key_key, payload=new_key, time=time)

    @property
    def disable_retina_key(self) -> int:
        """
        Key to disable the retina.
        """
        return self._get_key(DISABLE_RETINA_EVENT_STREAMING, RETINA_UART_SHIFT)

    def disable_retina(self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to disable retina.
        """
        return MultiCastCommand(self.disable_retina_key, time=time)

    def master_slave_use_internal_counter(
            self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set internal counter used.
        """
        return MultiCastCommand(
            self._get_key(MASTER_SLAVE_KEY, RETINA_UART_SHIFT),
            payload=_PAYLOAD_MASTER_SLAVE_USE_INTERNAL_COUNTER, time=time)

    def master_slave_set_slave(
            self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set slave.
        """
        return MultiCastCommand(
            self._get_key(MASTER_SLAVE_KEY, RETINA_UART_SHIFT),
            payload=_PAYLOAD_MASTER_SLAVE_SET_SLAVE, time=time)

    def master_slave_set_master_clock_not_started(
            self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set master clock active.
        """
        return MultiCastCommand(
            self._get_key(MASTER_SLAVE_KEY, RETINA_UART_SHIFT),
            payload=_PAYLOAD_MASTER_SLAVE_SET_MASTER_CLOCK_NOT_STARTED,
            time=time)

    def master_slave_set_master_clock_active(
            self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set master clock active.
        """
        return MultiCastCommand(
            self._get_key(MASTER_SLAVE_KEY, RETINA_UART_SHIFT),
            payload=_PAYLOAD_MASTER_SLAVE_SET_MASTER_CLOCK_ACTIVE,
            time=time)

    def bias_values(self, bias_id: int, bias_value: int,
                    time: Optional[int] = None) -> MultiCastCommand:
        """
        :param bias_id:
        :param bias_value:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to bias level.
        """
        return MultiCastCommand(
            self._get_key(BIAS_KEY, RETINA_UART_SHIFT),
            payload=((bias_id << 0) | (bias_value << 8)), time=time)

    def reset_retina(self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to reset retina.
        """
        return MultiCastCommand(
            self._get_key(RESET_RETINA_KEY, RETINA_UART_SHIFT), time=time)

    def turn_off_sensor_reporting(
            self, sensor_id: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param sensor_id:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to turn off sensor reporting.
        """
        return MultiCastCommand(
            self._get_key(SENSOR_REPORTING_OFF_KEY),
            payload=(sensor_id << _PAYLOAD_SENSOR_ID_OFFSET), time=time)

    def poll_sensors_once(self, sensor_id: int,
                          time: Optional[int] = None) -> MultiCastCommand:
        """
        :param sensor_id:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to poll sensor once.
        """
        return MultiCastCommand(
            self._get_key(POLL_SENSORS_ONCE_KEY),
            payload=(sensor_id << _PAYLOAD_SENSOR_ID_OFFSET), time=time)

    def poll_individual_sensor_continuously(
            self, sensor_id: int, time_in_ms: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param sensor_id:
        :param time_in_ms: time to sensor
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to sensor continuously.
        """
        return MultiCastCommand(
            self._get_key(POLL_SENSORS_CONTINUOUSLY_KEY),
            payload=((sensor_id << _PAYLOAD_SENSOR_ID_OFFSET) |
                     (time_in_ms << _PAYLOAD_OFFSET_FOR_SENSOR_TIME)),
            time=time)

    @property
    def enable_disable_motor_key(self) -> int:
        """
        Get key to disable motor.
        """
        return self._get_key(ENABLE_DISABLE_MOTOR_KEY, RETINA_UART_SHIFT)

    def generic_motor_enable(
            self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to enable motor.
        """
        return MultiCastCommand(
            self.enable_disable_motor_key, payload=1, time=time)

    def generic_motor_disable(
            self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to disable motor.
        """
        return MultiCastCommand(
            self.enable_disable_motor_key, payload=0, time=time)

    def generic_motor_total_period(
            self, time_in_ms: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time_in_ms:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set motor total period.
        """
        return MultiCastCommand(
            self._get_key(MOTOR_RUN_FOR_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=time_in_ms, time=time)

    def generic_motor0_raw_output_permanent(
            self, pwm_signal: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param pwm_signal:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set generic motor 0 raw output permanent.
        """
        return MultiCastCommand(
            self._get_key(MOTOR_0_RAW_PERM_KEY, RETINA_UART_SHIFT),
            payload=pwm_signal, time=time)

    def generic_motor1_raw_output_permanent(
            self, pwm_signal: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param pwm_signal:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set generic motor 1 raw output permanent.
        """
        return MultiCastCommand(
            self._get_key(MOTOR_1_RAW_PERM_KEY, RETINA_UART_SHIFT),
            payload=pwm_signal, time=time)

    def generic_motor0_raw_output_leak_to_0(
            self, pwm_signal: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param pwm_signal:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set generic motor 0 raw output leak to 0.
        """
        return MultiCastCommand(
            self._get_key(MOTOR_0_RAW_LEAK_KEY, RETINA_UART_SHIFT),
            payload=pwm_signal, time=time)

    def generic_motor1_raw_output_leak_to_0(
            self, pwm_signal: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param pwm_signal:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set generic motor 1 raw output leak to 0.
        """
        return MultiCastCommand(
            self._get_key(MOTOR_1_RAW_LEAK_KEY, RETINA_UART_SHIFT),
            payload=pwm_signal, time=time)

    def pwm_pin_output_timer_a_duration(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set a output timer duration.
        """
        return MultiCastCommand(
            self._get_key(MOTOR_TIMER_A_TOTAL_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def pwm_pin_output_timer_b_duration(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set b output timer duration.
        """
        return MultiCastCommand(
            self._get_key(MOTOR_TIMER_B_TOTAL_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def pwm_pin_output_timer_c_duration(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set c output timer duration.
        """
        return MultiCastCommand(
            self._get_key(MOTOR_TIMER_C_TOTAL_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def pwm_pin_output_timer_a_channel_0_ratio(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set a channel 0 output timer.
        """
        return MultiCastCommand(
            self._get_key(
                MOTOR_TIMER_A_CHANNEL_0_ACTIVE_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def pwm_pin_output_timer_a_channel_1_ratio(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set a channel 1 output timer.
        """
        return MultiCastCommand(
            self._get_key(
                MOTOR_TIMER_A_CHANNEL_1_ACTIVE_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def pwm_pin_output_timer_b_channel_0_ratio(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set b channel 0 output timer.

        """
        return MultiCastCommand(
            self._get_key(
                MOTOR_TIMER_B_CHANNEL_0_ACTIVE_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def pwm_pin_output_timer_b_channel_1_ratio(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set b channel 1 output timer.
        """
        return MultiCastCommand(
            self._get_key(
                MOTOR_TIMER_B_CHANNEL_1_ACTIVE_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def pwm_pin_output_timer_c_channel_0_ratio(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set c channel 0 output timer.
        """
        return MultiCastCommand(
            self._get_key(
                MOTOR_TIMER_C_CHANNEL_0_ACTIVE_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def pwm_pin_output_timer_c_channel_1_ratio(
            self, timer_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param timer_period:
        :returns: Command to set c channel 1 output timer.
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        """
        return MultiCastCommand(
            self._get_key(
                MOTOR_TIMER_C_CHANNEL_1_ACTIVE_PERIOD_KEY, RETINA_UART_SHIFT),
            payload=timer_period, time=time)

    def query_state_of_io_lines(
            self, time: Optional[int] = None) -> MultiCastCommand:
        """
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to query state of io lines.
        """
        return MultiCastCommand(
            self._get_key(QUERY_STATES_LINES_KEY), time=time)

    def set_output_pattern_for_payload(
            self, payload: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param payload:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set output pattern for payload.
        """
        return MultiCastCommand(
            self._get_key(SET_OUTPUT_PATTERN_KEY), payload=payload, time=time)

    def add_payload_logic_to_current_output(
            self, payload: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param payload:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to add payload logic to current output.
        """
        return MultiCastCommand(
            self._get_key(ADD_PAYLOAD_TO_CURRENT_OUTPUT_KEY),
            payload=payload, time=time)

    def remove_payload_logic_to_current_output(
            self, payload: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param payload:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to remove payload logic to current output.
        """
        return MultiCastCommand(
            self._get_key(REMOVE_PAYLOAD_TO_CURRENT_OUTPUT_KEY),
            payload=payload, time=time)

    def set_payload_pins_to_high_impedance(
            self, payload: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param payload:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the payload pins to high impedance.
        """
        return MultiCastCommand(
            self._get_key(SET_PAYLOAD_TO_HIGH_IMPEDANCE_KEY),
            payload=payload, time=time)

    def _check_for_pushbot_mode(self) -> None:
        if self.__mode is not MUNICH_MODES.PUSH_BOT:
            raise ConfigurationException(
                "The mode you configured is not the PushBot, and so this "
                f"message is invalid for mode {self.__mode}")

    @property
    def push_bot_laser_config_total_period_key(self) -> int:
        """
        The key to set the laser total period.
        """
        return self._get_key(
            PUSH_BOT_LASER_CONFIG_TOTAL_PERIOD, RETINA_UART_SHIFT)

    def push_bot_laser_config_total_period(
            self, total_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param total_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the laser total period.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_laser_config_total_period_key,
            payload=total_period, time=time)

    @property
    def push_bot_laser_config_active_time_key(self) -> int:
        """
        The key to set the laser active time.
        """
        return self._get_key(
            PUSH_BOT_LASER_CONFIG_ACTIVE_TIME, RETINA_UART_SHIFT)

    def push_bot_laser_config_active_time(
            self, active_time: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param active_time: The time for the laser
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the laser active time.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_laser_config_active_time_key,
            payload=active_time, time=time)

    @property
    def push_bot_laser_set_frequency_key(self) -> int:
        """
        The key to set the frequency.
        """
        return self._get_key(
            PUSH_BOT_LASER_FREQUENCY,
            PUSH_BOT_LASER_LED_SPEAKER_FREQUENCY_UART_SHIFT)

    def push_bot_laser_set_frequency(
            self, frequency: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param frequency:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the laser frequency.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_laser_set_frequency_key,
            payload=frequency, time=time)

    @property
    def push_bot_speaker_config_total_period_key(self) -> int:
        """
        The key to set the speaker total period.
        """
        return self._get_key(
            PUSH_BOT_SPEAKER_CONFIG_TOTAL_PERIOD, RETINA_UART_SHIFT)

    def push_bot_speaker_config_total_period(
            self, total_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param total_period:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the speaker total period.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_speaker_config_total_period_key,
            payload=total_period, time=time)

    @property
    def push_bot_speaker_config_active_time_key(self) -> int:
        """
        The key to set the speaker active time.
        """
        return self._get_key(
            PUSH_BOT_SPEAKER_CONFIG_ACTIVE_TIME, RETINA_UART_SHIFT)

    def push_bot_speaker_config_active_time(
            self, active_time: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param active_time:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the speaker active time.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_speaker_config_active_time_key,
            payload=active_time, time=time)

    @property
    def push_bot_speaker_set_tone_key(self) -> int:
        """
        The key to set the tone.
        """
        return self._get_key(
            PUSH_BOT_SPEAKER_TONE_BEEP,
            PUSH_BOT_LASER_LED_SPEAKER_FREQUENCY_UART_SHIFT)

    def push_bot_speaker_set_tone(
            self, frequency: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param frequency:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the tone.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_speaker_set_tone_key,
            payload=frequency, time=time)

    @property
    def push_bot_speaker_set_melody_key(self) -> int:
        """
        The key to set the melody.
        """
        return self._get_key(
            PUSH_BOT_SPEAKER_TONE_MELODY,
            PUSH_BOT_LASER_LED_SPEAKER_FREQUENCY_UART_SHIFT)

    def push_bot_speaker_set_melody(
            self, melody: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param melody:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the melody.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_speaker_set_melody_key,
            payload=melody, time=time)

    @property
    def push_bot_led_total_period_key(self) -> int:
        """
        The key to set the total led period.
        """
        return self._get_key(
            PUSH_BOT_LED_CONFIG_TOTAL_PERIOD, RETINA_UART_SHIFT)

    def push_bot_led_total_period(
            self, total_period: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param total_period: total period for the LED
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the total led period.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_led_total_period_key,
            payload=total_period, time=time)

    @property
    def push_bot_led_back_active_time_key(self) -> int:
        """
        The key to set the back led active time.
        """
        return self._get_key(
            PUSH_BOT_LED_BACK_CONFIG_ACTIVE_TIME, RETINA_UART_SHIFT)

    def push_bot_led_back_active_time(
            self, active_time: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param active_time:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the back led active time.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_led_back_active_time_key,
            payload=active_time, time=time)

    @property
    def push_bot_led_front_active_time_key(self) -> int:
        """
        The key to set the front led active time.
        """
        return self._get_key(
            PUSH_BOT_LED_FRONT_CONFIG_ACTIVE_TIME, RETINA_UART_SHIFT)

    def push_bot_led_front_active_time(
            self, active_time: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param active_time:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the front led active time.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_led_front_active_time_key,
            payload=active_time, time=time)

    @property
    def push_bot_led_set_frequency_key(self) -> int:
        """
        The key to set the led frequency.
        """
        return self._get_key(
            PUSH_BOT_LED_FREQUENCY,
            PUSH_BOT_LASER_LED_SPEAKER_FREQUENCY_UART_SHIFT)

    def push_bot_led_set_frequency(
            self, frequency: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param frequency:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to set the led frequency.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_led_set_frequency_key,
            payload=frequency, time=time)

    @property
    def push_bot_motor_0_permanent_key(self) -> int:
        """
        The key for the change motor 0 permanently.
        """
        return self._get_key(
            PUSH_BOT_MOTOR_0_PERMANENT_VELOCITY, PUSH_BOT_MOTOR_UART_SHIFT)

    def push_bot_motor_0_permanent(
            self, velocity: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param velocity:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to change motor 0 permanently.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_motor_0_permanent_key,
            payload=velocity, time=time)

    @property
    def push_bot_motor_1_permanent_key(self) -> int:
        """
        The key for the change motor 1 permanently.
        """
        return self._get_key(
            PUSH_BOT_MOTOR_1_PERMANENT_VELOCITY, PUSH_BOT_MOTOR_UART_SHIFT)

    def push_bot_motor_1_permanent(
            self, velocity: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param velocity:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to change motor 1 permanently.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_motor_1_permanent_key,
            payload=velocity, time=time)

    @property
    def push_bot_motor_0_leaking_towards_zero_key(self) -> int:
        """
        The key for the change motor 0 towards zero.
        """
        return self._get_key(
            PUSH_BOT_MOTOR_0_LEAKY_VELOCITY, PUSH_BOT_MOTOR_UART_SHIFT)

    def push_bot_motor_0_leaking_towards_zero(
            self, velocity: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param velocity:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to change motor 0 towards zero.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_motor_0_leaking_towards_zero_key,
            payload=velocity, time=time)

    @property
    def push_bot_motor_1_leaking_towards_zero_key(self) -> int:
        """
        The key for the change motor 1 towards zero.
        """
        return self._get_key(
            PUSH_BOT_MOTOR_1_LEAKY_VELOCITY, PUSH_BOT_MOTOR_UART_SHIFT)

    def push_bot_motor_1_leaking_towards_zero(
            self, velocity: int,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        :param velocity:
        :param time: The time within the simulation at which to send the
            command, or ``None`` if this is not a timed command
        :returns: Command to change motor 1 towards zero.
        :raises ConfigurationException: If the mode is not PUSH_BOT
        """
        self._check_for_pushbot_mode()
        return MultiCastCommand(
            self.push_bot_motor_1_leaking_towards_zero_key,
            payload=velocity, time=time)

    def sensor_transmission_key(self, sensor_id: int) -> int:
        """
        :param sensor_id:
        :returns: The transmission key to this sensor id.
        """
        return ((sensor_id << _SENSOR_OUTGOING_OFFSET_TO_D) |
                (self.__uart_id << _SENSOR_OUTGOING_OFFSET_TO_I))

    @property
    def set_retina_transmission_key(self) -> int:
        """
        The key to set the retina_transmission.
        """
        return self._get_key(
            ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION,
            RETINA_UART_SHIFT)

    def set_retina_transmission(
            self, retina_key: Optional[RetinaKey] = RetinaKey.NATIVE_128_X_128,
            retina_payload: Optional[RetinaPayload] = None,
            time: Optional[int] = None) -> MultiCastCommand:
        """
        Set the retina transmission key.

        :param retina_key: the new key for the retina
        :param retina_payload:
            the new payload for the set retina key command packet
        :param time: when to transmit this packet
        :return: the command to send
        """
        retina_key_id = retina_key.ident if retina_key is not None else 0

        if retina_payload is None:
            if retina_key == RetinaKey.FIXED_KEY:
                retina_payload = RetinaPayload.EVENTS_IN_PAYLOAD
            else:
                retina_payload = RetinaPayload.NO_PAYLOAD

        if (retina_key == RetinaKey.FIXED_KEY and
                retina_payload != RetinaPayload.EVENTS_IN_PAYLOAD):
            raise ConfigurationException(
                "If the Retina Key is FIXED_KEY, the payload must be"
                " EVENTS_IN_PAYLOAD")

        return MultiCastCommand(
            self.set_retina_transmission_key,
            payload=retina_key_id | retina_payload.ident,
            time=time)
