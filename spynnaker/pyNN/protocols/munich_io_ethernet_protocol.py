def _active_time_for_frequency(frequency):
    if frequency > 0:
        return int(1000000.0 / float(frequency))
    return 0


class MunichIoEthernetProtocol(object):

    def __init__(self):
        pass

    @staticmethod
    def enable_retina():
        return "E+\n"

    @staticmethod
    def disable_retina():
        return "E-\n"

    @staticmethod
    def set_retina_transmission(event_format):
        return "!E{}\n".format(event_format)

    @staticmethod
    def disable_motor():
        return "!M-\n"

    @staticmethod
    def enable_motor():
        return "!M+\n"

    @staticmethod
    def motor_0_permanent_velocity(velocity):
        if velocity >= 100:
            velocity = 100
        if velocity < -100:
            velocity = -100
        return "!MV0={}\n".format(velocity)

    @staticmethod
    def motor_1_permanent_velocity(velocity):
        if velocity >= 100:
            velocity = 100
        if velocity < -100:
            velocity = -100
        return "!MV1={}\n".format(velocity)

    @staticmethod
    def motor_0_leaky_velocity(velocity):
        if velocity >= 100:
            velocity = 100
        if velocity < -100:
            velocity = -100
        return "!MVD0={}\n".format(velocity)

    @staticmethod
    def motor_1_leaky_velocity(velocity):
        if velocity >= 100:
            velocity = 100
        if velocity < -100:
            velocity = -100
        return "!MVD1={}\n".format(velocity)

    @staticmethod
    def led_total_period(total_period):
        return "!PC={}\n".format(total_period)

    @staticmethod
    def led_front_active_time(active_time):
        return "!PC1={}\n".format(active_time)

    @staticmethod
    def led_back_active_time(active_time):
        return "!PC0={}\n".format(active_time)

    @staticmethod
    def led_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        return "!PC={}\n!PC0={}\n!PC1={}\n".format(
            active_time, active_time / 2, active_time / 2)

    @staticmethod
    def speaker_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        return "!PB={}\n!PB0={}\n".format(active_time, active_time / 2)

    @staticmethod
    def speaker_total_period(total_period):
        return "!PB={}\n".format(total_period)

    @staticmethod
    def speaker_active_time(active_time):
        return "!PB0={}\n".format(active_time)

    @staticmethod
    def laser_frequency(frequency):
        active_time = _active_time_for_frequency(frequency)
        return "!PA={}\n!PA0={}\n".format(active_time, active_time / 2)

    @staticmethod
    def laser_total_period(total_period):
        return "!PA={}\n".format(total_period)

    @staticmethod
    def laser_active_time(active_time):
        return "!PA0={}\n".format(active_time)
