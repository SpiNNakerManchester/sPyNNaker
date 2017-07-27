// structure of multicast key of command is KKKKKKKKKKKKKKKKKKKKK-IIIIIII-F-DDD
// K is ignored "instance key"
// I is instruction
// F is payload format
// D is device
#include <debug.h>
#include <stdint.h>

#define _OFFSET_TO_I 4
#define _OFFSET_TO_F 3
#define _OFFSET_TO_D 0

// Specific fields in the key
#define _OFFSET_FOR_UART_ID 29
#define _PUSH_BOT_UART_OFFSET_SPEAKER_LED_LASER 1

#define MUNICH_KEY(I, F, D) \
    ((I << _OFFSET_TO_I) | (F << _OFFSET_TO_F) | (D << _OFFSET_TO_D))
#define MUNICH_KEY_I_D(I, D) MUNICH_KEY(I, 0, D)
#define MUNICH_KEY_I(I) MUNICH_KEY(I, 0, 0)

// Payload fields
#define _PAYLOAD_OFFSET_FOR_TIMESTAMPS 29
#define _PAYLOAD_OFFSET_FOR_RETINA_SIZE 26
#define _PAYLOAD_SENSOR_ID_OFFSET 27
#define _PAYLOAD_OFFSET_FOR_SENSOR_TIME 31

// command key for setting up the master key of the board
#define _CONFIGURE_MASTER_KEY MUNICH_KEY_I(127)

// command key for setting up what mode of device running on the board
#define _CHANGE_MODE MUNICH_KEY_I_D(127, 1)

// command for turning off retina output
#define _DISABLE_RETINA_EVENT_STREAMING MUNICH_KEY_I_D(0, 0)

// command for retina where payload is events
#define _ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION MUNICH_KEY_I_D(0, 1)

// command for retina where events are the key
#define _ACTIVE_RETINA_EVENT_STREAMING_SET_KEY MUNICH_KEY_I_D(0, 2)

// set timer / counter for timestamps
#define _SET_TIMER_COUNTER_FOR_TIMESTAMPS MUNICH_KEY_I_D(0, 3)

// handle master / slave time sync
#define _MASTER_SLAVE_KEY MUNICH_KEY_I_D(0, 4)

// command for setting bias
#define _BIAS_KEY MUNICH_KEY_I_D(0, 5)

// reset retina key.
#define _RESET_RETINA_KEY MUNICH_KEY_I_D(0, 7)

// request on-board sensor data
#define _SENSOR_REPORTING_OFF_KEY MUNICH_KEY_I_D(1, 0)

// poll sensors once
#define _POLL_SENSORS_ONCE_KEY MUNICH_KEY_I_D(1, 1)

// poll sensors continuously
#define _POLL_SENSORS_CONTINUOUSLY_KEY MUNICH_KEY_I_D(1, 2)

// disable motor
#define _DISABLE_MOTOR_KEY MUNICH_KEY_I_D(2, 0)

// run motor for total period
#define _MOTOR_RUN_FOR_PERIOD_KEY MUNICH_KEY_I_D(2, 1)

// raw output for motor 0 (permanent)
#define _MOTOR_0_RAW_PERM_KEY MUNICH_KEY_I_D(2, 4)

// raw output for motor 1 (permanent)
#define _MOTOR_1_RAW_PERM_KEY MUNICH_KEY_I_D(2, 5)

// raw output for motor 0 (leak towards 0)
#define _MOTOR_0_RAW_LEAK_KEY MUNICH_KEY_I_D(2, 6)

// raw output for motor 1 (leak towards 0)
#define _MOTOR_1_RAW_LEAK_KEY MUNICH_KEY_I_D(2, 7)

// motor output duration timer period
#define _MOTOR_TIMER_A_TOTAL_PERIOD_KEY MUNICH_KEY_I_D(3, 0)
#define _MOTOR_TIMER_B_TOTAL_PERIOD_KEY MUNICH_KEY_I_D(3, 2)
#define _MOTOR_TIMER_C_TOTAL_PERIOD_KEY MUNICH_KEY_I_D(3, 4)

