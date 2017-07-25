from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.external_devices_models.push_bot \
    import AbstractPushBotOutputDevice
from data_specification.enums import DataType


class PushBotSpeaker(AbstractPushBotOutputDevice):

    SPEAKER_TOTAL_PERIOD = (
        0,
        MunichIoSpiNNakerLinkProtocol.push_bot_speaker_config_total_period_key,
        0, DataType.S1615.max, 20
    )

    SPEAKER_ACTIVE_TIME = (
        1,
        MunichIoSpiNNakerLinkProtocol.push_bot_speaker_config_active_time_key,
        0, DataType.S1615.max, 20
    )

    SPEAKER_TONE = (
        2, MunichIoSpiNNakerLinkProtocol.push_bot_speaker_set_tone_key,
        0, DataType.S1615.max, 20
    )

    SPEAKER_MELODY = (
        3, MunichIoSpiNNakerLinkProtocol.push_bot_speaker_set_melody_key,
        0, DataType.S1615.max, 20
    )
