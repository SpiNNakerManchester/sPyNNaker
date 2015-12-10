# spynnaker imports
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_mappable \
    import AbstractMappable
from spynnaker.pyNN.models.common.simple_population_settable \
    import SimplePopulationSettable
from spynnaker.pyNN.models.common.eieio_spike_recorder \
    import EIEIOSpikeRecorder
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.utilities.conf import config

# spinn front end common imports
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints
from spinn_front_end_common.interface.\
    abstract_resetable_for_run_interface import \
    AbstractResetableForRunInterface
from spinn_front_end_common.abstract_models.\
    abstract_uses_memory_mallocs import \
    AbstractPartitionableUsesMemoryMallocs
from spinn_front_end_common.utility_models.reverse_ip_tag_multi_cast_source \
    import ReverseIpTagMultiCastSource
from spinn_front_end_common.utility_models\
    .reverse_ip_tag_multicast_source_partitioned_vertex \
    import ReverseIPTagMulticastSourcePartitionedVertex


# general imports
import logging
import sys

logger = logging.getLogger(__name__)


class SpikeSourceArray(
        ReverseIpTagMultiCastSource, AbstractSpikeRecordable,
        AbstractResetableForRunInterface, SimplePopulationSettable,
        AbstractMappable):
    """ Model for play back of spikes
    """

    _model_based_max_atoms_per_core = sys.maxint

    def __init__(
            self, n_neurons, spike_times, machine_time_step, timescale_factor,
            port=None, tag=None, ip_address=None, board_address=None,
            max_on_chip_memory_usage_for_spikes_in_bytes=(
                constants.SPIKE_BUFFER_SIZE_BUFFERING_IN),
            space_before_notification=640,
            constraints=None, label="SpikeSourceArray",
            spike_recorder_buffer_size=(
                constants.EIEIO_SPIKE_BUFFER_SIZE_BUFFERING_OUT),
            buffer_size_before_receive=(
                constants.EIEIO_BUFFER_SIZE_BEFORE_RECEIVE)):
        self._ip_address = ip_address
        if ip_address is None:
            self._ip_address = config.get("Buffers", "receive_buffer_host")
        self._port = port
        if port is None:
            self._port = config.getint("Buffers", "receive_buffer_port")

        ReverseIpTagMultiCastSource.__init__(
            self, n_keys=n_neurons, machine_time_step=machine_time_step,
            timescale_factor=timescale_factor, label=label,
            constraints=constraints,
            max_atoms_per_core=(SpikeSourceArray.
                                _model_based_max_atoms_per_core),
            board_address=board_address,
            receive_port=None, receive_sdp_port=None, receive_tag=None,
            virtual_key=None, prefix=None, prefix_type=None, check_keys=False,
            send_buffer_times=spike_times,
            send_buffer_max_space=max_on_chip_memory_usage_for_spikes_in_bytes,
            send_buffer_space_before_notify=space_before_notification,
            send_buffer_notification_ip_address=self._ip_address,
            send_buffer_notification_port=self._port,
            send_buffer_notification_tag=tag)
        AbstractSpikeRecordable.__init__(self)
        AbstractProvidesOutgoingEdgeConstraints.__init__(self)
        AbstractResetableForRunInterface.__init__(self)
        SimplePopulationSettable.__init__(self)
        AbstractMappable.__init__(self)
        AbstractPartitionableUsesMemoryMallocs.__init__(self)


        # handle recording
        self._spike_recorder = EIEIOSpikeRecorder(machine_time_step)
        self._spike_recorder_buffer_size = spike_recorder_buffer_size
        self._buffer_size_before_receive = buffer_size_before_receive

        self._requires_mapping = True

    @property
    def requires_mapping(self):
        return self._requires_mapping

    def mark_no_changes(self):
        self._requires_mapping = False

    @property
    def spike_times(self):
        """
        property for the spike times of the spike soruce array
        :return:
        """
        return self._send_buffer_times

    @spike_times.setter
    def spike_times(self, spike_times):
        """
        setter for the spike soruce array's spike times. Not a extend, but an
         actual change
        :param spike_times:
        :return:
        """
        self._send_buffer_times = spike_times

    # @implements AbstractSpikeRecordable.is_recording_spikes
    def is_recording_spikes(self):
        """
        helper method fro chekcing if spikes are being stored
        :return:
        """
        return self._spike_recorder.record

    # @implements AbstractSpikeRecordable.set_recording_spikes
    def set_recording_spikes(self):
        """
        sets the recoridng flags
        :return:
        """
        self.enable_recording(
            self._ip_address, self._port, self._board_address,
            self._send_buffer_notification_tag,
            self._spike_recorder_buffer_size,
            self._buffer_size_before_receive)
        self._spike_recorder.record = True
        self._change_requires_mapping = True

    # @implements AbstractSpikeRecordable.delete_spikes
    def delete_spikes(self):
        self._spike_recorder.reset()

    def get_spikes(self, placements, graph_mapper):
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        buffer_manager = next(iter(subvertices)).buffer_manager
        return self._spike_recorder.get_spikes(
            self.label, buffer_manager,
            (ReverseIPTagMulticastSourcePartitionedVertex.
             _REGIONS.RECORDING_BUFFER.value),
            (ReverseIPTagMulticastSourcePartitionedVertex.
             _REGIONS.RECORDING_BUFFER_STATE.value),
            placements, graph_mapper, self,
            lambda subvertex: subvertex.virtual_key)

    @property
    def model_name(self):
        """ A string representing a label for this class.
        """
        return "SpikeSourceArray"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """

        :param new_value:
        :return:
        """
        SpikeSourceArray._model_based_max_atoms_per_core = new_value
