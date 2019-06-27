import logging
from spinn_utilities.overrides import overrides
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints)
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, EIEIOSpikeRecorder, SimplePopulationSettable)

logger = logging.getLogger(__name__)


class SpikeInjectorVertex(
        ReverseIpTagMultiCastSource,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractSpikeRecordable, SimplePopulationSettable):
    """ An Injector of Spikes for PyNN populations.  This only allows the user\
        to specify the virtual_key of the population to identify the population
    """
    __slots__ = [
        "__receive_port",
        "__requires_mapping",
        "__spike_recorder",
        "__virtual_key"]

    default_parameters = {
        'label': "spikeInjector", 'port': None, 'virtual_key': None}

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, label, constraints, port, virtual_key,
            reserve_reverse_ip_tag):
        # pylint: disable=too-many-arguments
        self.__requires_mapping = True
        self.__receive_port = None
        self.__virtual_key = None

        super(SpikeInjectorVertex, self).__init__(
            n_keys=n_neurons, label=label, receive_port=port,
            virtual_key=virtual_key,
            reserve_reverse_ip_tag=reserve_reverse_ip_tag,
            constraints=constraints)

        # Set up for recording
        self.__spike_recorder = EIEIOSpikeRecorder()

    @property
    def port(self):
        return self.__receive_port

    @port.setter
    def port(self, port):
        self.__receive_port = port

    @property
    def virtual_key(self):
        return self.__virtual_key

    @virtual_key.setter
    def virtual_key(self, virtual_key):
        self.__virtual_key = virtual_key

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported "
                           "so being ignored")
        if indexes is not None:
            logger.warning("Indexes currently not supported "
                           "so being ignored")
        self.enable_recording(new_state)
        self.__requires_mapping = not self.__spike_recorder.record
        self.__spike_recorder.record = new_state

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return get_simulator().machine_time_step

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        return self.__spike_recorder.get_spikes(
            self.label, buffer_manager,
            SpikeInjectorVertex.SPIKE_RECORDING_REGION_ID,
            placements, graph_mapper, self,
            lambda vertex:
                vertex.virtual_key
                if vertex.virtual_key is not None
                else 0,
            machine_time_step)

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        machine_vertices = graph_mapper.get_machine_vertices(self)
        for machine_vertex in machine_vertices:
            placement = placements.get_placement_of_vertex(machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeInjectorVertex.SPIKE_RECORDING_REGION_ID)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        constraints = ReverseIpTagMultiCastSource\
            .get_outgoing_partition_constraints(self, partition)
        constraints.append(ContiguousKeyRangeContraint())
        return constraints

    def describe(self):
        """
        Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
        will be returned.
        """

        parameters = dict()
        for parameter_name in self.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": "SpikeInjector",
            "default_parameters": self.default_parameters,
            "default_initial_values": self.default_parameters,
            "parameters": parameters,
        }
        return context
