"""
SpikeSourceArray
"""
from spynnaker.pyNN.utilities import constants

from spinn_front_end_common.abstract_models\
    .abstract_outgoing_edge_same_contiguous_keys_restrictor\
    import AbstractOutgoingEdgeSameContiguousKeysRestrictor
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.models.spike_source.spike_source_array_partitioned_vertex\
    import SpikeSourceArrayPartitionedVertex
from spynnaker.pyNN.buffer_management.storage_objects.buffered_sending_region\
    import BufferedSendingRegion
from spynnaker.pyNN.buffer_management.buffer_manager import BufferManager

from spinn_front_end_common.utilities import constants as \
    front_end_common_constants
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_iptag_constraint\
    import TagAllocatorRequireIptagConstraint

from data_specification.data_specification_generator\
    import DataSpecificationGenerator

from spinnman.messages.eieio.command_messages.event_stop_request\
    import EventStopRequest

from enum import Enum
import logging
import sys

logger = logging.getLogger(__name__)


class SpikeSourceArray(AbstractDataSpecableVertex,
                       AbstractPartitionableVertex,
                       AbstractOutgoingEdgeSameContiguousKeysRestrictor):

    CORE_APP_IDENTIFIER = (front_end_common_constants
                           .SPIKE_INJECTOR_CORE_APPLICATION_ID)
    _CONFIGURATION_REGION_SIZE = 36

    # limited to the n of the x,y,p,n key format
    _model_based_max_atoms_per_core = sys.maxint

    _SPIKE_SOURCE_REGIONS = Enum(
        value="_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('CONFIGURATION_REGION', 1),
               ('SPIKE_DATA_REGION', 2)])

    def __init__(
            self, n_neurons, spike_times, machine_time_step, spikes_per_second,
            ring_buffer_sigma, timescale_factor, port=None, tag=None,
            ip_address=None, board_address=None,
            max_on_chip_memory_usage_for_spikes_in_bytes=None,
            constraints=None, label="SpikeSourceArray"):
        if ip_address is None:
            ip_address = config.get("Buffers", "receive_buffer_host")
        if port is None:
            port = config.getint("Buffers", "receive_buffer_port")

        AbstractDataSpecableVertex.__init__(
            self, machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)
        AbstractPartitionableVertex.__init__(
            self, n_atoms=n_neurons, label=label,
            max_atoms_per_core=self._model_based_max_atoms_per_core,
            constraints=constraints)
        AbstractOutgoingEdgeSameContiguousKeysRestrictor.__init__(self)
        self._spike_times = spike_times
        self._max_on_chip_memory_usage_for_spikes = \
            max_on_chip_memory_usage_for_spikes_in_bytes
        self._threshold_for_reporting_bytes_written = 0

        self.add_constraint(TagAllocatorRequireIptagConstraint(
            ip_address, port, strip_sdp=True, board_address=board_address,
            tag_id=tag))

        if self._max_on_chip_memory_usage_for_spikes is None:
            self._max_on_chip_memory_usage_for_spikes = 8 * 1024 * 1024

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
        Return a string representing a label for this class.
        """
        return "SpikeSourceArray"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """

        :param new_value:
        :return:
        """
        SpikeSourceArray._model_based_max_atoms_per_core = new_value

    def create_subvertex(self, vertex_slice, resources_required, label=None,
                         constraints=list()):
        send_buffer = self._get_spike_send_buffer(vertex_slice)
        partitioned_vertex = SpikeSourceArrayPartitionedVertex(
            {SpikeSourceArray._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value:
                send_buffer}, resources_required, label, constraints)
        return partitioned_vertex

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
        send_buffer = None
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if key not in self._send_buffers:
            send_buffer = BufferedSendingRegion()
            if isinstance(self._spike_times[0], list):

                # This is in SpiNNaker 'list of lists' format:
                for neuron in range(vertex_slice.lo_atom,
                                    vertex_slice.hi_atom + 1):
                    for timeStamp in sorted(self._spike_times[neuron]):
                        time_stamp_in_ticks = int((timeStamp * 1000.0) /
                                                  self._machine_time_step)
                        send_buffer.add_key(time_stamp_in_ticks, neuron)
            else:

                # This is in official PyNN format, all neurons use the
                # same list:
                neuron_list = range(vertex_slice.lo_atom,
                                    vertex_slice.hi_atom + 1)
                for timeStamp in sorted(self._spike_times):
                    time_stamp_in_ticks = int((timeStamp * 1000.0) /
                                              self._machine_time_step)

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

    def _reserve_memory_regions(self, spec, spike_region_size):
        """ Reserve memory for the system, indices and spike data regions.
            The indices region will be copied to DTCM by the executable.
        """
        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value,
            size=constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4,
            label='systemInfo')

        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.CONFIGURATION_REGION.value,
            size=self._CONFIGURATION_REGION_SIZE, label='configurationRegion')

        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value,
            size=spike_region_size, label='SpikeDataRegion', empty=True)

    def _write_setup_info(self, spec, spike_buffer_region_size, ip_tags):
        """
        Write information used to control the simulation and gathering of
        results. Currently, this means the flag word used to signal whether
        information on neuron firing and neuron potential is either stored
        locally in a buffer or passed out of the simulation for storage/display
        as the simulation proceeds.

        The format of the information is as follows:
        Word 0: Flags selecting data to be gathered during simulation.
            Bit 0: Record spike history
            Bit 1: Record neuron potential
            Bit 2: Record gsyn values
            Bit 3: Reserved
            Bit 4: Output spike history on-the-fly
            Bit 5: Output neuron potential
            Bit 6: Output spike rate
        """
        self._write_basic_setup_info(
            spec, SpikeSourceArray.CORE_APP_IDENTIFIER,
            self._SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)

        spec.switch_write_focus(
            region=self._SPIKE_SOURCE_REGIONS.CONFIGURATION_REGION.value)

        # write configs for reverse ip tag
        # NOTE
        # as the packets are formed in the buffers, and that its a spike source
        # array, and shouldn't have injected packets, no config should be
        # required for it to work. the packet format will override these anyhow
        # END NOTE
        spec.write_value(data=0)  # prefix value
        spec.write_value(data=0)  # prefix
        spec.write_value(data=0)  # key left shift
        spec.write_value(data=0)  # add key check
        spec.write_value(data=0)  # key for transmitting
        spec.write_value(data=0)  # mask for transmitting

        # write configs for buffers
        spec.write_value(data=spike_buffer_region_size)
        spec.write_value(data=self._threshold_for_reporting_bytes_written)

        ip_tag = iter(ip_tags).next()
        spec.write_value(data=ip_tag.tag)

    # inherited from dataspecable vertex
    def generate_data_spec(
            self, subvertex, placement, subgraph, graph, routing_info,
            hostname, graph_mapper, report_folder, ip_tags, reverse_ip_tags,
            write_text_specs, application_run_time_folder):
        """
        Model-specific construction of the data blocks necessary to build a
        single SpikeSource Array on one core.
        :param subvertex:
        :param placement:
        :param subgraph:
        :param graph:
        :param routing_info:
        :param hostname:
        :param graph_mapper:
        :param report_folder:
        :param ip_tags:
        :param reverse_ip_tags:
        :param write_text_specs:
        :param application_run_time_folder:
        :return:
        """
        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder,
                write_text_specs, application_run_time_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        spec.comment("\n*** Spec for SpikeSourceArray Instance ***\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        spec.comment("\nReserving memory space for spike data region:\n\n")
        spike_buffer = self._get_spike_send_buffer(
            graph_mapper.get_subvertex_slice(subvertex))
        self._reserve_memory_regions(spec, spike_buffer.buffer_size)

        self._write_setup_info(
            spec, spike_buffer.buffer_size, ip_tags)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def get_binary_file_name(self):
        """

        :return:
        """
        return "reverse_iptag_multicast_source.aplx"

    # inherited from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice:
        :param graph:
        :return:
        """
        return 0

    def get_sdram_usage_for_atoms(self, vertex_slice, vertex_in_edges):
        """ calculates the total sdram usage of the spike source array. If the
        memory requirement is beyond what is deemed to be the usage of the
        processor, then it executes a buffered format.

        :param vertex_slice:
        :param vertex_in_edges:
        :return:
        """
        send_buffer = self._get_spike_send_buffer(vertex_slice)
        send_size = send_buffer.buffer_size
        return ((constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4) +
                SpikeSourceArray._CONFIGURATION_REGION_SIZE + send_size)

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice:
        :param graph:
        :return:
        """
        return 0

    def is_data_specable(self):
        """
        helper method for isinstance
        :return:
        """
        return True