// motor output ratio active period
#define _MOTOR_TIMER_A_CHANNEL_0_ACTIVE_PERIOD_KEY MUNICH_KEY_I_D(4, 0)
#define _MOTOR_TIMER_A_CHANNEL_1_ACTIVE_PERIOD_KEY MUNICH_KEY_I_D(4, 1)
#define _MOTOR_TIMER_B_CHANNEL_0_ACTIVE_PERIOD_KEY MUNICH_KEY_I_D(4, 2)
#define _MOTOR_TIMER_B_CHANNEL_1_ACTIVE_PERIOD_KEY MUNICH_KEY_I_D(4, 3)
#define _MOTOR_TIMER_C_CHANNEL_0_ACTIVE_PERIOD_KEY MUNICH_KEY_I_D(4, 4)
#define _MOTOR_TIMER_C_CHANNEL_1_ACTIVE_PERIOD_KEY MUNICH_KEY_I_D(4, 5)

// digital IO Signals
#define _QUERY_STATES_LINES_KEY MUNICH_KEY_I_D(5, 0)

// set output pattern to payload
#define _SET_OUTPUT_PATTERN_KEY MUNICH_KEY_I_D(5, 1)

// add payload (logic or (PL)) to current output
#define _ADD_PAYLOAD_TO_CURRENT_OUTPUT_KEY MUNICH_KEY_I_D(5, 2)

// remove payload (logic or (PL)) to current output from current output
#define _REMOVE_PAYLOAD_TO_CURRENT_OUTPUT_KEY MUNICH_KEY_I_D(5, 3)

// set payload pins to high impedance
#define _SET_PAYLOAD_TO_HIGH_IMPEDANCE_KEY MUNICH_KEY_I_D(5, 4)

// set laser params for pushbot
#define _PUSH_BOT_LASER_CONFIG_TOTAL_PERIOD MUNICH_KEY_I_D(4, 0)
#define _PUSH_BOT_LASER_CONFIG_ACTIVE_TIME  MUNICH_KEY_I_D(5, 0)
#define _PUSH_BOT_LASER_FREQUENCY           MUNICH_KEY_I_D(37, 1)

// set led params for pushbot
#define _PUSH_BOT_LED_CONFIG_TOTAL_PERIOD      MUNICH_KEY_I_D(4, 4)
#define _PUSH_BOT_LED_BACK_CONFIG_ACTIVE_TIME  MUNICH_KEY_I_D(5, 4)
#define _PUSH_BOT_LED_FRONT_CONFIG_ACTIVE_TIME MUNICH_KEY_I_D(5, 5)
#define _PUSH_BOT_LED_FREQUENCY                MUNICH_KEY_I_D(37, 0)

// set speaker params for pushbot
#define _PUSH_BOT_SPEAKER_CONFIG_TOTAL_PERIOD MUNICH_KEY_I_D(4, 2)
#define _PUSH_BOT_SPEAKER_CONFIG_ACTIVE_TIME  MUNICH_KEY_I_D(5, 2)
#define _PUSH_BOT_SPEAKER_TONE_BEEP           MUNICH_KEY_I_D(36, 0)
#define _PUSH_BOT_SPEAKER_TONE_MELODY         MUNICH_KEY_I_D(36, 1)

// pushbot motor control
#define _PUSH_BOT_MOTOR_0_PERMANENT_VELOCITY MUNICH_KEY_I_D(32, 0)
#define _PUSH_BOT_MOTOR_1_PERMANENT_VELOCITY MUNICH_KEY_I_D(32, 1)
#define _PUSH_BOT_MOTOR_0_LEAKY_VELOCITY     MUNICH_KEY_I_D(32, 2)
#define _PUSH_BOT_MOTOR_1_LEAKY_VELOCITY     MUNICH_KEY_I_D(32, 3)

// payload for setting different time stamp sizes
#define _PAYLOAD_NO_TIMESTAMPS (0 << _PAYLOAD_OFFSET_FOR_TIMESTAMPS)
#define _PAYLOAD_DELTA_TIMESTAMPS (1 << _PAYLOAD_OFFSET_FOR_TIMESTAMPS)
#define _PAYLOAD_TWO_BYTE_TIME_STAMPS (2 << _PAYLOAD_OFFSET_FOR_TIMESTAMPS)
#define _PAYLOAD_THREE_BYTE_TIME_STAMPS (3 << _PAYLOAD_OFFSET_FOR_TIMESTAMPS)
#define _PAYLOAD_FOUR_BYTE_TIME_STAMPS (4 << _PAYLOAD_OFFSET_FOR_TIMESTAMPS)

