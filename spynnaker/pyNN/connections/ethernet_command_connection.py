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

from spinn_front_end_common.abstract_models import (
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.utilities.constants import NOTIFY_PORT
from spinn_front_end_common.utilities.database import DatabaseConnection


class EthernetCommandConnection(DatabaseConnection):
    """ A connection that can send commands to a device at the start and end\
        of a simulation
    """
    __slots__ = [
        "__command_containers",
        "__translator"]

    def __init__(
            self, translator, command_containers=None, local_host=None,
            local_port=NOTIFY_PORT):
        """
        :param AbstractEthernetTranslator translator:
            A translator of multicast commands to device commands
        :param command_containers:
            A list of vertices that have commands to be sent at the start \
            and end of simulation
        :type command_containers:
            list(~spinn_front_end_common.abstract_models.AbstractSendMeMulticastCommandsVertex)
        :param str local_host:
            The optional host to listen on for the start/resume message
        :param int local_port:
            The optional port to listen on for the stop/pause message
        """

        super().__init__(
            start_resume_callback_function=self._start_resume_callback,
            stop_pause_callback_function=self._stop_pause_callback,
            local_host=local_host, local_port=local_port)

        self.__command_containers = list()
        if command_containers is not None:
            for command_container in command_containers:
                self.add_command_container(command_container)
        self.__translator = translator

    def add_command_container(self, command_container):
        """ Add a command container.

        :param command_container:
            A vertex that has commands to be sent at the start and end of \
            simulation
        :type command_container:
            ~spinn_front_end_common.abstract_models.AbstractSendMeMulticastCommandsVertex
        """
        if not isinstance(
                command_container, AbstractSendMeMulticastCommandsVertex):
            raise TypeError(
                "Each command container must be an instance of"
                " AbstractSendMeMulticastCommandsVertex")
        if command_container.timed_commands:
            raise TypeError("Timed commands cannot be handled by this class")
        self.__command_containers.append(command_container)

    def _start_resume_callback(self):
        # Send commands from each command container
        for command_container in self.__command_containers:
            for command in command_container.start_resume_commands:
                self.__translator.translate_control_packet(command)

    def _stop_pause_callback(self):
        # Send commands from each command container
        for command_container in self.__command_containers:
            for command in command_container.pause_stop_commands:
                self.__translator.translate_control_packet(command)
