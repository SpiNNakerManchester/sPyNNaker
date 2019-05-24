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
    __slots__ = [
        "__fixed_key",
        "__fixed_mask",
        "__polarity",
        "__position"]

    # key codes for the robot retina
    MANAGEMENT_BIT = 0x400
    MANAGEMENT_MASK = 0xFFFFF800
    LEFT_RETINA_ENABLE = 0x45
    RIGHT_RETINA_ENABLE = 0x46
    LEFT_RETINA_DISABLE = 0x45
    RIGHT_RETINA_DISABLE = 0x46
    LEFT_RETINA_KEY_SET = 0x43
    RIGHT_RETINA_KEY_SET = 0x44

    UP_POLARITY = "UP"
    DOWN_POLARITY = "DOWN"
    MERGED_POLARITY = "MERGED"

    LEFT_RETINA = "LEFT"
    RIGHT_RETINA = "RIGHT"
    _RETINAS = frozenset((LEFT_RETINA, RIGHT_RETINA))

    default_parameters = {
        'label': "MunichRetinaDevice",
        'polarity': None,
        'board_address': None}

    def __init__(
            self, retina_key, spinnaker_link_id, position,
            label=None,
            polarity=default_parameters['polarity'],
            board_address=default_parameters['board_address']):
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
        self.__position = position

        super(MunichRetinaDevice, self).__init__(
            n_atoms=fixed_n_neurons, spinnaker_link_id=spinnaker_link_id,
            max_atoms_per_core=fixed_n_neurons, label=label,
            board_address=board_address)

        if self.__position not in self._RETINAS:
            raise SpynnakerException(
                "The external Retina does not recognise this _position")

    def get_outgoing_partition_constraints(self, partition):
        return [FixedKeyAndMaskConstraint([
            BaseKeyAndMask(self.__fixed_key, self.__fixed_mask)])]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        commands = list()
        # change the retina key it transmits with
        # (based off if its right or left)
        if self.__position == self.RIGHT_RETINA:
            key_set_command = self.MANAGEMENT_BIT | self.RIGHT_RETINA_KEY_SET
        else:
            key_set_command = self.MANAGEMENT_BIT | self.LEFT_RETINA_KEY_SET

        # to ensure populations receive the correct packets, this needs to be
        # different based on which retina
        key_set_payload = (self._virtual_chip_x << 24 |
                           self._virtual_chip_y << 16)

        commands.append(MultiCastCommand(
            key=key_set_command, payload=key_set_payload, repeat=5,
            delay_between_repeats=1000))

        # make retina enabled (dependent on if its a left or right retina
        if self.__position == self.RIGHT_RETINA:
            enable_command = self.MANAGEMENT_BIT | self.RIGHT_RETINA_ENABLE
        else:
            enable_command = self.MANAGEMENT_BIT | self.LEFT_RETINA_ENABLE
        commands.append(MultiCastCommand(
            key=enable_command, payload=1, repeat=5,
            delay_between_repeats=1000))

        return commands

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        # disable retina
        if self.__position == self.RIGHT_RETINA:
            disable_command = self.MANAGEMENT_BIT | self.RIGHT_RETINA_DISABLE
        else:
            disable_command = self.MANAGEMENT_BIT | self.LEFT_RETINA_DISABLE

        return [MultiCastCommand(
            disable_command, payload=0, repeat=5, delay_between_repeats=1000)]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []
