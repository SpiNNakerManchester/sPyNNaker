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
from spynnaker.pyNN.protocols.munich_io_spinnaker_link_protocol import (
    _OFFSET_TO_IGNORED_KEY)


class TestMunichIOSpinnakerLinkProtocol(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_call_each_method(self):
        protocol = MunichIoSpiNNakerLinkProtocol(
            mode=MUNICH_MODES.PUSH_BOT)
        protocol.add_payload_logic_to_current_output(0)
        protocol.bias_values(0, 0)
        protocol.configure_master_key(0)
        protocol.disable_retina()
        protocol.generic_motor0_raw_output_leak_to_0(0)
        protocol.generic_motor0_raw_output_permanent(0)
        protocol.generic_motor1_raw_output_leak_to_0(0)
        protocol.generic_motor1_raw_output_permanent(0)
        protocol.generic_motor_disable()
        protocol.generic_motor_enable()
        protocol.generic_motor_total_period(0)
        protocol.master_slave_set_master_clock_active()
        protocol.master_slave_set_master_clock_not_started()
        protocol.master_slave_set_slave()
        protocol.master_slave_use_internal_counter()
        protocol.poll_individual_sensor_continuously(0, 0)
        protocol.poll_sensors_once(0)
        protocol.push_bot_laser_config_active_time(0)
        protocol.push_bot_laser_config_total_period(0)
        protocol.push_bot_laser_set_frequency(0)
        protocol.push_bot_led_back_active_time(0)
        protocol.push_bot_led_front_active_time(0)
        protocol.push_bot_led_set_frequency(0)
        protocol.push_bot_led_total_period(0)
        protocol.push_bot_motor_0_leaking_towards_zero(0)
        protocol.push_bot_motor_0_permanent(0)
        protocol.push_bot_motor_1_leaking_towards_zero(0)
        protocol.push_bot_motor_1_permanent(0)
        protocol.push_bot_speaker_config_active_time(0)
        protocol.push_bot_speaker_config_total_period(0)
        protocol.push_bot_speaker_set_melody(0)
        protocol.push_bot_speaker_set_tone(0)
        protocol.pwm_pin_output_timer_a_channel_0_ratio(0)
        protocol.pwm_pin_output_timer_a_channel_1_ratio(0)
        protocol.pwm_pin_output_timer_a_duration(0)
        protocol.pwm_pin_output_timer_b_channel_0_ratio(0)
        protocol.pwm_pin_output_timer_b_channel_1_ratio(0)
        protocol.pwm_pin_output_timer_b_duration(0)
        protocol.pwm_pin_output_timer_c_channel_0_ratio(0)
        protocol.pwm_pin_output_timer_c_channel_1_ratio(0)
        protocol.pwm_pin_output_timer_c_duration(0)
        protocol.query_state_of_io_lines()
        protocol.remove_payload_logic_to_current_output(0)
        protocol.reset_retina()
        protocol.sensor_transmission_key(0)
        protocol.sent_mode_command()
        protocol.set_mode()
        protocol.set_output_pattern_for_payload(0)
        protocol.set_payload_pins_to_high_impedance(0)
        protocol.set_retina_key(0)
        protocol.set_retina_transmission(RetinaKey.FIXED_KEY)
        protocol.turn_off_sensor_reporting(0)

    def test_read_each_property(self):
        # Explicit instance key for testability
        protocol = MunichIoSpiNNakerLinkProtocol(
            mode=MUNICH_MODES.PUSH_BOT, uart_id=1,
            instance_key=1 << _OFFSET_TO_IGNORED_KEY)
        # Basic data
        assert protocol.mode == MUNICH_MODES.PUSH_BOT
        assert protocol.uart_id == 1
        assert protocol.instance_key == 0x800
        # Derived keys
        assert protocol.disable_retina_key == 0x880
        assert protocol.set_retina_key_key == 0x882
        assert protocol.set_retina_transmission_key == 0x881
        assert protocol.enable_disable_motor_key == 0x8A0
        assert protocol.push_bot_laser_config_total_period_key == 0x8B0
        assert protocol.push_bot_speaker_config_total_period_key == 0x8B2
        assert protocol.push_bot_led_total_period_key == 0x8B4
        assert protocol.push_bot_laser_config_active_time_key == 0x8C0
        assert protocol.push_bot_speaker_config_active_time_key == 0x8C2
        assert protocol.push_bot_led_back_active_time_key == 0x8C4
        assert protocol.push_bot_led_front_active_time_key == 0x8C5
        assert protocol.push_bot_motor_0_permanent_key == 0xA10
        assert protocol.push_bot_motor_1_permanent_key == 0xA11
        assert protocol.push_bot_motor_0_leaking_towards_zero_key == 0xA12
        assert protocol.push_bot_motor_1_leaking_towards_zero_key == 0xA13
        assert protocol.push_bot_speaker_set_tone_key == 0xA42
        assert protocol.push_bot_speaker_set_melody_key == 0xA43
        assert protocol.push_bot_led_set_frequency_key == 0xA52
        assert protocol.push_bot_laser_set_frequency_key == 0xA53


if __name__ == "__main__":
    unittest.main()
