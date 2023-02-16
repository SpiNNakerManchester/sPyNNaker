# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotLaser, PushBotMotor, PushBotSpeaker, PushBotLED)


class Test(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def _test_device_enum(self, enum_class):
        for item in enum_class:
            print(item)
            item.value
            item.protocol_property
            item.min_value
            item.max_value
            item.time_between_send

    def test_laser_device(self):
        self._test_device_enum(PushBotLaser)

    def test_led_device(self):
        self._test_device_enum(PushBotLED)

    def test_motor_device(self):
        self._test_device_enum(PushBotMotor)

    def test_speaker_device(self):
        self._test_device_enum(PushBotSpeaker)


if __name__ == "__main__":
    unittest.main()
