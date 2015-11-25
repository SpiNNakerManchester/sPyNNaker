# spynnaker imports
from spynnaker.pyNN.models.common.eieio_spike_recorder \
    import EIEIOSpikeRecorder
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.utilities.conf import config

# spinn front end common imports
from spinn_front_end_common.utility_models.reverse_ip_tag_multi_cast_source \
    import ReverseIpTagMultiCastSource
from spinn_front_end_common.utility_models\
    .reverse_ip_tag_multicast_source_partitioned_vertex \
    import ReverseIPTagMulticastSourcePartitionedVertex


# general imports
import logging
import sys

logger = logging.getLogger(__name__)


class SpikeSourceArray(ReverseIpTagMultiCastSource, AbstractSpikeRecordable):
    """ Model for play back of spikes
    """

    _model_based_max_atoms_per_core = sys.maxint

    def __init__(
            self, n_neurons, spike_times, machine_time_step, timescale_factor,
            port=None, tag=None, ip_address=None, board_address=None,
            max_on_chip_memory_usage_for_spikes_in_bytes=1024 * 1024,
            space_before_notification=640,
            constraints=None, label="SpikeSourceArray",
            spike_recorder_buffer_size=1024 * 1024):
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

        # handle recording
        self._spike_recorder = EIEIOSpikeRecorder(machine_time_step)
        self._spike_recorder_buffer_size = spike_recorder_buffer_size

    @property
    def spike_times(self):
        return self._send_buffer_times

    @spike_times.setter
    def spike_times(self, spike_times):
        self._send_buffer_times = spike_times

    def is_recording_spikes(self):
        return self._spike_recorder.record

    def set_recording_spikes(self):
        self.enable_recording(
            self._ip_address, self._port, self._board_address,
            self._send_buffer_notification_tag,
            self._spike_recorder_buffer_size)
        self._spike_recorder.record = True

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

    def get_value(self, key):
        """ Get a property of the overall model
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise Exception("Population {} does not have parameter {}".format(
            self, key))

    def set_value(self, key, value):
        """ Set a property of the overall model
        :param key: the name of the param to change
        :param value: the value of the parameter to change
        """
        if hasattr(self, key):
            setattr(self, key, value)
            return
        raise Exception("Type {} does not have parameter {}".format(
            self._model_name, key))
