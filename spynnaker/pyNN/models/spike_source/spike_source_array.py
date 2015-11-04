"""
SpikeSourceArray
"""

# spynnaker imports
from spinn_front_end_common.utility_models.\
    outgoing_edge_same_contiguous_keys_restrictor import \
    OutgoingEdgeSameContiguousKeysRestrictor
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.common.eieio_spike_recorder \
    import EIEIOSpikeRecorder
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.models.spike_source.spike_source_array_partitioned_vertex\
    import SpikeSourceArrayPartitionedVertex

from spinn_front_end_common.interface.buffer_management.storage_objects\
    .buffered_sending_region import BufferedSendingRegion

# spinn front end common imports
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities import constants as \
    front_end_common_constants

# pacman imports
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_iptag_constraint\
    import TagAllocatorRequireIptagConstraint

# dsg imports
from data_specification.data_specification_generator\
    import DataSpecificationGenerator

# general imports
from enum import Enum
import logging
import sys
import math
import tempfile

logger = logging.getLogger(__name__)

# Space in case the buffering ends up pushing more packets than required
_RECORD_OVERALLOCATION = 2000


class SpikeSourceArray(
        AbstractDataSpecableVertex, AbstractPartitionableVertex,
        AbstractSpikeRecordable, AbstractProvidesOutgoingEdgeConstraints):
    """
    model for play back of spikes
    """

    _CONFIGURATION_REGION_SIZE = 36

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

        # handle recording
        self._spike_recorder = EIEIOSpikeRecorder(machine_time_step)

        # handle outgoing constraints
        self._outgoing_edge_key_restrictor = \
            OutgoingEdgeSameContiguousKeysRestrictor()

        # bool for if state has changed.
        self._change_requires_mapping = True

        # counter of how many machien time steps the vertex has extracted
        self._extracted_machine_time_steps = 0
        self._spikes_cache_file = None

    @property
    def change_requires_mapping(self):
        """
        property for checking if someting has changed
        :return:
        """
        return self._change_requires_mapping

    @change_requires_mapping.setter
    def change_requires_mapping(self, new_value):
        """
        setter for the changed property
        :param new_value: the new state to change it to
        :return:
        """
        self._change_requires_mapping = new_value

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
        if len(self._partitioned_vertices) != 0:
            self._send_buffers.clear()
            for (vertex_slice, vertex) in self._partitioned_vertices:
                send_buffer = dict()
                send_buffer[
                    self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value] =\
                    self._get_spike_send_buffer(vertex_slice)
                vertex.send_buffers = send_buffer

    def is_recording_spikes(self):
        """
        helper method fro chekcing if spikes are being stored
        :return:
        """
        return self._spike_recorder.record

    def set_recording_spikes(self):
        """
        sets the recoridng flags
        :return:
        """
        self._spike_recorder.record = True

    def get_last_extracted_spike_time(self):
        """
        returns the total number of machine time stepst aht this vertex thinks
        it has extracted from the
        :return:
        """
        return self._extracted_machine_time_steps

    def get_cache_file_for_spike_data(self):
        """
        gets the cahce file this vertex uses for storing its spike data
        :return: the cache file for spikes
        """
        if self._spikes_cache_file is None:
            self._spikes_cache_file = tempfile.NamedTemporaryFile(mode='a+b')
        return self._spikes_cache_file

    def get_spikes(self, transceiver, n_machine_time_steps, placements,
                   graph_mapper):
        """
        gets spikes from the spike source array
        :param transceiver:
        :param n_machine_time_steps:
        :param placements:
        :param graph_mapper:
        :return:
        """
        self._extracted_machine_time_steps += n_machine_time_steps
        return self._spike_recorder.get_spikes(
            self.label, transceiver,
            self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_RECORDED_REGION.value,
            placements, graph_mapper, self)

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
        """
        creates a partitioned vertex from a partitionable vertex
        :param vertex_slice: the slice of partitionable atoms that the
        new partitioned vertex will contain
        :param resources_required: the reosurces used by the partitioned vertex
        :param label: the label of the partitioned vertex
        :param constraints: extra constraints added to the partitioned vertex
        :return: a partitioned vertex
        :rtype: SpikeSourceArrayPartitionedVertex
        """
        # map region id to the sned buffer for this partitioned vertex
        send_buffer = dict()
        send_buffer[self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value] =\
            self._get_spike_send_buffer(vertex_slice)
        # create and return the partitioned vertex
        partitioned_vertex = SpikeSourceArrayPartitionedVertex(
            send_buffer, resources_required, label, constraints)
        self._partitioned_vertices.append((vertex_slice, partitioned_vertex))
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
            send_buffer = BufferedSendingRegion(
                self._max_on_chip_memory_usage_for_spikes)
            if hasattr(self._spike_times[0], "__len__"):

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

            self._send_buffers[key] = send_buffer
        else:
            send_buffer = self._send_buffers[key]
        return send_buffer

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
                          _RECORD_OVERALLOCATION)

        self._reserve_memory_regions(spec, spike_buffer.buffer_size,
                                     recording_size)

        self._write_setup_info(
            spec, spike_buffer.buffer_size, ip_tags, recording_size)

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
        """ calculates the total sdram usage of the spike source array. If the
        memory requirement is beyond what is deemed to be the usage of the
        processor, then it executes a buffered format.

        :param vertex_slice: the slice of atoms this partitioned vertex will
        represent from the partiionable vertex
        :param graph: the partitionable graph which contains the high level
        objects
        :return:
        """
        send_buffer = self._get_spike_send_buffer(vertex_slice)
        send_size = send_buffer.buffer_size
        record_size = 0
        if self._spike_recorder.record:
            record_size = (send_buffer.total_region_size + 4 +
                           _RECORD_OVERALLOCATION)
        return (
            (constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4) +
            SpikeSourceArray._CONFIGURATION_REGION_SIZE + send_size +
            record_size)

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
        :param partitioned_edge: the parittioned edge that leaves this vertex
        :param graph_mapper: the graph mapper object
        :return: list of constraints
        """
        return self._outgoing_edge_key_restrictor.\
            get_outgoing_edge_constraints()

    def is_data_specable(self):
        """
        helper method for isinstance
        :return:
        """
        return True

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
            if key != "spike_times":
                self._change_requires_mapping = True
            return
        raise Exception("Type {} does not have parameter {}".format(
            self._model_name, key))
