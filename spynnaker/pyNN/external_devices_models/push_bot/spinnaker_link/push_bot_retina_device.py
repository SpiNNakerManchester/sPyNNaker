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

from typing import Iterable
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spinn_front_end_common.utility_models import MultiCastCommand
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotRetinaDevice)
from spynnaker.pyNN.models.common import PopulationApplicationVertex


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
        AbstractPushBotRetinaDevice, ApplicationSpiNNakerLinkVertex,
        PopulationApplicationVertex):
    __slots__ = ("__new_key_command", )

    default_parameters = {'label': None, 'board_address': None,
                          'n_machine_vertices': 1}

    def __init__(
            self, spinnaker_link_id, protocol, resolution,
            board_address=default_parameters['board_address'],
            label=default_parameters['label'],
            n_machine_vertices=default_parameters['n_machine_vertices']):
        """
        :param int spinnaker_link_id:
        :param MunichIoSpiNNakerLinkProtocol protocol:
        :param PushBotRetinaResolution resolution:
        :param str board_address:
        :param str label:
        :param int n_machine_vertices:
        """
        super().__init__(protocol, resolution)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id,
            n_atoms=resolution.value.n_neurons,
            board_address=board_address, label=label,
            n_machine_vertices=n_machine_vertices)

        # stores for the injection aspects
        self.__new_key_command = None

    def new_key_command_payload(self):
        """
        Support method to obtain the key after the key allocator has run

        :param routing_info:
        :return: the key
        :rtype: int
        """
        routing_info = SpynnakerDataView.get_routing_infos()
        key = routing_info.get_first_key_from_pre_vertex(
            self, SPIKE_PARTITION_ID)
        return key

    @property
    @overrides(AbstractPushBotRetinaDevice.start_resume_commands)
    def start_resume_commands(
            self) -> Iterable[DelayedPayloadMultiCastCommand]:
        # Update the commands with the additional one to set the key
        new_commands = list()
        for command in super().start_resume_commands:
            if command.key == self._protocol.set_retina_transmission_key:
                # This has to be stored so that the payload can be updated
                self.__new_key_command = DelayedPayloadMultiCastCommand(
                    self._protocol.set_retina_key_key, self)
                new_commands.append(self.__new_key_command)
            new_commands.append(command)
        return new_commands
