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
from spinn_front_end_common.interface.buffer_management.\
    storage_objects.buffered_sending_region import \
    BufferedSendingRegion
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints
from spinn_front_end_common.interface.\
    abstract_resetable_for_run_interface import \
    AbstractResetableForRunInterface
from spinn_front_end_common.utility_models.reverse_ip_tag_multi_cast_source \
    import ReverseIpTagMultiCastSource
from spinn_front_end_common.utility_models\
    .reverse_ip_tag_multicast_source_partitioned_vertex \
    import ReverseIPTagMulticastSourcePartitionedVertex
from spinn_front_end_common.utilities import constants as \
    front_end_common_constants
from spinn_front_end_common.utilities import exceptions

# general imports
import logging
import sys
import math

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

        # handle recording
        self._spike_recorder = EIEIOSpikeRecorder(machine_time_step)
        self._spike_recorder_buffer_size = spike_recorder_buffer_size
        self._buffer_size_before_receive = buffer_size_before_receive

        # Keep track of any previously generated buffers
        self._send_buffers = dict()
        self._spike_recording_region_size = None
        self._partitioned_vertices = list()
        self._partitioned_vertices_current_max_buffer_size = dict()

        # used for reset and rerun
        self._requires_mapping = True
        self._change_requires_mapping = True
        self._last_runtime_position = 0

        self._max_on_chip_memory_usage_for_spikes = \
            max_on_chip_memory_usage_for_spikes_in_bytes
        self._space_before_notification = space_before_notification
        if self._max_on_chip_memory_usage_for_spikes is None:
            self._max_on_chip_memory_usage_for_spikes = \
                front_end_common_constants.MAX_SIZE_OF_BUFFERED_REGION_ON_CHIP

        # check the values do not conflict with chip memory limit
        if self._max_on_chip_memory_usage_for_spikes < 0:
            raise exceptions.ConfigurationException(
                "The memory usage on chip is either beyond what is supportable"
                " on the spinnaker board being supported or you have requested"
                " a negative value for a memory usage. Please correct and"
                " try again")

        if (self._max_on_chip_memory_usage_for_spikes <
                self._space_before_notification):
            self._space_before_notification =\
                self._max_on_chip_memory_usage_for_spikes


    def get_number_of_mallocs_used_by_dsg(self, vertex_slice, in_edges):
        mallocs = \
            ReverseIpTagMultiCastSource.get_number_of_mallocs_used_by_dsg(
                self, vertex_slice, in_edges)
        if config.getboolean("SpecExecution", "specExecOnHost"):
            return 1
        else:
            return mallocs

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

    # @implements AbstractPopulationSettable.update_parameters
    def update_parameters(self, txrx, vertex_slice):
        # there is nothing to send this way.
        pass

    def get_spikes(self, placements, graph_mapper, buffer_manager):
        return self._spike_recorder.get_spikes(
            self.label, buffer_manager,
            (ReverseIPTagMulticastSourcePartitionedVertex.
             REGIONS.RECORDING_BUFFER.value),
            (ReverseIPTagMulticastSourcePartitionedVertex.
             REGIONS.RECORDING_BUFFER_STATE.value),
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

    def _get_spike_send_buffer(self, vertex_slice):
        """
        spikeArray is a list with one entry per 'neuron'. The entry for
        one neuron is a list of times (in ms) when the neuron fires.
        We need to transpose this 'matrix' and get a list of firing neuron
        indices for each time tick:
        List can come in two formats (both now supported):
        1) Official PyNN format - single list that is used for all neurons
        2) SpiNNaker format - list of lists, one per neuron
        """
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if key not in self._send_buffers:

            send_buffer = BufferedSendingRegion(
                    self._max_on_chip_memory_usage_for_spikes)

            # translate spikes into buffer
            if hasattr(self._send_buffer_times, "__len__"):

                # This is in SpiNNaker 'list of lists' format:
                for neuron in range(vertex_slice.lo_atom,
                                    vertex_slice.hi_atom + 1):
                    for timeStamp in sorted(self._send_buffer_times[neuron]):
                        self._check_time_stamp(
                            send_buffer, timeStamp, self._machine_time_step,
                            self._no_machine_time_steps,
                            self._last_runtime_position,
                            (neuron - vertex_slice.lo_atom))
            else:

                # This is in official PyNN format, all neurons use the
                # same list:
                neuron_list = range(vertex_slice.n_atoms)
                for timeStamp in sorted(self._send_buffer_times):
                    self._check_time_stamp(
                        send_buffer, timeStamp, self._machine_time_step,
                        self._no_machine_time_steps,
                        self._last_runtime_position, neuron_list)

            self._send_buffers[key] = send_buffer
        else:
            send_buffer = self._send_buffers[key]
        return send_buffer

    @staticmethod
    def _check_time_stamp(
            send_buffer, time_stamp, machine_time_step, no_machine_time_steps,
            last_runtime_position, neuron_list):
        time_stamp_in_ticks = int(
            math.ceil((time_stamp * 1000.0) / machine_time_step))
        # deduce if the time stamp is within the time window of the simulation
        if last_runtime_position <= time_stamp_in_ticks < no_machine_time_steps:
            send_buffer.add_key(time_stamp_in_ticks, neuron_list)

    # @implements AbstractResetableForRunInterface.reset_for_run
    def reset_for_run(
            self, last_runtime_in_milliseconds, this_runtime_in_milliseconds):
        self._send_buffers.clear()
        self._last_runtime_position = last_runtime_in_milliseconds
        for (vertex_slice, partitioned_vertex) in self._partitioned_vertices:
            send_buffers = dict()
            send_buffers[
                ReverseIPTagMulticastSourcePartitionedVertex.
                REGIONS.SEND_BUFFER.value] = \
                self._get_spike_send_buffer(vertex_slice)
            partitioned_vertex.send_buffers = send_buffers

    def create_subvertex(self, vertex_slice, resources_required, label=None,
                         constraints=None):

        # map region id to the sned buffer for this partitioned vertex
        send_buffer = dict()
        send_buffers = self._get_spike_send_buffer(vertex_slice)
        send_buffer[
            ReverseIPTagMulticastSourcePartitionedVertex.REGIONS.
            SEND_BUFFER.value] = send_buffers
        send_buffer_times = send_buffers.timestamps

        # create spike times
        partitioned_vertex = ReverseIPTagMulticastSourcePartitionedVertex(
            n_keys=self.n_atoms, resources_required=resources_required,
            machine_time_step=self._machine_time_step,
            timescale_factor=self._timescale_factor, label=label,
            constraints=constraints,
            board_address=self._board_address,
            receive_port=self._receive_port,
            receive_sdp_port=self._receive_sdp_port,
            receive_tag=self._receive_tag,
            virtual_key=self._virtual_key, prefix=self._prefix,
            prefix_type=self._prefix_type, check_keys=self._check_keys,
            send_buffer_times=send_buffer_times,
            send_buffer_max_space=self._send_buffer_max_space,
            send_buffer_space_before_notify=(
                self._send_buffer_space_before_notify),
            send_buffer_notification_ip_address=(
                self._send_buffer_notification_ip_address),
            send_buffer_notification_port=self._send_buffer_notification_port,
            send_buffer_notification_tag=self._send_buffer_notification_tag)

        partitioned_vertex.set_no_machine_time_steps(
            self._no_machine_time_steps)
        if self._record_buffer_size > 0:
            partitioned_vertex.enable_recording(
                self._record_buffering_ip_address, self._record_buffering_port,
                self._record_buffering_board_address,
                self._record_buffering_tag, self._record_buffer_size,
                self._record_buffer_size_before_receive)

        self._partitioned_vertices.append((vertex_slice, partitioned_vertex))
        self._partitioned_vertices_current_max_buffer_size[
            partitioned_vertex] = send_buffers.max_buffer_size_possible
        return partitioned_vertex
