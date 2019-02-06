import unittest

from spynnaker.pyNN.external_devices_models.push_bot.push_bot_parameters \
    import PushBotLaser
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_parameters \
    import PushBotMotor
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_parameters \
    import PushBotSpeaker
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_parameters \
    import PushBotLED


class Test(unittest.TestCase):

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
