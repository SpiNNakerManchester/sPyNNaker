from spynnaker.pyNN.models.spike_source.abstract_spike_source import \
    AbstractSpikeSource
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neural_properties.randomDistributions import \
    generate_parameter


from data_specification.data_specification_generator import \
    DataSpecificationGenerator


from math import exp, ceil
from enum import Enum
import numpy

import logging
from data_specification.enums.data_type import DataType
logger = logging.getLogger(__name__)

SLOW_RATE_PER_TICK_CUTOFF = 0.25
PARAMS_BASE_WORDS = 3
PARAMS_WORDS_PER_NEURON = 5
RANDOM_SEED_WORDS = 4


class SpikeSourcePoisson(AbstractSpikeSource):
    """
    This class represents a Poisson Spike source object, which can represent
    a pynn_population.py of virtual neurons each with its own parameters.
    """

    CORE_APP_IDENTIFIER = constants.SPIKESOURCEPOISSON_CORE_APPLICATION_ID
    _POISSON_SPIKE_SOURCE_REGIONS = Enum(
        value="_POISSON_SPIKE_SOURCE_REGIONS",
        names=[('SYSTEM_REGION', 0),
               ('POISSON_PARAMS_REGION', 1),
               ('SPIKE_HISTORY_REGION', 2)])
    _model_based_max_atoms_per_core = 256

    def __init__(self, n_neurons, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma,
                 contraints=None, label="SpikeSourcePoisson",
                 rate=1.0, start=0.0, duration=None, seed=None):
        """
        Creates a new SpikeSourcePoisson Object.
        """
        AbstractSpikeSource.__init__(self, label, n_neurons, contraints,
                                     machine_time_step=machine_time_step,
                                     timescale_factor=timescale_factor,
                                     max_atoms_per_core=SpikeSourcePoisson.
                                     _model_based_max_atoms_per_core)
        self._rate = rate
        self._start = start
        self._duration = duration
        self._seed = seed

        if duration is None:
            self._duration = ((4294967295.0 - self._start)
                              / (1000.0 * machine_time_step))

    @property
    def model_name(self):
        """
        Return a string representing a label for this class.
        """
        return "SpikeSourcePoisson"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        SpikeSourcePoisson.\
            _model_based_max_atoms_per_core = new_value

    def get_spike_buffer_size(self, vertex_slice):
        """
        Gets the size of the spike buffer for a range of neurons and time steps
        """
        if not self._record:
            return 0

        if self._no_machine_time_steps is None:
            return 0

        bytes_per_time_step = int(
            ceil((vertex_slice.hi_atom - vertex_slice.lo_atom + 1) / 32.0)) * 4
        return self.get_recording_region_size(bytes_per_time_step)

    @staticmethod
    def get_params_bytes(vertex_slice):
        """
        Gets the size of the possion parameters in bytes
        """
        return (RANDOM_SEED_WORDS + PARAMS_BASE_WORDS
                + (((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1)
                   * PARAMS_WORDS_PER_NEURON)) * 4

    def reserve_memory_regions(self, spec, setup_sz, poisson_params_sz,
                               spike_hist_buff_sz):
        """
        Reserve memory regions for poisson source parameters
        and output buffer.
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=self._POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value,
            size=setup_sz, label='setup')
        spec.reserve_memory_region(
            region=self._POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value,
            size=poisson_params_sz, label='PoissonParams')
        if spike_hist_buff_sz > 0:
            spec.reserve_memory_region(
                region=self._POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
                size=spike_hist_buff_sz, label='spikeHistBuffer',
                empty=True)

    def write_setup_info(self, spec, spike_history_region_sz):
        """
        Write information used to control the simulationand gathering of
        results.
        Currently, this means the flag word used to signal whether information
        on neuron firing and neuron potential is either stored locally in a
        buffer or
        passed out of the simulation for storage/display as the simulation
        proceeds.

        The format of the information is as follows:
        Word 0: Flags selecting data to be gathered during simulation.
            Bit 0: Record spike history
        """

        # What recording commands wereset for the parent pynn_population.py?
        self._write_basic_setup_info(spec,
                                     SpikeSourcePoisson.CORE_APP_IDENTIFIER)
        recording_info = 0
        if (spike_history_region_sz > 0) and self._record:
            recording_info |= constants.RECORD_SPIKE_BIT
        recording_info |= 0xBEEF0000
        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(
            region=self._POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)
        spec.write_value(data=recording_info)
        spec.write_value(data=spike_history_region_sz)
        spec.write_value(data=0)
        spec.write_value(data=0)

    def write_poisson_parameters(
            self, spec, processor_chip_x, processor_chip_y, processor_id,
            num_neurons):
        """
        Generate Neuron Parameter data for Poisson spike sources (region 2):
        """
        spec.comment("\nWriting Neuron Parameters for {} poisson sources:\n"
                     .format(num_neurons))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=self._POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value)

        # Write header info to the memory region:

        # Write Key info for this core:
        population_identity = \
            packet_conversions.get_key_from_coords(processor_chip_x,
                                                   processor_chip_y,
                                                   processor_id)
        spec.write_value(data=population_identity)

        # Write the random seed (4 words), generated randomly!
        if self._seed is None:
            spec.write_value(data=numpy.random.randint(0x7FFFFFFF))
            spec.write_value(data=numpy.random.randint(0x7FFFFFFF))
            spec.write_value(data=numpy.random.randint(0x7FFFFFFF))
            spec.write_value(data=numpy.random.randint(0x7FFFFFFF))
        else:
            spec.write_value(data=self._seed[0])
            spec.write_value(data=self._seed[1])
            spec.write_value(data=self._seed[2])
            spec.write_value(data=self._seed[3])

        # For each neuron, get the rate to work out if it is a slow
        # or fast source
        slow_sources = list()
        fast_sources = list()
        for i in range(0, num_neurons):

            # Get the parameter values for source i:
            rate_val = generate_parameter(self._rate, i)
            start_val = generate_parameter(self._start, i)
            end_val = generate_parameter(self._duration, i) + start_val

            # Decide if it is a fast or slow source and
            spikes_per_tick = \
                (float(rate_val) * (self._machine_time_step / 1000000.0))
            if spikes_per_tick <= SLOW_RATE_PER_TICK_CUTOFF:
                slow_sources.append([i, rate_val, start_val, end_val])
            else:
                fast_sources.append([i, spikes_per_tick, start_val, end_val])

        # Write the numbers of each type of source
        spec.write_value(data=len(slow_sources))
        spec.write_value(data=len(fast_sources))

        # Now write one struct for each slow source as follows
        #
        #   typedef struct slow_spike_source_t
        #   {
        #     uint32_t neuron_id;
        #     uint32_t start_ticks;
        #     uint32_t end_ticks;
        #
        #     accum mean_isi_ticks;
        #     accum time_to_spike_ticks;
        #   } slow_spike_source_t;
        for (neuron_id, rate_val, start_val, end_val) in slow_sources:
            isi_val = float(1000000.0 / (rate_val * self._machine_time_step))
            start_scaled = int(start_val * 1000.0 / self._machine_time_step)
            end_scaled = int(end_val * 1000.0 / self._machine_time_step)
            spec.write_value(data=neuron_id, data_type=DataType.UINT32)
            spec.write_value(data=start_scaled, data_type=DataType.UINT32)
            spec.write_value(data=end_scaled, data_type=DataType.UINT32)
            spec.write_value(data=isi_val, data_type=DataType.S1615)
            spec.write_value(data=0x0, data_type=DataType.UINT32)

        # Now write
        #   typedef struct fast_spike_source_t
        #   {
        #     uint32_t neuron_id;
        #     uint32_t start_ticks;
        #     uint32_t end_ticks;
        #
        #     unsigned long fract exp_minus_lambda;
        #   } fast_spike_source_t;
        for (neuron_id, spikes_per_tick, start_val, end_val) in fast_sources:
            exp_minus_lamda = exp(-1.0 * spikes_per_tick)
            start_scaled = int(start_val * 1000.0 / self._machine_time_step)
            end_scaled = int(end_val * 1000.0 / self._machine_time_step)
            spec.write_value(data=neuron_id, data_type=DataType.UINT32)
            spec.write_value(data=start_scaled, data_type=DataType.UINT32)
            spec.write_value(data=end_scaled, data_type=DataType.UINT32)
            spec.write_value(data=exp_minus_lamda, data_type=DataType.U032)
        return

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
            self._POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            sub_vertex_out_spike_bytes_function=
            sub_vertex_out_spike_bytes_function)

    #inhirrtted from partionable vertex
    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        method for calculating sdram usage
        """
        poisson_params_sz = self.get_params_bytes(vertex_slice)
        spike_hist_buff_sz = self.get_spike_buffer_size(vertex_slice)
        return constants.SETUP_SIZE + poisson_params_sz + spike_hist_buff_sz

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """
        method for caulculating dtcm usage for a coltection of atoms
        """
        return 0
        #no_atoms = vertex_slice.hi_atom - vertex_slice.lo_atom + 1
        #return (44 + (16 * 4)) * no_atoms

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """
        Gets the CPU requirements for a range of atoms
        """
        return 0
        #no_atoms = vertex_slice.hi_atom - vertex_slice.lo_atom + 1
        #return 128 * no_atoms

    #inhirrted from dataspecable vertex

    def generate_data_spec(self, subvertex, placement, subgraph, graph,
                           routing_info, hostname, graph_mapper, report_folder):
        """
        Model-specific construction of the data blocks necessary to build a
        single SpikeSourcePoisson on one core.
        """
        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)

        spike_hist_buff_sz = self.get_spike_buffer_size(vertex_slice)

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        poisson_params_sz = self.get_params_bytes(vertex_slice)

        # Reserve SDRAM space for memory areas:
        self.reserve_memory_regions(
            spec, constants.SETUP_SIZE, poisson_params_sz, spike_hist_buff_sz)

        self.write_setup_info(spec, spike_hist_buff_sz)

        self.write_poisson_parameters(spec, placement.x, placement.y,
                                      placement.p, vertex_slice.n_atoms)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def get_binary_file_name(self):
        return "spike_source_poisson.aplx"

    def is_recordable(self):
        return True