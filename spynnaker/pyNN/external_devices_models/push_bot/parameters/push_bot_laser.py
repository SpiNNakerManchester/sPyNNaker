# Copyright (c) 2017 The University of Manchester
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

from data_specification.enums import DataType
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotOutputDevice)


class PushBotLaser(AbstractPushBotOutputDevice):
    """ The properties of the laser device that may be set.
    """

    #: The total period for the laser
    LASER_TOTAL_PERIOD = (
        0,
        MunichIoSpiNNakerLinkProtocol.push_bot_laser_config_total_period_key,
        0, DataType.S1615.max, 20
    )

    #: The active period for the laser (no larger than the total period)
    LASER_ACTIVE_TIME = (
        1, MunichIoSpiNNakerLinkProtocol.push_bot_laser_config_active_time_key,
        0, DataType.S1615.max, 20
    )

    #: The frequency of the laser
    LASER_FREQUENCY = (
        2, MunichIoSpiNNakerLinkProtocol.push_bot_laser_set_frequency_key,
        0, DataType.S1615.max, 20
    )
