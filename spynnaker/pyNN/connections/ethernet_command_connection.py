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
            raise Exception(
                "Each command container must be an instance of"
                " AbstractSendMeMulticastCommandsVertex")
        if command_container.timed_commands:
            raise Exception("Timed commands cannot be handled by this class")
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