// payload for retina size
#define _PAYLOAD_RETINA_NO_DOWN_SAMPLING_IN_PAYLOAD \
    (0 << _PAYLOAD_OFFSET_FOR_RETINA_SIZE)
#define _PAYLOAD_RETINA_NO_DOWN_SAMPLING (1 << _PAYLOAD_OFFSET_FOR_RETINA_SIZE)
#define _PAYLOAD_RETINA_64_DOWN_SAMPLING (2 << _PAYLOAD_OFFSET_FOR_RETINA_SIZE)
#define _PAYLOAD_RETINA_32_DOWN_SAMPLING (3 << _PAYLOAD_OFFSET_FOR_RETINA_SIZE)
#define _PAYLOAD_RETINA_16_DOWN_SAMPLING (4 << _PAYLOAD_OFFSET_FOR_RETINA_SIZE)

// payload for master slave
#define _PAYLOAD_MASTER_SLAVE_USE_INTERNAL_COUNTER 0
#define _PAYLOAD_MASTER_SLAVE_SET_SLAVE 1
#define _PAYLOAD_MASTER_SLAVE_SET_MASTER_CLOCK_NOT_STARTED 2
#define _PAYLOAD_MASTER_SLAVE_SET_MASTER_CLOCK_ACTIVE 4

//! human readable definitions of each mode
typedef enum modes_e {
    MUNICH_PROTOCOL_RESET_TO_DEFAULT = 0,
    MUNICH_PROTOCOL_PUSH_BOT = 1,
    MUNICH_PROTOCOL_SPOMNIBOT = 2,
    MUNICH_PROTOCOL_BALL_BALANCER = 3,
    MUNICH_PROTOCOL_MY_ORO_BOTICS = 4,
    MUNICH_PROTOCOL_FREE = 5
} munich_protocol_modes_e;

typedef struct multicast_packet {
    uint32_t key;
    uint32_t payload;
    uint32_t payload_flag;
} multicast_packet;

//! The current mode
munich_protocol_modes_e _mode = NULL;

//! The value of the ignored part of the key - note this is pre-shifted into
//! position so can simply be or'd
uint32_t _instance_key = NULL;

static inline void set_protocol_mode(
        munich_protocol_modes_e mode, uint32_t instance_key) {
    _mode = mode;
    _instance_key = instance_key;
}

