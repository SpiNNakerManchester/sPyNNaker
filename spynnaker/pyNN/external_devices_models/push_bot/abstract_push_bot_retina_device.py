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

from typing import Iterable, List
from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utility_models import MultiCastCommand


class AbstractPushBotRetinaDevice(
        AbstractSendMeMulticastCommandsVertex):
    """
    An abstraction of a silicon retina attached to a SpiNNaker system.
    """

    def __init__(self, protocol, resolution):
        """
        :param protocol:
        :type protocol:
            MunichIoEthernetProtocol or MunichIoSpiNNakerLinkProtocol
        :param PushBotRetinaResolution resolution:
        """
        self._protocol = protocol
        self._resolution = resolution

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self) -> Iterable[MultiCastCommand]:
        # add mode command if not done already
        if not self._protocol.sent_mode_command():
            yield self._protocol.set_mode()

        # device specific commands
        yield self._protocol.disable_retina()

        retina_key = None
        if self._resolution is not None:
            retina_key = self._resolution.value
        yield self._protocol.set_retina_transmission(retina_key=retina_key)

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self) -> Iterable[MultiCastCommand]:
        yield self._protocol.disable_retina()

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self) -> List[MultiCastCommand]:
        return []
