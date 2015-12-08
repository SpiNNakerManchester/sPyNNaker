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
from spynnaker.pyNN.models.spike_source.spike_source_array_partitioned_vertex\
    import SpikeSourceArrayPartitionedVertex

# spinn front end common imports
from spinn_front_end_common.interface.buffer_management.storage_objects\
    .buffered_sending_region import BufferedSendingRegion
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities import constants as \
    front_end_common_constants
from spinn_front_end_common.interface.\
    abstract_resetable_for_run_interface import \
    AbstractResetableForRunInterface
from spinn_front_end_common.abstract_models.\
    abstract_uses_memory_mallocs import \
    AbstractPartitionableUsesMemoryMallocs

# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_iptag_constraint\
    import TagAllocatorRequireIptagConstraint
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint

# dsg imports
from data_specification.data_specification_generator\
    import DataSpecificationGenerator

# general imports
from enum import Enum
import logging
import sys
import math

logger = logging.getLogger(__name__)


class SpikeSourceArray(
        AbstractDataSpecableVertex, AbstractPartitionableVertex,
        AbstractSpikeRecordable, AbstractProvidesOutgoingEdgeConstraints,
        AbstractResetableForRunInterface, SimplePopulationSettable,
        AbstractMappable, AbstractPartitionableUsesMemoryMallocs):
    """
    model for play back of spikes
    """
    _DEFAULT_MALLOCS_USED = 3
    _CONFIGURATION_REGION_SIZE = 36
    # Space in case the buffering ends up pushing more packets than required
    _RECORD_OVERALLOCATION = 2000

    # limited to the n of the x,y,p,n key format
    _model_based_max_atoms_per_core = sys.maxint

    _SPIKE_SOURCE_REGIONS = Enum(
        value="_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('CONFIGURATION_REGION', 1),
               ('SPIKE_DATA_REGION', 2),
               ('SPIKE_DATA_RECORDED_REGION', 3)])

    def __init__(
            self, n_neurons, spike_times, machine_time_step, timescale_factor,
            port=None, tag=None, ip_address=None, board_address=None,
            max_on_chip_memory_usage_for_spikes_in_bytes=None,
            space_before_notification=640,
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
        AbstractSpikeRecordable.__init__(self)
        AbstractProvidesOutgoingEdgeConstraints.__init__(self)
        AbstractResetableForRunInterface.__init__(self)
        SimplePopulationSettable.__init__(self)
        AbstractMappable.__init__(self)
        AbstractPartitionableUsesMemoryMallocs.__init__(self)

        self._spike_times = spike_times
        self._max_on_chip_memory_usage_for_spikes = \
            max_on_chip_memory_usage_for_spikes_in_bytes
        self._space_before_notification = space_before_notification

        self.add_constraint(TagAllocatorRequireIptagConstraint(
            ip_address, port, strip_sdp=True, board_address=board_address,
            tag_id=tag))

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

        if (self._max_on_chip_memory_usage_for_spikes <
                self._space_before_notification):
            self._space_before_notification =\
                self._max_on_chip_memory_usage_for_spikes

        # Keep track of any previously generated buffers
        self._send_buffers = dict()
        self._spike_recording_region_size = None
        self._partitioned_vertices = list()
        self._partitioned_vertices_current_max_buffer_size = dict()

        # handle recording
        self._spike_recorder = EIEIOSpikeRecorder(machine_time_step)

        # counter of how many machien time steps the vertex has extracted
        self._extracted_machine_time_steps = 0
        self._last_runtime_position = 0
        self._spikes_cache_file = None

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
        return self._spike_times

    @spike_times.setter
    def spike_times(self, spike_times):
        """
        setter for the spike soruce array's spike times. Not a extend, but an
         actual change
        :param spike_times:
        :return:
        """
        self._spike_times = spike_times

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
        self._spike_recorder.record = True
        self._change_requires_mapping = True

    # @implements AbstractSpikeRecordable.delete_spikes
    def delete_spikes(self):
        self._spike_recorder.reset()

    def get_spikes(self, transceiver, n_machine_time_steps, placements,
                   graph_mapper, return_data=True):
        """
        gets spikes from the spike source array
        :param transceiver:
        :param n_machine_time_steps:
        :param placements:
        :param graph_mapper:
        :return:
        """
        return self._spike_recorder.get_spikes(
            self.label, transceiver,
            self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_RECORDED_REGION.value,
            n_machine_time_steps, placements, graph_mapper, self, return_data)

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

    def create_subvertex(self, vertex_slice, resources_required, label=None,
                         constraints=list()):
        """ Creates a partitioned vertex from a partitionable vertex
        :param vertex_slice: the slice of partitionable atoms that the new \
                partitioned vertex will contain
        :param resources_required: the resources used by the partitioned vertex
        :param label: the label of the partitioned vertex
        :param constraints: extra constraints added to the partitioned vertex
        :return: a partitioned vertex
        :rtype: SpikeSourceArrayPartitionedVertex
        """
        # map region id to the send buffer for this partitioned vertex
        send_buffer = dict()
        send_buffers = self._get_spike_send_buffer(vertex_slice)
        send_buffer[self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value] =\
            send_buffers
        # create and return the partitioned vertex
        partitioned_vertex = SpikeSourceArrayPartitionedVertex(
            send_buffer, resources_required, label, constraints)
        self._partitioned_vertices.append((vertex_slice, partitioned_vertex))
        self._partitioned_vertices_current_max_buffer_size[partitioned_vertex] \
            = send_buffers.max_buffer_size_possible
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
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if key not in self._send_buffers:

            send_buffer = BufferedSendingRegion(
                    self._max_on_chip_memory_usage_for_spikes)

            # translate spikes into buffer
            if hasattr(self._spike_times[0], "__len__"):

                # This is in SpiNNaker 'list of lists' format:
                for neuron in range(vertex_slice.lo_atom,
                                    vertex_slice.hi_atom + 1):
                    for timeStamp in sorted(self._spike_times[neuron]):
                        self._check_time_stamp(
                            send_buffer, timeStamp, self._machine_time_step,
                            self._no_machine_time_steps,
                            self._last_runtime_position,
                            (neuron - vertex_slice.lo_atom))
            else:

                # This is in official PyNN format, all neurons use the
                # same list:
                neuron_list = range(vertex_slice.n_atoms)
                for timeStamp in sorted(self._spike_times):
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

    def _reserve_memory_regions(
            self, spec, spike_region_size, recorded_region_size):
        """ Reserve memory for the system, indices and spike data regions.
            The indices region will be copied to DTCM by the executable.
        """
        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value,
            size=(constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4) + 8,
            label='systemInfo')

        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.CONFIGURATION_REGION.value,
            size=self._CONFIGURATION_REGION_SIZE, label='configurationRegion')

        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value,
            size=spike_region_size, label='SpikeDataRegion', empty=True)

        if self._spike_recorder.record:
            spec.reserve_memory_region(
                region=(self._SPIKE_SOURCE_REGIONS
                        .SPIKE_DATA_RECORDED_REGION.value),
                size=recorded_region_size + 4, label="RecordedSpikeDataRegion",
                empty=True)

    def _write_setup_info(self, spec, spike_buffer_region_size, ip_tags,
                          total_recording_region_size):
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
            spec, self._SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)

        # write flag for recording
        if self._spike_recorder.record:
            value = 1 | 0xBEEF0000
            spec.write_value(data=value)
            spec.write_value(data=(total_recording_region_size + 4))
        else:
            spec.write_value(data=0)
            spec.write_value(data=0)

        spec.switch_write_focus(
            region=self._SPIKE_SOURCE_REGIONS.CONFIGURATION_REGION.value)

        # write config for reverse ip tag
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

        # write config for buffers
        spec.write_value(data=spike_buffer_region_size)
        spec.write_value(data=self._space_before_notification)

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
        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        spike_buffer = self._get_spike_send_buffer(vertex_slice)
        recording_size = (spike_buffer.total_region_size + 4 +
                          self._RECORD_OVERALLOCATION)

        self._reserve_memory_regions(
            spec, spike_buffer.max_buffer_size_possible, recording_size)

        self._write_setup_info(
            spec, spike_buffer.max_buffer_size_possible, ip_tags,
            recording_size)

        subvertex.set_routing_infos(routing_info)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

        # tell the subvertex its region size
        subvertex.region_size = recording_size

        return [data_writer.filename]

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

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """ calculates the total SDRAM usage of the spike source array. If \
            the memory requirement is beyond what is deemed to be the usage\
            of the processor, then it executes a buffered format.

        :param vertex_slice: the slice of atoms this partitioned vertex will
        represent from the partitionable vertex
        :param graph: the partitionable graph which contains the high level
        objects
        :return:
        """
        send_buffer = self._get_spike_send_buffer(vertex_slice)
        send_size = send_buffer.max_buffer_size_possible
        record_size = 0
        if self._spike_recorder.record:
            record_size = (send_buffer.total_region_size + 4 +
                           self._RECORD_OVERALLOCATION)
        total_size = (
            (constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4) +
            SpikeSourceArray._CONFIGURATION_REGION_SIZE + send_size +
            record_size)

        # add memory count for mallocs
        no_mallocs = self.get_number_of_mallocs_used_by_dsg(
            vertex_slice, graph)
        total_size += \
            no_mallocs * front_end_common_constants.SARK_PER_MALLOC_SDRAM_USAGE

        return total_size

    def get_number_of_mallocs_used_by_dsg(self, vertex_slice, in_edges):
        standard_mallocs = self._DEFAULT_MALLOCS_USED
        if self._spike_recorder.record:
            standard_mallocs += 1
        if config.getboolean("SpecExecution", "specExecOnHost"):
            return 1
        else:
            return standard_mallocs

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """

        :param vertex_slice:
        :param graph:
        :return:
        """
        return 0

    def get_outgoing_edge_constraints(self, partitioned_edge, graph_mapper):
        """
        gets the constraints for edges going out of this vertex
        :param partitioned_edge: the partitioned edge that leaves this vertex
        :param graph_mapper: the graph mapper object
        :return: list of constraints
        """
        return [KeyAllocatorContiguousRangeContraint()]

    def is_data_specable(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    # @implements AbstractResetableForRunInterface.reset_for_run
    def reset_for_run(
            self, last_runtime_in_milliseconds, this_runtime_in_milliseconds):
        self._send_buffers.clear()
        self._last_runtime_position = last_runtime_in_milliseconds
        for (vertex_slice, partitioned_vertex) in self._partitioned_vertices:
            send_buffers = dict()
            send_buffers[
                self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value] = \
                self._get_spike_send_buffer(vertex_slice)
            partitioned_vertex.send_buffers = send_buffers
