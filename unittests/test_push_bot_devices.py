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
