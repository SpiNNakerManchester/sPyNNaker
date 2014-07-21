from abc import ABCMeta
from abc import abstractmethod
import os
import math
import tempfile
import logging

from six import add_metaclass
import numpy

from data_specification.data_specification_generator import \
    DataSpecificationGenerator
from data_specification.file_data_writer import FileDataWriter
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neural_properties.abstract_synaptic_manager import \
    SynapticManager
from spynnaker.pyNN.models.abstract_models.\
    abstract_partitionable_population_vertex import \
    AbstractPartitionablePopulationVertex


logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class PopulationManager(SynapticManager, AbstractPartitionablePopulationVertex):

    def __init__(self, record, binary, n_neurons, label, constraints):
        SynapticManager.__init__(self)
        AbstractPartitionablePopulationVertex.__init__(self, n_neurons,
                                                       label, constraints)
        self._record = record
        self._record_v = False
        self._record_gsyn = False
        self._binary = binary
        self._executable_constant = None

    def record_v(self):
        self._record_v = True

    def record_gsyn(self):
        self._record_gsyn = True

    @abstractmethod
    def get_parameters(self):
        """
        method to return whatever params a model has
        """

    def reserve_population_based_memory_regions(
            self, spec, setup_sz, neuron_params_sz, synapse_params_sz,
            row_len_trans_sz, master_pop_table_sz, all_syn_block_sz,
            spike_hist_buff_sz, potential_hist_buff_sz, gsyn_hist_buff_sz,
            stdp_params_sz):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) Neuron parameter data (will be copied to DTCM by 'C'
           code at start-up)
        3) synapse parameter data (will be copied to DTCM)
        4) Synaptic row length look-up (copied to DTCM)
        5) Synaptic block look-up table. Translates the start address
           of each block of synapses (copied to DTCM)
        6) Synaptic row data (lives in SDRAM)
        7) Spike history
        8) Neuron potential history
        9) Gsyn value history
        """

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(region=self.POPULATION_BASED_REGIONS.SYSTEM,
                                   size=setup_sz, label='setup')
        spec.reserve_memory_region(
            region=self.POPULATION_BASED_REGIONS.NEURON_PARAMS,
            size=neuron_params_sz, label='NeuronParams')
        spec.reserve_memory_region(
            region=self.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS,
            size=synapse_params_sz, label='SynapseParams')
        spec.reserve_memory_region(
            region=self.POPULATION_BASED_REGIONS.ROW_LEN_TRANSLATION,
            size=row_len_trans_sz, label='RowLenTable')
        spec.reserve_memory_region(
            region=self.POPULATION_BASED_REGIONS.MASTER_POP_TABLE,
            size=master_pop_table_sz, label='MasterPopTable')
        spec.reserve_memory_region(
            region=self.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX,
            size=all_syn_block_sz, label='SynBlocks')

        if self._record:
            spec.reserve_memory_region(
                region=self.POPULATION_BASED_REGIONS.SPIKE_HISTORY,
                size=spike_hist_buff_sz, label='spikeHistBuffer',
                leaveUnfilled=True)
        if self._record_v:
            spec.reserve_memory_region(
                region=self.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY,
                size=potential_hist_buff_sz, label='potHistBuffer',
                leaveUnfilled=True)
        if self._record_gsyn:
            spec.reserve_memory_region(
                region=self.POPULATION_BASED_REGIONS.GSYN_HISTORY,
                size=gsyn_hist_buff_sz, label='gsynHistBuffer',
                leaveUnfilled=True)
        if stdp_params_sz != 0:
            spec.reserve_memory_region(
                region=self.POPULATION_BASED_REGIONS.STDP_PARAMS,
                size=stdp_params_sz, label='stdpParams')

    def write_setup_info(self, spec, spike_history_region_sz,
                         neuron_potential_region_sz, gsyn_region_sz,
                         executable_constant):
        """
        Write information used to control the simulation and gathering of
        results.Currently, this means the flag word used to signal whether
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
        recording_info = 0
        if spike_history_region_sz > 0 and self._record:
            recording_info |= constants.RECORD_SPIKE_BIT
        if neuron_potential_region_sz > 0 and self._record_v:
            recording_info |= constants.RECORD_STATE_BIT
        if gsyn_region_sz > 0 and self._record_gsyn:
            recording_info |= constants.RECORD_GSYN_BIT
        recording_info |= 0xBEEF0000

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(region=self.POPULATION_BASED_REGIONS.SYSTEM)
        spec.write_value(data=executable_constant)
        spec.write_value(data=self._machine_time_step)
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_history_region_sz)
        spec.write_value(data=neuron_potential_region_sz)
        spec.write_value(data=gsyn_region_sz)

    def write_neuron_parameters(self, spec, processor,
                                subvertex, ring_buffer_to_input_left_shift):
        spec.comment("\nWriting Neuron Parameters for {%d} "
                     "Neurons:\n".format(subvertex.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=self.POPULATION_BASED_REGIONS.NEURON_PARAMS)

        # Write header info to the memory region:
        # Write Key info for this core:
        chip_x, chip_y, chip_p = processor.get_coordinates()
        population_identity = \
            packet_conversions.get_key_from_coords(chip_x, chip_y, chip_p)
        spec.write_value(data=population_identity)

        # Write the number of neurons in the block:
        spec.write_value(data=subvertex.n_atoms)

        # Write the number of parameters per neuron (struct size in words):
        params = self.get_parameters()

        # noinspection PyTypeChecker
        spec.write_value(data=len(params))

        # Write machine time step: (Integer, expressed in microseconds)
        spec.write_value(data=self._machine_time_step)

        # Write ring_buffer_to_input_left_shift
        spec.write_value(data=ring_buffer_to_input_left_shift)

        # TODO: NEEDS TO BE LOOKED AT PROPERLY
        # Create loop over number of neurons:
        for atom in range(0, subvertex.n_atoms):
            # Process the parameters

            # noinspection PyTypeChecker
            for param in params:
                value = param.get_value()
                if hasattr(value, "__len__"):
                    if len(value) > 1:
                        value = value[atom]
                    else:
                        value = value[0]

                datatype = param.get_dataspec_datatype()
                scale = param.get_scale()

                value = value * scale

                spec.write_value(data=value, data_type=datatype)
        # End the loop over the neurons:

    @staticmethod
    def get_ring_buffer_to_input_left_shift(subvertex):
        total_exc_weights = numpy.zeros(subvertex.n_atoms)
        total_inh_weights = numpy.zeros(subvertex.n_atoms)
        for subedge in subvertex.in_subedges:
            sublist = subedge.get_synapse_sublist()
            sublist.sum_weights(total_exc_weights, total_inh_weights)

        max_weight = max((max(total_exc_weights), max(total_inh_weights)))
        max_weight_log_2 = 0
        if max_weight > 0:
            max_weight_log_2 = math.log(max_weight, 2)

        # Currently, we can only cope with positive left shifts, so the minimum
        # scaling will be no shift i.e. a max weight of 0nA
        if max_weight_log_2 < 0:
            max_weight_log_2 = 0

        max_weight_power = int(math.ceil(max_weight_log_2))

        logger.debug("Max weight is {}, Max power is {}"
                     .format(max_weight, max_weight_power))

        # Actual shift is the max_weight_power - 1 for 16-bit fixed to s1615,
        # but we ignore the "-1" to allow a bit of overhead in the above
        # calculation in case a couple of extra spikes come in
        return max_weight_power

    def generate_data_spec(self, processor, subvertex):
        """
        Model-specific construction of the data blocks necessary to
        build a group of IF_curr_exp neurons resident on a single core.
        """
        # Create new DataSpec for this processor:
        binary_file_name = self.get_binary_file_name(processor)

        data_writer = FileDataWriter(binary_file_name)

        spec = DataSpecificationGenerator(data_writer)

        spec.comment("\n*** Spec for block of {%s} neurons ***\n"
                     .format(self.model_name))

        # Calculate the size of the tables to be reserved in SDRAM:
        neuron_params_sz = self.get_neuron_params_size(subvertex.lo_atom,
                                                       subvertex.hi_atom)
        synapse_params_sz = self.get_synapse_parameter_size(subvertex.lo_atom,
                                                            subvertex.hi_atom)
        all_syn_block_sz = self.get_exact_synaptic_block_memory_size(subvertex)
        spike_hist_buff_sz = self.get_spike_buffer_size(subvertex.lo_atom,
                                                        subvertex.hi_atom)
        potential_hist_buff_sz = self.get_v_buffer_size(subvertex.lo_atom,
                                                        subvertex.hi_atom)
        gsyn_hist_buff_sz = self.get_g_syn_buffer_size(subvertex.lo_atom,
                                                       subvertex.hi_atom)
        stdp_region_sz = self.get_stdp_parameter_size(subvertex.lo_atom,
                                                      subvertex.hi_atom,
                                                      self.in_edges)

        # Declare random number generators and distributions:
        self.write_random_distribution_declarations(spec)

        # Construct the data images needed for the Neuron:
        self.reserve_population_based_memory_regions(
            spec, constants.SETUP_SIZE, neuron_params_sz, synapse_params_sz,
            SynapticManager.ROW_LEN_TABLE_SIZE,
            SynapticManager.MASTER_POPULATION_TABLE_SIZE, all_syn_block_sz,
            spike_hist_buff_sz, potential_hist_buff_sz, gsyn_hist_buff_sz,
            stdp_region_sz)

        self.write_setup_info(spec, spike_hist_buff_sz, potential_hist_buff_sz,
                              gsyn_hist_buff_sz, self._executable_constant)

        ring_buffer_shift = self.get_ring_buffer_to_input_left_shift(subvertex)
        weight_scale = self.get_weight_scale(ring_buffer_shift)
        logger.debug("Weight scale is {}".format(weight_scale))

        self.write_neuron_parameters(spec, processor, subvertex,
                                     ring_buffer_shift)

        self.write_synapse_parameters(spec, subvertex)

        self.write_stdp_parameters(
            spec, subvertex, weight_scale, 
            self.POPULATION_BASED_REGIONS.STDP_PARAMS)

        self.write_row_length_translation_table(
            spec, self.POPULATION_BASED_REGIONS.ROW_LEN_TRANSLATION)

        self.write_synaptic_matrix_and_master_population_table(
            spec, subvertex, all_syn_block_sz, weight_scale,
            self.POPULATION_BASED_REGIONS.MASTER_POP_TABLE,
            self.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX)

        for subedge in subvertex.in_subedges:
            subedge.free_sublist()

        # End the writing of this specification:
        spec.end_specification()
        data_writer.close()

         # Split binary name into title and extension
        binary_title, binary_extension = os.path.splitext(self._binary)

        # If we have an STDP mechanism, add it's executable suffic to title
        if self._stdp_mechanism is not None:
            binary_title = \
                binary_title + "_" + \
                self._stdp_mechanism.get_vertex_executable_suffix()

        # Rebuild executable name
        binary_name = os.path.join(config.get("SpecGeneration",
                                              "common_binary_folder"),
                                   binary_title + binary_extension)

        # Return list of target cores, executables, files to load and
        # memory writes to perform:
        return binary_name, list(), list()

    @staticmethod
    def get_binary_file_name(processor):
        x, y, p = processor.get_coordinates()
        hostname = processor.chip.machine.hostname
        has_binary_folder_set = \
            config.has_option("SpecGeneration", "Binary_folder")
        if not has_binary_folder_set:
            binary_folder = tempfile.gettempdir()
            config.set("SpecGeneration", "Binary_folder", binary_folder)
        else:
            binary_folder = config.get("SpecGeneration", "Binary_folder")

        binary_file_name = \
            binary_folder + os.sep + "{%s}_dataSpec_{%d}_{%d}_{%d}.dat"\
                                     .format(hostname, x, y, p)
        return binary_file_name