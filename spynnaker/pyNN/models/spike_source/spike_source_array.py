"""
SpikeSourceArray
"""

# spynnaker imports
from spinn_front_end_common.abstract_models\
    .abstract_outgoing_edge_same_contiguous_keys_restrictor\
    import AbstractOutgoingEdgeSameContiguousKeysRestrictor
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.models.spike_source.spike_source_array_partitioned_vertex\
    import SpikeSourceArrayPartitionedVertex
from spinn_front_end_common.interface.buffer_management.storage_objects\
    .buffered_sending_region import BufferedSendingRegion
from spinn_front_end_common.interface.buffer_management.buffer_manager \
    import BufferManager

# spinn front end common imports
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities import constants as \
    front_end_common_constants
from spinn_front_end_common.utility_models\
    .reverse_ip_tag_multicast_source_partitionable_vertex \
    import ReverseIPTagMulticastSourcePartitionableVertex

# spinnman imports
from spinnman.messages.eieio.command_messages.event_stop_request\
    import EventStopRequest

# general imports
import logging
import sys
import math

logger = logging.getLogger(__name__)


class SpikeSourceArray(ReverseIPTagMulticastSourcePartitionableVertex,
                       AbstractOutgoingEdgeSameContiguousKeysRestrictor):
    """
    model for play back of spikes
    """

    _model_based_max_atoms_per_core = sys.maxint

    def __init__(
            self, n_keys, spike_times, machine_time_step, spikes_per_second,
            ring_buffer_sigma, timescale_factor, port=None, tag=None,
            ip_address=None, board_address=None,
            max_on_chip_memory_usage_for_spikes_in_bytes=None,
            space_before_notification=640,
            constraints=None, label="SpikeSourceArray"):

        if ip_address is None:
            ip_address = config.get("Buffers", "receive_buffer_host")
        if port is None:
            port = config.getint("Buffers", "receive_buffer_port")

        ReverseIPTagMulticastSourcePartitionableVertex.__init__(
            self, label, n_keys, virtual_key=None, buffer_space=0,
            constraints)
        AbstractOutgoingEdgeSameContiguousKeysRestrictor.__init__(self)
        self._spike_times = spike_times
        self._max_on_chip_memory_usage_for_spikes = \
            max_on_chip_memory_usage_for_spikes_in_bytes
        self._space_before_notification = space_before_notification

        if self._max_on_chip_memory_usage_for_spikes is None:
            self._max_on_chip_memory_usage_for_spikes = \
                front_end_common_constants.MAX_SIZE_OF_BUFFERED_REGION_ON_CHIP

        # check the values do not conflict with chip memory limit
        if self._max_on_chip_memory_usage_for_spikes < 0:
            raise ConfigurationException(
                "The memory usage on chip is either beyond what is supportable"
                " on the spinnaker board being supported or you have requested"
                " a negative value for a memory usage. Please correct and"
                " try again")

        # Keep track of any previously generated buffers
        self._send_buffers = dict()

    @property
    def model_name(self):
        """
        """
        return "SpikeSourceArray"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """
        """
        SpikeSourceArray._model_based_max_atoms_per_core = new_value

    def create_subvertex(self, vertex_slice, resources_required, label=None,
                         constraints=list()):
        """
        """
        # map region id to the sned buffer for this partitioned vertex
        send_buffer = dict()
        send_buffer[self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value] =\
            self._get_spike_send_buffer(vertex_slice)
        # create and return the partitioned vertex
        return SpikeSourceArrayPartitionedVertex(
            send_buffer, resources_required, label, constraints)

    def _get_spike_send_buffer(self, vertex_slice):
        """
        """
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if key not in self._send_buffers:
            send_buffer = BufferedSendingRegion()
            if isinstance(self._spike_times[0], list):

                # This is in SpiNNaker 'list of lists' format:
                for neuron in range(vertex_slice.lo_atom,
                                    vertex_slice.hi_atom + 1):
                    for timeStamp in sorted(self._spike_times[neuron]):
                        time_stamp_in_ticks = int(
                            math.ceil((timeStamp * 1000.0) /
                                      self._machine_time_step))
                        send_buffer.add_key(time_stamp_in_ticks,
                                            neuron - vertex_slice.lo_atom)
            else:

                # This is in official PyNN format, all neurons use the
                # same list:
                neuron_list = range(vertex_slice.n_atoms)
                for timeStamp in sorted(self._spike_times):
                    time_stamp_in_ticks = int(
                        math.ceil((timeStamp * 1000.0) /
                                  self._machine_time_step))

                    # add to send_buffer collection
                    send_buffer.add_keys(time_stamp_in_ticks, neuron_list)

            # Update the size
            total_size = 0
            for timestamp in send_buffer.timestamps:
                n_keys = send_buffer.get_n_keys(timestamp)
                total_size += BufferManager.get_n_bytes(n_keys)
            total_size += EventStopRequest.get_min_packet_length()
            if total_size > self._max_on_chip_memory_usage_for_spikes:
                total_size = self._max_on_chip_memory_usage_for_spikes
            send_buffer.buffer_size = total_size
            self._send_buffers[key] = send_buffer
        else:
            send_buffer = self._send_buffers[key]
        return send_buffer

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        """
        send_buffer = self._get_spike_send_buffer(vertex_slice)
        send_size = send_buffer.buffer_size
        return (ReverseIPTagMulticastSourcePartitionableVertex
                .get_sdram_usage_for_atoms(self, vertex_slice, graph) +
                send_size)
