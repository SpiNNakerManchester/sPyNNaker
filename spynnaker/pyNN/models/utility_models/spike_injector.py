from pacman.model.decorators import overrides
from pacman.model.constraints.key_allocator_constraints \
    import ContiguousKeyRangeContraint
from spinn_front_end_common.abstract_models \
    import AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.utility_models import \
    ReverseIpTagMultiCastSource, ReverseIPTagMulticastSourceMachineVertex
from spinn_front_end_common.utilities.globals_variables import get_simulator

from spynnaker.pyNN.models.common \
    import AbstractSpikeRecordable, EIEIOSpikeRecorder
from spynnaker.pyNN.utilities.constants import \
    EIEIO_BUFFER_SIZE_BEFORE_RECEIVE, EIEIO_SPIKE_BUFFER_SIZE_BUFFERING_OUT


class SpikeInjector(ReverseIpTagMultiCastSource,
                    AbstractProvidesOutgoingPartitionConstraints,
                    AbstractSpikeRecordable):
    """ An Injector of Spikes for PyNN populations.  This only allows the user\
        to specify the virtual_key of the population to identify the population
    """

    default_parameters = {
        'label': "spikeInjector", 'port': None, 'virtual_key': None}

    _REGIONS = ReverseIPTagMulticastSourceMachineVertex._REGIONS

    def __init__(
            self, n_neurons, label=default_parameters['label'],
            port=default_parameters['port'],
            virtual_key=default_parameters['virtual_key'],
            spike_buffer_max_size=EIEIO_SPIKE_BUFFER_SIZE_BUFFERING_OUT,
            buffer_size_before_receive=EIEIO_BUFFER_SIZE_BEFORE_RECEIVE):

        ReverseIpTagMultiCastSource.__init__(
            self, n_keys=n_neurons, label=label, receive_port=port,
            virtual_key=virtual_key, reserve_reverse_ip_tag=True)

        AbstractProvidesOutgoingPartitionConstraints.__init__(self)

        # Set up for recording
        self._spike_recorder = EIEIOSpikeRecorder()
        self._spike_buffer_max_size = spike_buffer_max_size
        self._buffer_size_before_receive = buffer_size_before_receive

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self._spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(self, new_state=True):  # @UnusedVariable
        config = get_simulator().config
        ip_address = config.get("Buffers", "receive_buffer_host")
        port = config.get("Buffers", "receive_buffer_port")
        self.enable_recording(
            ip_address, port, None, None,
            self._spike_buffer_max_size, self._buffer_size_before_receive)
        self._spike_recorder.record = True

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager,  # @UnusedVariable
            machine_time_step):
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        buffer_manager = next(iter(subvertices)).buffer_manager
        return self._spike_recorder.get_spikes(
            self.label, buffer_manager,
            SpikeInjector._REGIONS.RECORDING_BUFFER.value,
            SpikeInjector._REGIONS.RECORDING_BUFFER_STATE.value,
            placements, graph_mapper, self,
            lambda subvertex: subvertex.virtual_key,
            machine_time_step)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        constraints = ReverseIpTagMultiCastSource\
            .get_outgoing_partition_constraints(self, partition)
        constraints.append(ContiguousKeyRangeContraint())
        return constraints
