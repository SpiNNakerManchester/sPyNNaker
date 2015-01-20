from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.spike_source.abstract_spike_source \
    import AbstractSpikeSource
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.utilities.conf import config


from data_specification.data_specification_generator import \
    DataSpecificationGenerator

from spynnaker.pyNN import exceptions


from math import ceil
from collections import defaultdict
import logging
import math

logger = logging.getLogger(__name__)


class SpikeSourceArray(AbstractSpikeSource):

    CORE_APP_IDENTIFIER = constants.SPIKESOURCEARRAY_CORE_APPLICATION_ID
    _model_based_max_atoms_per_core = 256

    def __init__(self, n_neurons, spike_times, machine_time_step,
                 spikes_per_second, ring_buffer_sigma,
                 timescale_factor, constraints=None, label="SpikeSourceArray"):
        """
        Creates a new SpikeSourceArray Object.
        """
        AbstractSpikeSource.__init__(self, label=label, n_neurons=n_neurons,
                                     constraints=constraints,
                                     max_atoms_per_core=SpikeSourceArray.
                                     _model_based_max_atoms_per_core,
                                     machine_time_step=machine_time_step,
                                     timescale_factor=timescale_factor)
        self._spike_times = spike_times

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

    def get_spikes_per_timestep(self, vertex_slice):
        """
        spikeArray is a list with one entry per 'neuron'. The entry for
        one neuron is a list of times (in ms) when the neuron fires.
        We need to transpose this 'matrix' and get a list of firing neuron
        indices for each time tick:
        List can come in two formats (both now supported):
        1) Official PyNN format - single list that is used for all neurons
        2) SpiNNaker format - list of lists, one per neuron
        """
        spike_dict = defaultdict(list)
        if isinstance(self._spike_times[0], list):
            # This is in SpiNNaker 'list of lists' format:
            for neuron in range(vertex_slice.lo_atom,
                                vertex_slice.hi_atom + 1):
                for timeStamp in self._spike_times[neuron]:
                    time_stamp_in_ticks = \
                        int((timeStamp * 1000.0) / self._machine_time_step)
                    spike_dict[time_stamp_in_ticks].append(neuron)
        else:
            # This is in official PyNN format, all neurons use the same list:
            neuron_list = list(range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1))
            for timeStamp in self._spike_times:
                time_stamp_in_ticks = \
                    int((timeStamp * 1000.0) / self._machine_time_step)

                spike_dict[time_stamp_in_ticks].extend(neuron_list)

        return spike_dict

    @staticmethod
    def get_spike_block_row_length(n_atoms):
        return int(math.ceil(n_atoms / constants.BITS_PER_WORD))

    @staticmethod
    def get_spike_region_bytes(spike_block_row_length, no_active_timesteps):
        return spike_block_row_length * no_active_timesteps * 4

    def get_spike_buffer_size(self, vert_slice):
        """
        Gets the size of the spike buffer for a range of neurons and time steps
        """
        if not self._record:
            return 0

        if self._no_machine_time_steps is None:
            return 0

        out_spike_spikes = \
            int(ceil((vert_slice.hi_atom - vert_slice.lo_atom + 1) / 32.0)) * 4
        return self.get_recording_region_size(out_spike_spikes)

    @staticmethod
    def get_block_index_bytes(no_active_timesteps):
        return (constants.BLOCK_INDEX_HEADER_WORDS + (no_active_timesteps
                * constants.BLOCK_INDEX_ROW_WORDS)) * 4

    def process_spike_array_info(self, subvertex, graph_mapper):
        """
        Parse python definitons of the required spike arrays and construct
        both the spike blocks, containing lists of spike IDs for each time step,
        and the index table, which gives the address in memory to access
        the spike block for the current time step.
        """
        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        spike_dict = self.get_spikes_per_timestep(vertex_slice)

        # Dict spikeDict now has entries based on timeStamp and each entry
        # is a list of neurons firing at that time.
        # Get keys in time order:
        time_keys = spike_dict.keys()
        time_keys.sort()

        # Calculate how big the spike rows will be:
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        spike_block_row_length = \
            self.get_spike_block_row_length(n_atoms)
        spike_region_size = self.get_spike_region_bytes(spike_block_row_length,
                                                        len(time_keys))

        # Create a new tableEntry for each unique time stamp, then
        # build a spike Block, tracking its size:
        table_entries = list()
        spike_blocks = list()
        spike_block_start_addr = 0
        for timeStamp in time_keys:
            current_spike_block = list()
            # Create tableEntry:
            table_entries.append([timeStamp, spike_block_start_addr])
            # Construct spikeBlock:
            list_of_spike_indices = spike_dict[timeStamp]
            for spikeIndex in list_of_spike_indices:
                current_spike_block.append(spikeIndex - vertex_slice.lo_atom)
            # Add the spike block for this time step to the spike blocks list:
            spike_blocks.append(current_spike_block)
            spike_block_start_addr += spike_block_row_length
        return n_atoms, table_entries, spike_blocks, spike_region_size

    def reserve_memory_regions(self, spec, setup_sz, block_index_region_size,
                               spike_region_size, spike_hist_buff_sz):
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
            region=self._SPIKE_SOURCE_REGIONS.BLOCK_INDEX_REGION.value,
            size=block_index_region_size, label='SpikeBlockIndexRegion')

        spec.reserve_memory_region(
            region=self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value,
            size=spike_region_size, label='SpikeDataRegion')

        if spike_hist_buff_sz > 0:
            spec.reserve_memory_region(
                region=self._SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
                size=spike_hist_buff_sz, label='spikeHistBuffer',
                empty=True)

    def write_setup_info(self, spec, spike_history_region_sz):
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
        if (spike_history_region_sz > 0) and self._record:
            recording_info |= constants.RECORD_SPIKE_BIT
        recording_info |= 0xBEEF0000
        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(
            region=self._SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_history_region_sz)
        spec.write_value(data=0)
        spec.write_value(data=0)

    def write_block_index_region(self, spec, placement,
                                 num_neurons, table_entries):
        """
        Spike block index table. Gives address of each block of spikes.
        numNeurons is the total number of spike sources to be modelled.
        tableEntries is a list of the entries, each of which consists of:
        struct {
            uint32 timeStamp          # In simulation ticks
            uint32 addressOfBlockWord # Relative to start of spikeDataRegion
        } entry

        """
        spec.switch_write_focus(
            region=self._SPIKE_SOURCE_REGIONS.BLOCK_INDEX_REGION.value)
        # Word 0 is the key (x, y, p) for this core:
        chip_x, chip_y, chip_p = placement.x, placement.y, placement.p
        population_identity = \
            packet_conversions.get_key_from_coords(chip_x, chip_y, chip_p)
        spec.write_value(data=population_identity)

        # Word 1 is the total number of 'neurons' (i.e. spike sources) in
        # the pynn_population.py:
        spec.write_value(data=num_neurons)

        # Word 2 is the total number of entries in this table of indices:
        num_entries = len(table_entries)
        spec.write_value(data=num_entries)

        # Write individual entries:
        for entry in table_entries:
            time_stamp = entry[0]   # Time in ticks when this block is used
            address = entry[1]   # Address into spikeBlock region
            spec.write_value(data=time_stamp)
            spec.write_value(data=address)
        return

    def write_spike_data_region(self, spec, num_neurons, spike_blocks):
        """
        Spike data blocks.
        Blocks given in list spikeBlocks.
        Each block is a list of the indices of 'neurons' that should
        fire this tick of the simulation clock. they are converted
        into bit vectors of length ceil(numNeurons/32) words, in
        which the bit position is the neuron index and a '1' in a given
        position means that neuron fires this tick.
        """
        spec.switch_write_focus(
            region=self._SPIKE_SOURCE_REGIONS.SPIKE_DATA_REGION.value)
        vector_len = int(math.ceil(num_neurons / 32.0))
        for block in spike_blocks:
            spike_bit_vectors = [0] * vector_len
            # Process this block of spike indices, setting a bit corresponding
            # to this index for each spiking neuron source:
            for index in block:
                word_num = index >> 5
                bit_num = index & 0x1F
                or_mask = 1 << bit_num

                # Set the target bit:
                spike_bit_vectors[word_num] |= or_mask
            # Write this to spikeBlock region:
            for i in range(vector_len):
                spec.write_value(data=spike_bit_vectors[i])

    def get_spikes(self, txrx, placements, graph_mapper,
                   compatible_output=False):

        # Spike sources store spike vectors optimally so calculate min
        # words to represent
        sub_vertex_out_spike_bytes_function = \
            lambda subvertex, subvertex_slice: int(ceil(
                    subvertex_slice.n_atoms / 32.0)) * 4

        # Use standard behaviour to read spikes
        return self._get_spikes(
            transciever=txrx, placements=placements,
            graph_mapper=graph_mapper, compatible_output=compatible_output,
            spike_recording_region=
            self._SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            sub_vertex_out_spike_bytes_function=
            sub_vertex_out_spike_bytes_function)

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

        spike_history_region_sz = self.get_spike_buffer_size(subvert_slice)

        spec.comment("\n*** Spec for SpikeSourceArray Instance ***\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:

        spec.comment("\nReserving memory space for spike data region:\n\n")

        num_neurons, table_entries, spike_blocks, spike_region_size = \
            self.process_spike_array_info(subvertex, graph_mapper)
        if spike_region_size == 0:
            spike_region_size = 4

        # Calculate memory requirements:
        block_index_region_size = self.get_block_index_bytes(len(table_entries))

        # Create the data regions for the spike source array:
        self.reserve_memory_regions(spec, constants.SETUP_SIZE,
                                    block_index_region_size,
                                    spike_region_size, spike_history_region_sz)
        self.write_setup_info(spec, spike_history_region_sz)

        self.write_block_index_region(spec, placement, num_neurons,
                                      table_entries)
        self.write_spike_data_region(spec, num_neurons, spike_blocks)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def get_binary_file_name(self):
        return "spike_source_array.aplx"

    #inhirrted from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        return 0
        #n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        #return 128 * n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, vertex_in_edges):
        spike_dict = self.get_spikes_per_timestep(vertex_slice)
        no_active_timesteps = len(spike_dict.keys())
        spike_block_row_length = self.get_spike_block_row_length(
            ((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1))
        spike_region_sz = self.get_spike_region_bytes(spike_block_row_length,
                                                      no_active_timesteps)
        block_index_region_size = \
            self.get_block_index_bytes(no_active_timesteps)

        spike_history_region_sz = self.get_spike_buffer_size(vertex_slice)
        return (constants.SETUP_SIZE + spike_region_sz + block_index_region_size
                + spike_history_region_sz)

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        return 0
        #n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        #return (44 + (16 * 4)) * n_atoms

    def is_recordable(self):
        return True