static inline multicast_packet munich_protocol_get_configure_master_key_command(
        uint32_t new_key) {
    return (multicast_packet) {
        .key = _CONFIGURE_MASTER_KEY | _instance_key,
        .payload = new_key,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_get_set_mode_command() {
    return (multicast_packet) {
        .key = _CHANGE_MODE | _instance_key,
        .payload = (uint32_t) _mode,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_set_retina_transmission_key(
        uint32_t new_key, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_ACTIVE_RETINA_EVENT_STREAMING_SET_KEY |
                (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = new_key,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_disable_retina_event_streaming(
        uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_DISABLE_RETINA_EVENT_STREAMING |
                (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = 0,
        .payload_flag = NO_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_master_slave_use_internal_counter(uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MASTER_SLAVE_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
                _instance_key),
        .payload = _PAYLOAD_MASTER_SLAVE_USE_INTERNAL_COUNTER,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_master_slave_set_slave(
        uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MASTER_SLAVE_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
                _instance_key),
        .payload = _PAYLOAD_MASTER_SLAVE_SET_SLAVE,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_master_slave_set_master_clock_not_started(uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MASTER_SLAVE_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
                _instance_key),
        .payload = _PAYLOAD_MASTER_SLAVE_SET_MASTER_CLOCK_NOT_STARTED,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
    munich_protocol_master_slave_set_master_clock_active(
        uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MASTER_SLAVE_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
                _instance_key),
        .payload = _PAYLOAD_MASTER_SLAVE_SET_MASTER_CLOCK_ACTIVE,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_bias_values(
        uint32_t bias_id, uint32_t bias_value, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MASTER_SLAVE_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
                _instance_key),
        .payload = ((bias_id << 0) | (bias_value << 8)),
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_reset_retina(uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_RESET_RETINA_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
                _instance_key),
        .payload = 0,
        .payload_flag = NO_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_turn_off_sensor_reporting(
        uint32_t sensor_id) {
    return (multicast_packet) {
        .key = _SENSOR_REPORTING_OFF_KEY | _instance_key,
        .payload = (sensor_id << _PAYLOAD_SENSOR_ID_OFFSET),
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_poll_sensors_once(
        uint32_t sensor_id) {
    return (multicast_packet) {
        .key = _POLL_SENSORS_ONCE_KEY | _instance_key,
        .payload = (sensor_id << _PAYLOAD_SENSOR_ID_OFFSET),
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_poll_individual_sensor_continuously(
        uint32_t sensor_id, uint32_t time_in_ms) {
    return (multicast_packet) {
        .key = _POLL_SENSORS_CONTINUOUSLY_KEY | _instance_key,
        .payload = ((sensor_id << _PAYLOAD_SENSOR_ID_OFFSET) |
                      (time_in_ms << _PAYLOAD_OFFSET_FOR_SENSOR_TIME)),
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_generic_motor_enable_disable(
        uint32_t enable_disable, uint32_t uart_id) {
    return (multicast_packet) {
        .key = _DISABLE_MOTOR_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
               _instance_key,
        .payload = enable_disable,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_generic_motor_total_period_duration(
        uint32_t time_in_ms, uint32_t uart_id) {
    return (multicast_packet) {
        .key = _MOTOR_RUN_FOR_PERIOD_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
               _instance_key,
        .payload = time_in_ms,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_generic_motor0_raw_output_permanent(
        uint32_t pwm_signal, uint32_t uart_id) {
    return (multicast_packet) {
        .key = _MOTOR_0_RAW_PERM_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
               _instance_key,
        .payload = pwm_signal,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_generic_motor1_raw_output_permanent(
        uint32_t pwm_signal, uint32_t uart_id) {
    return (multicast_packet) {
        .key = _MOTOR_1_RAW_PERM_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
               _instance_key,
        .payload = pwm_signal,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_generic_motor0_raw_output_leak_to_0(
        uint32_t pwm_signal, uint32_t uart_id) {
    return (multicast_packet) {
        .key = _MOTOR_0_RAW_LEAK_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
               _instance_key,
        .payload = pwm_signal,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_generic_motor1_raw_output_leak_to_0(
        uint32_t pwm_signal, uint32_t uart_id) {
    return (multicast_packet) {
        .key = _MOTOR_1_RAW_LEAK_KEY | (uart_id << _OFFSET_FOR_UART_ID) |
               _instance_key,
        .payload = pwm_signal,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_pwm_pin_output_timer_a_duration(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_A_TOTAL_PERIOD_KEY |
                  (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_pwm_pin_output_timer_b_duration(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_B_TOTAL_PERIOD_KEY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_pwm_pin_output_timer_c_duration(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_C_TOTAL_PERIOD_KEY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_pwm_pin_output_timer_a_channel_0_ratio(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_A_CHANNEL_0_ACTIVE_PERIOD_KEY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_pwm_pin_output_timer_a_channel_1_ratio(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_A_CHANNEL_1_ACTIVE_PERIOD_KEY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_pwm_pin_output_timer_b_channel_0_ratio(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_B_CHANNEL_0_ACTIVE_PERIOD_KEY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_pwm_pin_output_timer_b_channel_1_ratio(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_B_CHANNEL_1_ACTIVE_PERIOD_KEY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_pwm_pin_output_timer_c_channel_0_ratio(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_C_CHANNEL_0_ACTIVE_PERIOD_KEY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_pwm_pin_output_timer_c_channel_1_ratio(
        uint32_t timer_period, uint32_t uart_id) {
    return (multicast_packet) {
        .key = (_MOTOR_TIMER_C_CHANNEL_1_ACTIVE_PERIOD_KEY  |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = timer_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_query_state_of_io_lines() {
    return (multicast_packet) {
        .key = _QUERY_STATES_LINES_KEY | _instance_key,
        .payload = 0,
        .payload_flag = NO_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_set_output_pattern_for_payload(
        uint32_t payload) {
    return (multicast_packet) {
        .key = _SET_OUTPUT_PATTERN_KEY | _instance_key,
        .payload = payload,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
    munich_protocol_add_payload_logic_to_current_output(
        uint32_t payload) {
    return (multicast_packet) {
        .key = _ADD_PAYLOAD_TO_CURRENT_OUTPUT_KEY | _instance_key,
        .payload = payload,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
    munich_protocol_remove_payload_logic_to_current_output(
        uint32_t payload) {
    return (multicast_packet) {
        .key = _REMOVE_PAYLOAD_TO_CURRENT_OUTPUT_KEY | _instance_key,
        .payload = payload,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_set_payload_pins_to_high_impedance(uint32_t payload) {
    return (multicast_packet) {
        .key = _SET_PAYLOAD_TO_HIGH_IMPEDANCE_KEY | _instance_key,
        .payload = payload,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_push_bot_laser_config_total_period(
        uint32_t total_period, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_LASER_CONFIG_TOTAL_PERIOD |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = total_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_push_bot_laser_config_active_time(
        uint32_t active_time, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_LASER_CONFIG_ACTIVE_TIME |
                  (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = active_time,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_laser_set_frequency(
        uint32_t frequency, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_LASER_FREQUENCY | _instance_key |
                 (uart_id << _PUSH_BOT_UART_OFFSET_SPEAKER_LED_LASER)),
        .payload = frequency,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_push_bot_speaker_config_total_period(
        uint32_t total_period, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_SPEAKER_CONFIG_TOTAL_PERIOD |
                (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = total_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_push_bot_speaker_config_active_time(
        uint32_t active_time, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_SPEAKER_CONFIG_ACTIVE_TIME |
                (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = active_time,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_speaker_set_tone(
        uint32_t frequency, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_SPEAKER_TONE_BEEP | _instance_key |
                 (uart_id << _PUSH_BOT_UART_OFFSET_SPEAKER_LED_LASER)),
        .payload = frequency,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_speaker_set_melody(
        uint32_t melody, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_SPEAKER_TONE_MELODY | _instance_key |
                 (uart_id << _PUSH_BOT_UART_OFFSET_SPEAKER_LED_LASER)),
        .payload = melody,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_led_total_period(
        uint32_t total_period, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_LED_CONFIG_TOTAL_PERIOD |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = total_period,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_led_back_active_time(
        uint32_t active_time, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_LED_BACK_CONFIG_ACTIVE_TIME |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = active_time,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_led_front_active_time(
        uint32_t active_time, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_LED_FRONT_CONFIG_ACTIVE_TIME |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = active_time,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_led_set_frequency(
        uint32_t frequency, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_LED_FREQUENCY | _instance_key |
                 (uart_id << _PUSH_BOT_UART_OFFSET_SPEAKER_LED_LASER)),
        .payload = frequency,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_motor_0_permanent(
        state_t velocity, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_MOTOR_0_PERMANENT_VELOCITY + uart_id) |
                _instance_key,
        .payload = velocity,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet munich_protocol_push_bot_motor_1_permanent(
        uint32_t velocity, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_MOTOR_1_PERMANENT_VELOCITY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = velocity,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_push_bot_motor_0_leaking_towards_zero(
        uint32_t velocity, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_MOTOR_0_LEAKY_VELOCITY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = velocity,
        .payload_flag = WITH_PAYLOAD
    };
}

static inline multicast_packet
munich_protocol_push_bot_motor_1_leaking_towards_zero(
        uint32_t velocity, uint32_t uart_id) {
    if (_mode != MUNICH_PROTOCOL_PUSH_BOT) {
        log_error(
            "The mode you configured is not the pushbot, and so this "
            "message is invalid for mode %d", _mode);
    }

    return (multicast_packet) {
        .key = (_PUSH_BOT_MOTOR_1_LEAKY_VELOCITY |
                 (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
        .payload = velocity,
        .payload_flag = WITH_PAYLOAD
    };
}


static inline multicast_packet _key_retina(
        uint32_t retina_pixels, uint32_t time_stamps, uint32_t uart_id) {
    if (retina_pixels == 128 * 128) {
        // if fine, create message
        return (multicast_packet) {
            .key = (_ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION |
                      (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
            .payload = (time_stamps | _PAYLOAD_RETINA_NO_DOWN_SAMPLING),
            .payload_flag = WITH_PAYLOAD
        };
    }
    if (retina_pixels == 64 * 64) {
        return (multicast_packet) {
            .key = (_ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION |
                      (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
            .payload = (time_stamps | _PAYLOAD_RETINA_64_DOWN_SAMPLING),
            .payload_flag = WITH_PAYLOAD
        };
    }
    if (retina_pixels == 32 * 32) {
        return (multicast_packet) {
            .key = (_ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION |
                      (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
            .payload = (time_stamps | _PAYLOAD_RETINA_32_DOWN_SAMPLING),
            .payload_flag = WITH_PAYLOAD
        };
    }
    if (retina_pixels == 16 * 16) {
        return (multicast_packet) {
            .key = (_ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION |
                      (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
            .payload = (time_stamps | _PAYLOAD_RETINA_16_DOWN_SAMPLING),
            .payload_flag = WITH_PAYLOAD
        };
    }

    log_error("The no of pixels is not supported in this protocol.");
    rt_error(RTE_API);
    return (multicast_packet) {.key = 0, .payload = 0, .payload_flag = 0};
}

static inline multicast_packet munich_protocol_set_retina_transmission(
        bool events_in_key, uint32_t retina_pixels,
        bool payload_holds_time_stamps, uint32_t size_of_time_stamp_in_bytes,
        uint32_t uart_id) {

    // if events in the key.
    if (events_in_key) {
        if (!payload_holds_time_stamps) {
            // not using payloads
            return _key_retina(
        	    retina_pixels, _PAYLOAD_NO_TIMESTAMPS, uart_id);
        }

        // using payloads
        if (size_of_time_stamp_in_bytes == 0) {
            return _key_retina(
        	    retina_pixels, _PAYLOAD_DELTA_TIMESTAMPS, uart_id);
        } else if (size_of_time_stamp_in_bytes == 2) {
            return _key_retina(
                    retina_pixels, _PAYLOAD_TWO_BYTE_TIME_STAMPS, uart_id);
        } else if (size_of_time_stamp_in_bytes == 3) {
            return _key_retina(
                    retina_pixels, _PAYLOAD_THREE_BYTE_TIME_STAMPS, uart_id);
        } else if (size_of_time_stamp_in_bytes == 4) {
            return _key_retina(
                    retina_pixels, _PAYLOAD_FOUR_BYTE_TIME_STAMPS, uart_id);
        }

        log_error("Unknown size of timestamp in bytes: %d\n",
        	size_of_time_stamp_in_bytes);
        rt_error(RTE_SWERR);
        return (multicast_packet) {
            .key = 0, .payload = 0, .payload_flag = 0
        };
    } else {
        // using payloads to hold all events

        // warn users about models
        log_warning(
            "The current SpyNNaker models do not support the reception of"
            " packets with payloads, therefore you will need to add a "
            "adaptor model between the device and spynnaker models.");

        // verify that its what the end user wants.
        if (payload_holds_time_stamps ||
                (size_of_time_stamp_in_bytes == NULL)) {
            log_error(
                "If you are using payloads to store events, you cannot"
                " have time stamps at all.");
            rt_error(RTE_API);
        }

        // if fine, create message
        return (multicast_packet) {
            .key = (_ACTIVE_RETINA_EVENT_STREAMING_KEYS_CONFIGURATION |
                      (uart_id << _OFFSET_FOR_UART_ID) | _instance_key),
            .payload = (_PAYLOAD_NO_TIMESTAMPS |
                          _PAYLOAD_RETINA_NO_DOWN_SAMPLING_IN_PAYLOAD),
            .payload_flag = WITH_PAYLOAD
        };
    }
}
