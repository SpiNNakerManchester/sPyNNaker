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

import unittest
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.protocols import (
    MunichIoSpiNNakerLinkProtocol, MUNICH_MODES, RetinaKey)


class TestMunichIOSpinnakerLinkProtocol(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_call_each_function(self):
        protocol = MunichIoSpiNNakerLinkProtocol(
            mode=MUNICH_MODES.PUSH_BOT)
        protocol.add_payload_logic_to_current_output(0)
        protocol.add_payload_logic_to_current_output_key
        protocol.bias_values(0, 0)
        protocol.bias_values_key
        protocol.configure_master_key(0)
        protocol.configure_master_key_key
        protocol.disable_retina()
        protocol.disable_retina_key
        protocol.enable_disable_motor_key
        protocol.generic_motor0_raw_output_leak_to_0(0)
        protocol.generic_motor0_raw_output_leak_to_0_key
        protocol.generic_motor0_raw_output_permanent(0)
        protocol.generic_motor0_raw_output_permanent_key
        protocol.generic_motor1_raw_output_leak_to_0(0)
        protocol.generic_motor1_raw_output_leak_to_0_key
        protocol.generic_motor1_raw_output_permanent(0)
        protocol.generic_motor1_raw_output_permanent_key
        protocol.generic_motor_disable()
        protocol.generic_motor_enable()
        protocol.generic_motor_total_period(0)
        protocol.generic_motor_total_period_key
        protocol.instance_key
        protocol.master_slave_key
        protocol.master_slave_set_master_clock_active()
        protocol.master_slave_set_master_clock_not_started()
        protocol.master_slave_set_slave()
        protocol.master_slave_use_internal_counter()
        protocol.mode
        protocol.poll_individual_sensor_continuously(0, 0)
        protocol.poll_individual_sensor_continuously_key
        protocol.poll_sensors_once(0)
        protocol.poll_sensors_once_key
        protocol.push_bot_laser_config_active_time(0)
        protocol.push_bot_laser_config_active_time_key
        protocol.push_bot_laser_config_total_period(0)
        protocol.push_bot_laser_config_total_period_key
        protocol.push_bot_laser_set_frequency(0)
        protocol.push_bot_laser_set_frequency_key
        protocol.push_bot_led_back_active_time(0)
        protocol.push_bot_led_back_active_time_key
        protocol.push_bot_led_front_active_time(0)
        protocol.push_bot_led_front_active_time_key
        protocol.push_bot_led_set_frequency(0)
        protocol.push_bot_led_set_frequency_key
        protocol.push_bot_led_total_period(0)
        protocol.push_bot_led_total_period_key
        protocol.push_bot_motor_0_leaking_towards_zero(0)
        protocol.push_bot_motor_0_leaking_towards_zero_key
        protocol.push_bot_motor_0_permanent(0)
        protocol.push_bot_motor_0_permanent_key
        protocol.push_bot_motor_1_leaking_towards_zero(0)
        protocol.push_bot_motor_1_leaking_towards_zero_key
        protocol.push_bot_motor_1_permanent(0)
        protocol.push_bot_motor_1_permanent_key
        protocol.push_bot_speaker_config_active_time(0)
        protocol.push_bot_speaker_config_active_time_key
        protocol.push_bot_speaker_config_total_period(0)
        protocol.push_bot_speaker_config_total_period_key
        protocol.push_bot_speaker_set_melody(0)
        protocol.push_bot_speaker_set_melody_key
        protocol.push_bot_speaker_set_tone(0)
        protocol.push_bot_speaker_set_tone_key
        protocol.pwm_pin_output_timer_a_channel_0_ratio(0)
        protocol.pwm_pin_output_timer_a_channel_0_ratio_key
        protocol.pwm_pin_output_timer_a_channel_1_ratio(0)
        protocol.pwm_pin_output_timer_a_channel_1_ratio_key
        protocol.pwm_pin_output_timer_a_duration(0)
        protocol.pwm_pin_output_timer_a_duration_key
        protocol.pwm_pin_output_timer_b_channel_0_ratio(0)
        protocol.pwm_pin_output_timer_b_channel_0_ratio_key
        protocol.pwm_pin_output_timer_b_channel_1_ratio(0)
        protocol.pwm_pin_output_timer_b_channel_1_ratio_key
        protocol.pwm_pin_output_timer_b_duration(0)
        protocol.pwm_pin_output_timer_b_duration_key
        protocol.pwm_pin_output_timer_c_channel_0_ratio(0)
        protocol.pwm_pin_output_timer_c_channel_0_ratio_key
        protocol.pwm_pin_output_timer_c_channel_1_ratio(0)
        protocol.pwm_pin_output_timer_c_channel_1_ratio_key
        protocol.pwm_pin_output_timer_c_duration(0)
        protocol.pwm_pin_output_timer_c_duration_key
        protocol.query_state_of_io_lines()
        protocol.query_state_of_io_lines_key
        protocol.remove_payload_logic_to_current_output(0)
        protocol.remove_payload_logic_to_current_output_key
        protocol.reset_retina()
        protocol.reset_retina_key
        protocol.sensor_transmission_key(0)
        protocol.sent_mode_command()
        protocol.set_mode()
        protocol.set_mode_key
        protocol.set_output_pattern_for_payload(0)
        protocol.set_output_pattern_for_payload_key
        protocol.set_payload_pins_to_high_impedance
        protocol.set_payload_pins_to_high_impedance_key
        protocol.set_retina_key(0)
        protocol.set_retina_key_key
        protocol.set_retina_transmission(RetinaKey.FIXED_KEY)
        protocol.set_retina_transmission_key
        protocol.turn_off_sensor_reporting(0)
        protocol.turn_off_sensor_reporting_key
        protocol.uart_id


if __name__ == "__main__":
    unittest.main()
