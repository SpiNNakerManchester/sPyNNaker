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

from spinn_front_end_common.interface.ds import DataType
from spynnaker.pyNN.protocols import MunichIoSpiNNakerLinkProtocol
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotOutputDevice)


class PushBotSpeaker(AbstractPushBotOutputDevice):
    """
    The properties of the speaker device that may be set.
    """

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
