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
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spinn_front_end_common.utility_models import MultiCastCommand
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotRetinaDevice)


class DelayedPayloadMultiCastCommand(MultiCastCommand):
    """
    A Hack to get the key after the zone allocator is run
    """

    def __init__(self, key, vertex):
        super().__init__(key)
        self._vertex = vertex

    @property
    def payload(self):
        if self._payload is None:
            self._payload = self._vertex.new_key_command_payload()
        return self._payload

    @property
    def is_payload(self):
        return self.payload is not None


class PushBotSpiNNakerLinkRetinaDevice(
        AbstractPushBotRetinaDevice, ApplicationSpiNNakerLinkVertex):
    __slots__ = ["__new_key_command"]

    default_parameters = {'label': None, 'board_address': None}

    def __init__(
            self, spinnaker_link_id, protocol, resolution,
            board_address=default_parameters['board_address'],
            label=default_parameters['label']):
        """
        :param spinnaker_link_id:
        :param protocol:
        :type protocol: ~spynnaker.pyNN.protocols.MunichIoSpiNNakerLinkProtocol
        :param resolution:
        :type resolution:
            ~spynnaker.pyNN.external_devices_models.push_bot.parameters.PushBotRetinaResolution
        :param board_address:
        :param label:
        """
        super().__init__(protocol, resolution)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id,
            n_atoms=resolution.value.n_neurons,
            board_address=board_address, label=label)

        # stores for the injection aspects
        self.__new_key_command = None

    @inject_items({
        "routing_info": "RoutingInfos"
    })
    def new_key_command_payload(self, routing_info):
        """
        Support method to obtain the key after the key allocator has run

        :param routing_info:
        :return: the key
        :rtype: int
        """
        key = routing_info.get_first_key_from_pre_vertex(
            next(iter(self.machine_vertices)), SPIKE_PARTITION_ID)
        return key

    @property
    @overrides(AbstractPushBotRetinaDevice.start_resume_commands)
    def start_resume_commands(self):
        # Update the commands with the additional one to set the key
        new_commands = list()
        for command in super().start_resume_commands:
            if command.key == self._protocol.disable_retina_key:
                # This has to be stored so that the payload can be updated
                self.__new_key_command = DelayedPayloadMultiCastCommand(
                    self._protocol.set_retina_key_key, self)
                new_commands.append(self.__new_key_command)
            new_commands.append(command)
        return new_commands
