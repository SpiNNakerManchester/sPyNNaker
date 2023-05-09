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


def _clamp(a, b, c):
    """
    Force `b` to be between `a` and `c`. `a` must be no larger than `c`.
    """
    return max(a, min(b, c))


def _active_time_for_frequency(frequency):
    if frequency > 0:
        return int(1000000.0 / float(frequency))
    return 0


class MunichIoEthernetProtocol(object):
    """
    Implementation of the Munich robot IO protocol, communicating over
    Ethernet.
    """

    def __init__(self):
        # Nothing to do here
        pass

    @staticmethod
    def enable_retina():
        return b"E+\n"

    @staticmethod
    def disable_retina():
        return b"E-\n"

    @staticmethod
    def set_retina_transmission(event_format):
        return f"!E{event_format}\n".encode("ascii")

    @staticmethod
    def disable_motor():
        return b"!M-\n"

    @staticmethod
    def enable_motor():
        return b"!M+\n"

    @staticmethod
    def motor_0_permanent_velocity(velocity):
        return f"!MV0={_clamp(-100, velocity, 100)}\n".encode("ascii")

    @staticmethod
    def motor_1_permanent_velocity(velocity):
        return f"!MV1={_clamp(-100, velocity, 100)}\n".encode("ascii")

    @staticmethod
    def motor_0_leaky_velocity(velocity):
        return f"!MVD0={_clamp(-100, velocity, 100)}\n".encode("ascii")

    @staticmethod
    def motor_1_leaky_velocity(velocity):
        return f"!MVD1={_clamp(-100, velocity, 100)}\n".encode("ascii")

    @staticmethod
    def led_total_period(total_period):
        return f"!PC={total_period}\n".encode("ascii")

    @staticmethod
    def led_front_active_time(active_time):
        return f"!PC1={active_time}\n".encode("ascii")

    @staticmethod
    def led_back_active_time(active_time):
        return f"!PC0={active_time}\n".encode("ascii")

    @staticmethod
    def led_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        at2 = active_time // 2
        return f"!PC={active_time}\n!PC0={at2}\n!PC1={at2}\n".encode("ascii")

    @staticmethod
    def speaker_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        return f"!PB={active_time}\n!PB0={active_time // 2}\n".encode("ascii")

    @staticmethod
    def speaker_total_period(total_period):
        return f"!PB={total_period}\n".encode("ascii")

    @staticmethod
    def speaker_active_time(active_time):
        return f"!PB0={active_time}\n".encode("ascii")

    @staticmethod
    def laser_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        return f"!PA={active_time}\n!PA0={active_time // 2}\n".encode("ascii")

    @staticmethod
    def laser_total_period(total_period):
        return f"!PA={total_period}\n".encode("ascii")

    @staticmethod
    def laser_active_time(active_time):
        return f"!PA0={active_time}\n".encode("ascii")
