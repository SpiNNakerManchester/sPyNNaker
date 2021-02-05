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

from data_specification.enums import DataType
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotOutputDevice)


class PushBotLED(AbstractPushBotOutputDevice):
    """ The properties of the LED device that may be set.
    """

    LED_TOTAL_PERIOD = (
        0, MunichIoSpiNNakerLinkProtocol.push_bot_led_total_period_key,
        0, DataType.S1615.max, 20
    )

    LED_FRONT_ACTIVE_TIME = (
        1, MunichIoSpiNNakerLinkProtocol.push_bot_led_front_active_time_key,
        0, DataType.S1615.max, 20
    )

    LED_BACK_ACTIVE_TIME = (
        2, MunichIoSpiNNakerLinkProtocol.push_bot_led_back_active_time_key,
        0, DataType.S1615.max, 20
    )

    LED_FREQUENCY = (
        3, MunichIoSpiNNakerLinkProtocol.push_bot_led_set_frequency_key,
        0, DataType.S1615.max, 20
    )
