# Copyright (c) 2017-2023 The University of Manchester
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

from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotOutputDevice)


class PushBotMotor(AbstractPushBotOutputDevice):
    """ The properties of the motor devices that may be set.
    The pushbot has two motors, 0 (left) and 1 (right).
    """
    # TODO: is that the right way round?

    #: For motor 0, set a particular speed
    MOTOR_0_PERMANENT = (
        0, MunichIoSpiNNakerLinkProtocol.push_bot_motor_0_permanent_key,
        -100, 100, 20
    )

    #: For motor 0, set a variable speed depending on time since event receive
    MOTOR_0_LEAKY = (
        1,
        (MunichIoSpiNNakerLinkProtocol
         .push_bot_motor_0_leaking_towards_zero_key),
        -100, 100, 20
    )

    #: For motor 0, set a particular speed
    MOTOR_1_PERMANENT = (
        2, MunichIoSpiNNakerLinkProtocol.push_bot_motor_1_permanent_key,
        -100, 100, 20
    )

    #: For motor 1, set a variable speed depending on time since event receive
    MOTOR_1_LEAKY = (
        3,
        (MunichIoSpiNNakerLinkProtocol
         .push_bot_motor_1_leaking_towards_zero_key),
        -100, 100, 20
    )
