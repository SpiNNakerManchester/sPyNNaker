import logging
import os
from spynnaker.pyNN.buffer_management.storage_objects.buffer_collection import \
    BufferCollection

from spynnaker.pyNN.models.abstract_models.abstract_comm_models.\
    abstract_buffer_receivable_partitionable_vertex import \
    AbstractBufferReceivablePartitionableVertex
from spynnaker.pyNN.models.spike_source.spike_source_array_partitioned_vertex import \
    SpikeSourceArrayPartitionedVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.spike_source.abstract_spike_source \
    import AbstractSpikeSource
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN import exceptions
from data_specification.data_specification_generator import \
    DataSpecificationGenerator
import math


logger = logging.getLogger(__name__)


class SpikeSourceArray(AbstractSpikeSource,
                       AbstractBufferReceivablePartitionableVertex):

    CORE_APP_IDENTIFIER = constants.SPIKESOURCEARRAY_CORE_APPLICATION_ID
    _CONFIGURATION_REGION_SIZE = 48
    _model_based_max_atoms_per_core = 2048  # limited to the n of
                                            # the x,y,p,n key format

    def __init__(
            self, n_neurons, spike_times, machine_time_step,
            buffer_ip_tag_tag_id, buffer_ip_tag_port, buffer_ip_tag_address,
            constraints=None,
            max_on_chip_memory_usage_for_recording_in_bytes=None,
            max_on_chip_memory_usage_for_spikes_in_bytes=None,
            no_buffers_for_recording=constants.NO_BUFFERS_FOR_TRANSMITTING,
            label="SpikeSourceArray"):
        """
        Creates a new SpikeSourceArray Object.
        """
        AbstractSpikeSource.__init__(
            self, label=label, n_neurons=n_neurons, constraints=constraints,
            max_atoms_per_core=SpikeSourceArray._model_based_max_atoms_per_core,
            machine_time_step=machine_time_step, tag=buffer_ip_tag_tag_id,
            port=buffer_ip_tag_port, address=buffer_ip_tag_address,
            max_on_chip_memory_usage_for_recording=
            max_on_chip_memory_usage_for_recording_in_bytes)
        #set supers
        AbstractBufferReceivablePartitionableVertex.__init__(self)

        self._spike_times = spike_times
        self._max_on_chip_memory_usage_for_spikes = \
            max_on_chip_memory_usage_for_spikes_in_bytes
        self._max_on_chip_memory_usage_for_recording = \
            max_on_chip_memory_usage_for_recording_in_bytes
        self._no_buffers_for_recording = no_buffers_for_recording
        self._buffer_region_memory_size = None

    @property
    def model_name(self):
        """
        Return a string representing a label for this class.
        """
        return "SpikeSourceArray"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        SpikeSourceArray.\
            _model_based_max_atoms_per_core = new_value

    def _get_spikes_per_timestep(self, vertex_slice):
        """
        spikeArray is a list with one entry per 'neuron'. The entry for
        one neuron is a list of times (in ms) when the neuron fires.
        We need to transpose this 'matrix' and get a list of firing neuron
        indices for each time tick:
        List can come in two formats (both now supported):
        1) Official PyNN format - single list that is used for all neurons
        2) SpiNNaker format - list of lists, one per neuron
        """
        buffer_collection = BufferCollection()
        no_buffers = 0
        number_of_spikes_transmitted = 0
        if isinstance(self._spike_times[0], list):
            # This is in SpiNNaker 'list of lists' format:
            for neuron in range(vertex_slice.lo_atom,
                                vertex_slice.hi_atom + 1):
                for timeStamp in sorted(self._spike_times[neuron]):
                    time_stamp_in_ticks = \
                        int((timeStamp * 1000.0) / self._machine_time_step)
                    if not buffer_collection.contains_key(time_stamp_in_ticks):
                        buffer_collection.add_buffer_element_to_transmit(
                            self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value,
                            time_stamp_in_ticks, neuron)
                        no_buffers += 1
                        number_of_spikes_transmitted += 1
                    else:
                        buffer_collection.add_buffer_element_to_transmit(
                            self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value,
                            time_stamp_in_ticks, neuron)
                        number_of_spikes_transmitted += 1
        else:
            # This is in official PyNN format, all neurons use the same list:
            neuron_list = range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1)
            for timeStamp in sorted(self._spike_times):
                time_stamp_in_ticks = \
                    int((timeStamp * 1000.0) / self._machine_time_step)
                if not buffer_collection.contains_key(time_stamp_in_ticks):
                    buffer_collection.add_buffer_elements_to_transmit(
                        self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value,
                        time_stamp_in_ticks, neuron_list)
                    no_buffers += 1
                    number_of_spikes_transmitted += vertex_slice.n_atoms
                else:
                    buffer_collection.add_buffer_elements_to_transmit(
                        self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value,
                        time_stamp_in_ticks, neuron_list)
                    number_of_spikes_transmitted += vertex_slice.n_atoms

        memory_used = \
            ((no_buffers * (constants.BUFFER_HEADER_SIZE +
                            constants.TIMESTAMP_SPACE_REQUIREMENT)) +
             (number_of_spikes_transmitted * constants.KEY_SIZE))
        return memory_used, buffer_collection

    def _reserve_memory_regions(self, spec, setup_sz, spike_region_size,
                                spike_hist_buff_sz):
        """
        *** Modified version of same routine in models.py These could be
        combined to form a common routine, perhaps by passing a list of
        entries. ***
        Reserve memory for the system, indices and spike data regions.
        The indices region will be copied to DTCM by the executable.
        """
        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value,
            size=setup_sz, label='systemInfo')

        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.CONFIGURATION_REGION.value,
            size=setup_sz, label='configurationRegion')

        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value,
            size=spike_region_size, label='SpikeDataRegion', empty=True)

        if spike_hist_buff_sz > 0:
            spec.reserve_memory_region(
                region=self._SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
                size=spike_hist_buff_sz, label='spikeHistBuffer',
                empty=True)

    def _write_setup_info(self, spec, spike_buffer_region_size,
                          recording_buffer_region_size):
        """
        Write information used to control the simulationand gathering of
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
        # What recording commands were set for the parent pynn_population.py?
        self._write_basic_setup_info(spec, SpikeSourceArray.CORE_APP_IDENTIFIER)
        recording_info = 0
        if (spike_buffer_region_size > 0) and self._record:
            recording_info |= constants.RECORD_SPIKE_BIT
        recording_info |= 0xBEEF0000
        #add the params saying how big each
        spec.switch_write_focus(
            region=self._SPIKE_SOURCE_REGIONS.CONFIGURATION_REGION.value)
        #write configs for reverse ip tag
        # NOTE
        # as the packets are formed in the buffers, and that its a spike source
        #array, and shouldnt have injectored packets, no config should be
        # required for it to work. the packet format will override these anyhow
        # END NOTE
        spec.write_value(data=0)  # prefix value
        spec.write_value(data=0)  # key left shift
        spec.write_value(data=0)  # add key check
        spec.write_value(data=0)  # key for transmitting
        spec.write_value(data=0)  # mask for transmitting

        #write configs for buffers
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_buffer_region_size)
        spec.write_value(data=recording_buffer_region_size)
        spec.write_value(data=self._threshold_for_reporting_bytes_written)

    def get_spikes(self, txrx, placements, graph_mapper, buffer_manager,
                   compatible_output=False):
        # Use standard behaviour to read spikes
        return self._get_spikes(
            transciever=txrx, placements=placements,
            graph_mapper=graph_mapper, compatible_output=compatible_output,
            spike_recording_region=
            self._SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            buffer_manager=buffer_manager)

    #inhirrted from dataspecable vertex
    def generate_data_spec(self, subvertex, placement, subgraph, graph,
                           routing_info, hostname, graph_mapper, report_folder):
        """
        Model-specific construction of the data blocks necessary to build a
        single SpikeSource Array on one core.
        """
        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        #get slice from mapper
        subvert_slice = graph_mapper.get_subvertex_slice(subvertex)

        spike_history_region_sz = self._get_recording_region_size(subvert_slice)

        spec.comment("\n*** Spec for SpikeSourceArray Instance ***\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:

        spec.comment("\nReserving memory space for spike data region:\n\n")

        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        real_spike_region_size = self.get_sdram_usage_for_atoms(vertex_slice,
                                                                None)

        # if the region size is zero, there still needs to be a header saying
        if real_spike_region_size == 0:
            real_spike_region_size = 4

        # Calculate memory requirements:
        spike_buffer_region_size = \
            self._get_recording_region_size(real_spike_region_size)

        #set buffered knowledge of the size of the buffered regions (in + out)
        self._buffer_region_memory_size = real_spike_region_size
        self._threshold_for_reporting_bytes_written = math.floor(
            spike_buffer_region_size / self._no_buffers_for_recording)

        # Create the data regions for the spike source array:
        self._reserve_memory_regions(
            spec, self._CONFIGURATION_REGION_SIZE, real_spike_region_size,
            spike_buffer_region_size)

        self._write_setup_info(
            spec, spike_history_region_sz, spike_buffer_region_size)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def get_binary_file_name(self):
        # Rebuild executable name
        common_binary_path = os.path.join(config.get("SpecGeneration",
                                                     "common_binary_folder"))

        binary_name = os.path.join(common_binary_path,
                                   'spike_source_array.aplx')
        return binary_name

    #inhirrted from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """ assumed correct cpu usage is not important

        :param vertex_slice:
        :param graph:
        :return:
        """
        return 0

    def get_sdram_usage_for_atoms(self, vertex_slice, vertex_in_edges):
        """ calcualtes the total sdram usage of the spike source array. If the
        memory requirement is beyond what is deemed to be the usage of the
        processor, then it executes a buffered format.

        :param vertex_slice:
        :param vertex_in_edges:
        :return:
        """
        self._set_default_sizes()

        spike_region_sz, buffer_collection = \
            self._get_spikes_per_timestep(vertex_slice)
        recording_region_size = self._get_recording_region_size(spike_region_sz)

        if spike_region_sz >= self._max_on_chip_memory_usage_for_spikes:
            self._buffer_region_memory_size = \
                self._max_on_chip_memory_usage_for_spikes
            self._requires_buffering = True

        return constants.SETUP_SIZE + spike_region_sz + recording_region_size

    def _set_default_sizes(self):
        """ used to do lazy evaluation of the default sizes of the chip
        memory usage for both recording and receiving spikes

        :return:
        """
        if self._max_on_chip_memory_usage_for_spikes is None:
            if self.record:
                self._max_on_chip_memory_usage_for_spikes = \
                    constants.DEFAULT_MEG_LIMIT / 2
            else:
                self._max_on_chip_memory_usage_for_spikes = \
                    constants.DEFAULT_MEG_LIMIT
        if self._max_on_chip_memory_usage_for_recording is None:
            if self.record:
                self._max_on_chip_memory_usage_for_recording = \
                    constants.DEFAULT_MEG_LIMIT / 2
            else:
                self._max_on_chip_memory_usage_for_recording = \
                    constants.DEFAULT_MEG_LIMIT
        #check the values do not confleict with chip memory limit
        max_memory_used_in_bytes = \
            self._max_on_chip_memory_usage_for_spikes + \
            self._max_on_chip_memory_usage_for_recording
        if (max_memory_used_in_bytes > constants.MAX_MEG_LIMIT
                or self._max_on_chip_memory_usage_for_spikes < 0
                or self._max_on_chip_memory_usage_for_recording < 0):
            raise exceptions.ConfigurationException(
                "The memory usage on chip is either beyond what is supportable"
                "on the spinnaker board being supported or you have requested"
                "a negative value for a memory usage. Please correct and "
                "try again")

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """ assumed that correct dtcm usage is not required

        :param vertex_slice:
        :param graph:
        :return:
        """
        return 0

    def create_subvertex(self, resources_required, vertex_slice, label=None,
                         additional_constraints=list()):
        """ overloaded method from abstract pattitionable vertex. used to hand
        a partitioned spike soruce array its own buffers

        :param resources_required:
        :param vertex_slice:
        :param label:
        :param additional_constraints:
        :return:
        """
        size, buffers = self._get_spikes_per_timestep(vertex_slice)
        return SpikeSourceArrayPartitionedVertex(
            buffers=buffers, label=label, resources_used=resources_required,
            additional_constraints=additional_constraints)

    def is_buffer_sendable_vertex(self):
        """helper method for isinstance

        :return:
        """
        return True

    def is_recordable(self):
        """helper method for isinstance

        :return:
        """
        return True

    def is_buffer_receivable_partitionable_vertex(self):
        """helper method for isinstance

        :return:
        """
        return True