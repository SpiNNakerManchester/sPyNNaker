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


def _clamp(a, b, c):
    """ Force `b` to be between `a` and `c`. `a` must be no larger than `c`.
    """
    return max(a, min(b, c))


def _active_time_for_frequency(frequency):
    if frequency > 0:
        return int(1000000.0 / float(frequency))
    return 0


class MunichIoEthernetProtocol(object):
    """ Implementation of the Munich robot IO protocol, communicating over
        ethernet.
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
        return "!E{}\n".format(event_format).encode("ascii")

    @staticmethod
    def disable_motor():
        return b"!M-\n"

    @staticmethod
    def enable_motor():
        return b"!M+\n"

    @staticmethod
    def motor_0_permanent_velocity(velocity):
        return "!MV0={}\n".format(
            _clamp(-100, velocity, 100)).encode("ascii")

    @staticmethod
    def motor_1_permanent_velocity(velocity):
        return "!MV1={}\n".format(
            _clamp(-100, velocity, 100)).encode("ascii")

    @staticmethod
    def motor_0_leaky_velocity(velocity):
        return "!MVD0={}\n".format(
            _clamp(-100, velocity, 100)).encode("ascii")

    @staticmethod
    def motor_1_leaky_velocity(velocity):
        return "!MVD1={}\n".format(
            _clamp(-100, velocity, 100)).encode("ascii")

    @staticmethod
    def led_total_period(total_period):
        return "!PC={}\n".format(total_period).encode("ascii")

    @staticmethod
    def led_front_active_time(active_time):
        return "!PC1={}\n".format(active_time).encode("ascii")

    @staticmethod
    def led_back_active_time(active_time):
        return "!PC0={}\n".format(active_time).encode("ascii")

    @staticmethod
    def led_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        return "!PC={}\n!PC0={}\n!PC1={}\n".format(
            active_time, active_time // 2, active_time // 2).encode("ascii")

    @staticmethod
    def speaker_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        return "!PB={}\n!PB0={}\n".format(
            active_time, active_time // 2).encode("ascii")

    @staticmethod
    def speaker_total_period(total_period):
        return "!PB={}\n".format(total_period).encode("ascii")

    @staticmethod
    def speaker_active_time(active_time):
        return "!PB0={}\n".format(active_time).encode("ascii")

    @staticmethod
    def laser_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        return "!PA={}\n!PA0={}\n".format(
            active_time, active_time // 2).encode("ascii")

    @staticmethod
    def laser_total_period(total_period):
        return "!PA={}\n".format(total_period).encode("ascii")

    @staticmethod
    def laser_active_time(active_time):
        return "!PA0={}\n".format(active_time).encode("ascii")
