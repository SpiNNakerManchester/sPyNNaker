from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject, supports_injection
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.external_devices_models.push_bot \
    import AbstractPushBotRetinaDevice

import logging

logger = logging.getLogger(__name__)


@supports_injection
class PushBotSpiNNakerLinkRetinaDevice(
        AbstractPushBotRetinaDevice, ApplicationSpiNNakerLinkVertex):
    __slots__ = [
        "_graph_mapper",
        "_new_key_command",
        "_routing_infos"]

    default_parameters = {'label': None, 'board_address': None}

    def __init__(
            self, n_neurons, spinnaker_link_id, protocol, resolution,
            board_address=default_parameters['board_address'],
            label=default_parameters['label']):
        # pylint: disable=too-many-arguments
        if n_neurons is not None and n_neurons != resolution.value.n_neurons:
            logger.warn(
                "The specified number of neurons for the push bot retina"
                " device has been ignored %d will be used instead",
                resolution.value.n_neurons)

        AbstractPushBotRetinaDevice.__init__(self, protocol, resolution)
        ApplicationSpiNNakerLinkVertex.__init__(
            self, spinnaker_link_id=spinnaker_link_id,
            n_atoms=resolution.value.n_neurons,
            board_address=board_address, label=label)

        # stores for the injection aspects
        self._graph_mapper = None
        self._routing_infos = None
        self._new_key_command = None

    @inject("MemoryGraphMapper")
    def graph_mapper(self, graph_mapper):
        self._graph_mapper = graph_mapper
        if self._routing_infos is not None:
            self._update_new_key_payload()

    @inject("MemoryRoutingInfos")
    def routing_info(self, routing_info):
        self._routing_infos = routing_info
        if self._graph_mapper is not None:
            self._update_new_key_payload()

    @property
    @overrides(AbstractPushBotRetinaDevice.start_resume_commands)
    def start_resume_commands(self):
        # Note this is not undefined, it is just a property so, it can't
        # be statically analysed
        commands = AbstractPushBotRetinaDevice\
            .start_resume_commands.fget(self)  # @UndefinedVariable

        # Update the commands with the additional one to set the key
        new_commands = list()
        for command in commands:
            if command.key == self._protocol.disable_retina_key:
                # This has to be stored so that the payload can be updated
                self._new_key_command = self._protocol.set_retina_key(0)
                new_commands.append(self._new_key_command)
            new_commands.append(command)
        return new_commands

    def _update_new_key_payload(self):
        vertex = list(self._graph_mapper.get_machine_vertices(self))[0]
        key = self._routing_infos.get_first_key_from_pre_vertex(
            vertex, SPIKE_PARTITION_ID)
        self._new_key_command.payload = key
