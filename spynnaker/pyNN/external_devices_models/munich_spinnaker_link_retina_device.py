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
from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyAndMaskConstraint)
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints,
    AbstractSendMeMulticastCommandsVertex)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spinn_front_end_common.utility_models import MultiCastCommand
from spynnaker.pyNN.exceptions import SpynnakerException

# robot with 7 7 1


def get_x_from_robot_retina(key):
    return (key >> 7) & 0x7f


def get_y_from_robot_retina(key):
    return key & 0x7f


def get_spike_value_from_robot_retina(key):
    return (key >> 14) & 0x1


class MunichRetinaDevice(
        ApplicationSpiNNakerLinkVertex, AbstractSendMeMulticastCommandsVertex,
        AbstractProvidesOutgoingPartitionConstraints,
        ProvidesKeyToAtomMappingImpl):
    """ An Omnibot silicon retina device.
    """
    __slots__ = [
        "__fixed_key",
        "__fixed_mask",
        "__polarity",
        "__is_right"]

    # key codes for the robot retina
    _MANAGEMENT_BIT = 0x400
    _MANAGEMENT_MASK = 0xFFFFF800
    _LEFT_RETINA_ENABLE = 0x45
    _RIGHT_RETINA_ENABLE = 0x46
    _LEFT_RETINA_DISABLE = 0x45
    _RIGHT_RETINA_DISABLE = 0x46
    _LEFT_RETINA_KEY_SET = 0x43
    _RIGHT_RETINA_KEY_SET = 0x44

    UP_POLARITY = "UP"
    DOWN_POLARITY = "DOWN"
    MERGED_POLARITY = "MERGED"

    #: Select the left retina
    LEFT_RETINA = "LEFT"
    #: Select the right retina
    RIGHT_RETINA = "RIGHT"
    _RETINAS = frozenset((LEFT_RETINA, RIGHT_RETINA))

    default_parameters = {
        'label': "MunichRetinaDevice",
        'polarity': None,
        'board_address': None}

    def __init__(
            self, retina_key, spinnaker_link_id, position,
            label=default_parameters['label'],
            polarity=default_parameters['polarity'],
            board_address=default_parameters['board_address']):
        """
        :param int retina_key:
        :param int spinnaker_link_id:
            The SpiNNaker link to which the retina is connected
        :param str position: ``LEFT`` or ``RIGHT``
        :param str label:
        :param str polarity: ``UP``, ``DOWN`` or ``MERGED``
        :param board_address:
        :type board_address: str or None
        """
        # pylint: disable=too-many-arguments
        if polarity is None:
            polarity = MunichRetinaDevice.MERGED_POLARITY

        self.__fixed_key = (retina_key & 0xFFFF) << 16
        self.__fixed_mask = 0xFFFF8000
        if polarity == MunichRetinaDevice.UP_POLARITY:
            self.__fixed_key |= 0x4000

        if polarity == MunichRetinaDevice.MERGED_POLARITY:
            # There are 128 x 128 retina "pixels" x 2 polarities
            fixed_n_neurons = 128 * 128 * 2
        else:
            # There are 128 x 128 retina "pixels"
            fixed_n_neurons = 128 * 128
            self.__fixed_mask = 0xFFFFC000

        self.__polarity = polarity
        if position not in self._RETINAS:
            raise SpynnakerException(
                "The external Retina does not recognise this position")
        self.__is_right = position == self.RIGHT_RETINA

        super().__init__(
            n_atoms=fixed_n_neurons, spinnaker_link_id=spinnaker_link_id,
            label=label, board_address=board_address)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [FixedKeyAndMaskConstraint([
            BaseKeyAndMask(self.__fixed_key, self.__fixed_mask)])]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        commands = list()
        # change the retina key it transmits with
        # (based off if its right or left)
        key_set_command = self._MANAGEMENT_BIT | (
            self._RIGHT_RETINA_KEY_SET if self.__is_right
            else self._LEFT_RETINA_KEY_SET)

        # to ensure populations receive the correct packets, this needs to be
        # different based on which retina
        key_set_payload = (1 << 24) if self.__is_right else 0

        commands.append(MultiCastCommand(
            key=key_set_command, payload=key_set_payload, repeat=5,
            delay_between_repeats=1000))

        # make retina enabled (dependent on if its a left or right retina
        enable_command = self._MANAGEMENT_BIT | (
            self._RIGHT_RETINA_ENABLE if self.__is_right
            else self._LEFT_RETINA_ENABLE)
        commands.append(MultiCastCommand(
            key=enable_command, payload=1, repeat=5,
            delay_between_repeats=1000))

        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        # disable retina
        disable_command = self._MANAGEMENT_BIT | (
            self._RIGHT_RETINA_DISABLE if self.__is_right
            else self._LEFT_RETINA_DISABLE)

        return [MultiCastCommand(
            disable_command, payload=0, repeat=5, delay_between_repeats=1000)]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
