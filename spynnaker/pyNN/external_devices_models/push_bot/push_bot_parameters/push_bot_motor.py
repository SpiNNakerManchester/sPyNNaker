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

from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotOutputDevice)


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
