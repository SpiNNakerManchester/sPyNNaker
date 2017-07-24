from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from data_specification.enums import DataType
from spynnaker.pyNN.external_devices_models.push_bot \
    import AbstractPushBotOutputDevice


class PushBotLaser(AbstractPushBotOutputDevice):

    LASER_TOTAL_PERIOD = (
        0,
        MunichIoSpiNNakerLinkProtocol.push_bot_laser_config_total_period_key,
        0, DataType.S1615.max, 20
    )

    LASER_ACTIVE_TIME = (
        1, MunichIoSpiNNakerLinkProtocol.push_bot_laser_config_active_time_key,
        0, DataType.S1615.max, 20
    )

    LASER_FREQUENCY = (
        2, MunichIoSpiNNakerLinkProtocol.push_bot_laser_set_frequency_key,
        0, DataType.S1615.max, 20
    )
