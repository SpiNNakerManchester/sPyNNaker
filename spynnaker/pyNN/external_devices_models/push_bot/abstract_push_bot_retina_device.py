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

from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)


class AbstractPushBotRetinaDevice(
        AbstractSendMeMulticastCommandsVertex):
    """ An abstraction of a silicon retina attached to a SpiNNaker system.
    """

    def __init__(self, protocol, resolution):
        """
        :param protocol:
        :type protocol:
            MunichIoEthernetProtocol or
            ~spynnaker.pyNN.protocols.MunichIoSpiNNakerLinkProtocol
        :param resolution:
        :type resolution:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotRetinaResolution
        """
        self._protocol = protocol
        self._resolution = resolution

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        commands = list()

        # add mode command if not done already
        if not self._protocol.sent_mode_command():
            commands.append(self._protocol.set_mode())

        # device specific commands
        commands.append(self._protocol.disable_retina())
        commands.append(self._protocol.set_retina_transmission(
            retina_key=self._resolution.value))

        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        return [self._protocol.disable_retina()]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
