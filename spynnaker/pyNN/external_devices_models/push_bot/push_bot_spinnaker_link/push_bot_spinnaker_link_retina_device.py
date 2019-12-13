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

import logging
from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject, supports_injection
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.external_devices_models.push_bot import (
    AbstractPushBotRetinaDevice)

logger = logging.getLogger(__name__)


@supports_injection
class PushBotSpiNNakerLinkRetinaDevice(
        AbstractPushBotRetinaDevice, ApplicationSpiNNakerLinkVertex):
    __slots__ = [
        "__graph_mapper",
        "__new_key_command",
        "__routing_infos"]

    default_parameters = {'label': None, 'board_address': None}

    def __init__(
            self, spinnaker_link_id, protocol, resolution,
            board_address=default_parameters['board_address'],
            label=default_parameters['label']):

        AbstractPushBotRetinaDevice.__init__(self, protocol, resolution)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id,
            n_atoms=resolution.value.n_neurons,
            board_address=board_address, label=label)

        # stores for the injection aspects
        self.__graph_mapper = None
        self.__routing_infos = None
        self.__new_key_command = None

    @inject("MemoryGraphMapper")
    def graph_mapper(self, graph_mapper):
        self.__graph_mapper = graph_mapper
        if self.__routing_infos is not None:
            self._update_new_key_payload()

    @inject("MemoryRoutingInfos")
    def routing_info(self, routing_info):
        self.__routing_infos = routing_info
        if self.__graph_mapper is not None:
            self._update_new_key_payload()

    @property
    @overrides(AbstractPushBotRetinaDevice.start_resume_commands)
    def start_resume_commands(self):
        # Note this is not undefined, it is just a property so, it can't
        # be statically analysed
        sr_cmds = AbstractPushBotRetinaDevice.start_resume_commands
        commands = sr_cmds.fget(self)  # pylint: disable=no-member

        # Update the commands with the additional one to set the key
        new_commands = list()
        for command in commands:
            if command.key == self._protocol.disable_retina_key:
                # This has to be stored so that the payload can be updated
                self.__new_key_command = self._protocol.set_retina_key(0)
                new_commands.append(self.__new_key_command)
            new_commands.append(command)
        return new_commands

    def _update_new_key_payload(self):
        vertex = list(self.__graph_mapper.get_machine_vertices(self))[0]
        key = self.__routing_infos.get_first_key_from_pre_vertex(
            vertex, SPIKE_PARTITION_ID)
        self.__new_key_command.payload = key
