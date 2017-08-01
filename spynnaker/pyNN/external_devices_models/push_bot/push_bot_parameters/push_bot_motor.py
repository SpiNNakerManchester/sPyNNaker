from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.external_devices_models.push_bot \
    import AbstractPushBotOutputDevice


class PushBotMotor(AbstractPushBotOutputDevice):

    MOTOR_0_PERMANENT = (
        0, MunichIoSpiNNakerLinkProtocol.push_bot_motor_0_permanent_key,
        -100, 100, 20
    )

    MOTOR_0_LEAKY = (
        1,
        (MunichIoSpiNNakerLinkProtocol
         .push_bot_motor_0_leaking_towards_zero_key),
        -100, 100, 20
    )

    MOTOR_1_PERMANENT = (
        2, MunichIoSpiNNakerLinkProtocol.push_bot_motor_1_permanent_key,
        -100, 100, 20
    )

    MOTOR_1_LEAKY = (
        3,
        (MunichIoSpiNNakerLinkProtocol
         .push_bot_motor_1_leaking_towards_zero_key),
        -100, 100, 20
    )
