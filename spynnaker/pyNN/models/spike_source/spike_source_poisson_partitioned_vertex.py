import math
import numpy
from enum import Enum

from data_specification.data_specification_generator \
    import DataSpecificationGenerator
from data_specification.enums.data_type import DataType

from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

from spinn_front_end_common.abstract_models.abstract_executable \
    import AbstractExecutable
from spinn_front_end_common.interface.has_n_machine_timesteps \
    import HasNMachineTimesteps
from spinn_front_end_common.utilities import data_spec_utilities
from spinn_front_end_common.utilities import simulation_utilities
from spinn_front_end_common.abstract_models\
    .abstract_data_specable_partitioned_vertex \
    import AbstractDataSpecablePartitionedVertex
from spinn_front_end_common.abstract_models\
    .abstract_outgoing_edge_same_contiguous_keys_restrictor \
    import AbstractOutgoingEdgeSameContiguousKeysRestrictor


from spynnaker.pyNN.utilities.randomDistributions import generate_parameter
from spynnaker.pyNN.models.common.abstract_spike_recordable_subvertex \
    import AbstractSpikeRecordableSubvertex

SLOW_RATE_PER_TICK_CUTOFF = 0.25


class SpikeSourcePoissonPartitionedVertex(
        PartitionedVertex, AbstractSpikeRecordableSubvertex,
        AbstractDataSpecablePartitionedVertex,
        AbstractExecutable, HasNMachineTimesteps,
        AbstractOutgoingEdgeSameContiguousKeysRestrictor):

    _POISSON_SPIKE_SOURCE_REGIONS = Enum(
        value="_POISSON_SPIKE_SOURCE_REGIONS",
        names=[('HEADER', 0),
               ('RECORDING_DATA', 1),
               ('POISSON_PARAMS_REGION', 2),
               ('SPIKE_HISTORY_REGION', 3)])

    _SPIKE_HISTORY_CONFIGURATION_SIZE = 8

    def __init__(self, resources_required, label, constraints,
                 spike_source_poisson, vertex_slice, machine_time_step,
                 timescale_factor, record):
        PartitionedVertex.__init__(self, resources_required, label,
                                   constraints)
        AbstractSpikeRecordableSubvertex.__init__(self)
        AbstractDataSpecablePartitionedVertex.__init__(self)
        AbstractExecutable.__init__(self)
        HasNMachineTimesteps.__init__(self)
        AbstractOutgoingEdgeSameContiguousKeysRestrictor.__init__(self)
        self._spike_source_poisson = spike_source_poisson
        self._vertex_slice = vertex_slice
        self._machine_time_step = machine_time_step
        self._timescale_factor = timescale_factor
        self._record = record

    def generate_data_spec(
            self, placement, graph, routing_info, ip_tags, reverse_ip_tags,
            report_folder, output_folder, write_text_specs):

        data_path, data_writer = data_spec_utilities.get_data_spec_data_writer(
            placement, output_folder)
        report_writer = None
        if write_text_specs:
            report_writer = data_spec_utilities.get_data_spec_report_writer(
                placement, report_folder)
        spec = DataSpecificationGenerator(data_writer, report_writer)

        spike_hist_buff_sz = \
            self._spike_source_poisson.get_spike_recording_region_size(
                self.n_machine_timesteps, self._vertex_slice)
        poisson_params_sz = self._spike_source_poisson.get_params_bytes(
            self._vertex_slice)

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        # Reserve SDRAM space for memory areas:
        self._reserve_memory_regions(
            spec, poisson_params_sz, spike_hist_buff_sz)

        simulation_utilities.simulation_write_header(
            spec, self._POISSON_SPIKE_SOURCE_REGIONS.HEADER.value,
            "spike_source_poisson", self._machine_time_step,
            self._timescale_factor, self.no_machine_time_steps)

        # Every subedge should have the same key
        keys_and_masks = routing_info.get_keys_and_masks_from_subedge(
            graph.outgoing_subedges_from_subvertex(self)[0])
        key = keys_and_masks[0].key

        self._write_poisson_parameters(spec, key, self._vertex_slice.n_atoms)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()
        if write_text_specs:
            report_writer.close()

        return data_path

    def _reserve_memory_regions(
            self, spec, poisson_params_sz, spike_hist_buff_sz):
        """ Reserve memory regions for poisson source parameters and output\
            buffer.

        :param spec:
        :param poisson_params_sz:
        :param spike_hist_buff_sz:
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        simulation_utilities.simulation_reserve_header(
            spec, self._POISSON_SPIKE_SOURCE_REGIONS.HEADER.value)
        spec.reserve_memory_region(
            region=self._POISSON_SPIKE_SOURCE_REGIONS.RECORDING_DATA.value,
            size=self._SPIKE_HISTORY_CONFIGURATION_SIZE, label='recording')
        spec.reserve_memory_region(
            region=self._POISSON_SPIKE_SOURCE_REGIONS
                       .POISSON_PARAMS_REGION.value,
            size=poisson_params_sz, label='PoissonParams')
        if spike_hist_buff_sz > 0:
            spec.reserve_memory_region(
                region=self._POISSON_SPIKE_SOURCE_REGIONS
                           .SPIKE_HISTORY_REGION.value,
                size=spike_hist_buff_sz, label='spikeHistBuffer',
                empty=True)

    def _write_poisson_parameters(self, spec, key, num_neurons):
        """ Generate Parameter data for Poisson spike sources:

        :param spec:
        :param key:
        :param num_neurons:
        :return:
        """
        spec.comment("\nWriting Parameters for {} poisson sources:\n"
                     .format(num_neurons))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            region=self._POISSON_SPIKE_SOURCE_REGIONS
                       .POISSON_PARAMS_REGION.value)

        # Write Key info for this core:
        if key is None:
            # if theres no key, then two falses will cover it.
            spec.write_value(data=0)
            spec.write_value(data=0)
        else:
            # has a key, thus set has key to 1 and then add key
            spec.write_value(data=1)
            spec.write_value(data=key)

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
            exp_minus_lamda = math.exp(-1.0 * spikes_per_tick)
            start_scaled = int(start_val * 1000.0 / self._machine_time_step)
            end_scaled = int(end_val * 1000.0 / self._machine_time_step)
            spec.write_value(data=neuron_id, data_type=DataType.UINT32)
            spec.write_value(data=start_scaled, data_type=DataType.UINT32)
            spec.write_value(data=end_scaled, data_type=DataType.UINT32)
            spec.write_value(data=exp_minus_lamda, data_type=DataType.U032)
        return

    def get_binary_file_name(self):
        """
        """
        return "spike_source_poisson.aplx"

    def get_spike_recording_region(self):
        return self._POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION
