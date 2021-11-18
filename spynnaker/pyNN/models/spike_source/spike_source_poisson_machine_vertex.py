# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import struct
from enum import Enum
import numpy

from data_specification.enums import DataType
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_SECOND_CONVERSION, SIMULATION_N_BYTES, BYTES_PER_WORD,
    MICRO_TO_MILLISECOND_CONVERSION, BYTES_PER_SHORT)
from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary, AbstractSupportsDatabaseInjection,
    AbstractRewritesDataSpecification, AbstractGeneratesDataSpecification)
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.interface.profiling import (
    AbstractHasProfileData, profile_utils)
from spinn_front_end_common.interface.profiling.profile_utils import (
    get_profiling_data)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import (
    AbstractMaxSpikes, AbstractReadParametersBeforeSet)
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.constants import (
    LIVE_POISSON_CONTROL_PARTITION_ID)
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.models.abstract_models import (
    SendsSynapticInputsOverSDRAM, ReceivesSynapticInputsOverSDRAM)
from spynnaker.pyNN.exceptions import SynapticConfigurationException


def _flatten(alist):
    for item in alist:
        if hasattr(item, "__iter__"):
            yield from _flatten(item)
        else:
            yield item


def get_rates_bytes(vertex_slice, rate_data):
    """ Gets the size of the Poisson rates in bytes

    :param ~pacman.model.graphs.common.Slice vertex_slice:
    :rtype: int
    """
    n_rates = sum(len(rate_data[i]) for i in range(
        vertex_slice.lo_atom, vertex_slice.hi_atom + 1))
    return ((vertex_slice.n_atoms * PARAMS_WORDS_PER_NEURON) +
            (n_rates * PARAMS_WORDS_PER_RATE)) * BYTES_PER_WORD


def get_sdram_edge_params_bytes(vertex_slice):
    """ Gets the size of the Poisson SDRAM region in bytes
    :param ~pacman.model.graphs.common.Slice vertex_slice:
    :rtype: int
    """
    return SDRAM_EDGE_PARAMS_BASE_BYTES + (
        vertex_slice.n_atoms * SDRAM_EDGE_PARAMS_BYTES_PER_WEIGHT)


# uint32_t n_rates; uint32_t index
PARAMS_WORDS_PER_NEURON = 2

# start_scaled, end_scaled, next_scaled, is_fast_source, exp_minus_lambda,
# sqrt_lambda, isi_val, time_to_spike
PARAMS_WORDS_PER_RATE = 8

# The size of each weight to be stored for SDRAM transfers
SDRAM_EDGE_PARAMS_BYTES_PER_WEIGHT = BYTES_PER_SHORT

# SDRAM edge param base size:
# 1. address, 2. size of transfer,
# 3. offset to start writing, 4. VLA of weights (not counted here)
SDRAM_EDGE_PARAMS_BASE_BYTES = 3 * BYTES_PER_WORD

_ONE_WORD = struct.Struct("<I")
_FOUR_WORDS = struct.Struct("<4I")


class SpikeSourcePoissonMachineVertex(
        MachineVertex, AbstractReceiveBuffersToHost,
        ProvidesProvenanceDataFromMachineImpl,
        AbstractSupportsDatabaseInjection, AbstractHasProfileData,
        AbstractHasAssociatedBinary, AbstractRewritesDataSpecification,
        AbstractGeneratesDataSpecification, AbstractReadParametersBeforeSet,
        SendsSynapticInputsOverSDRAM):

    __slots__ = [
        "__buffered_sdram_per_timestep",
        "__is_recording",
        "__minimum_buffer_sdram",
        "__resources",
        "__change_requires_neuron_parameters_reload",
        "__sdram_partition"]

    class POISSON_SPIKE_SOURCE_REGIONS(Enum):
        SYSTEM_REGION = 0
        POISSON_PARAMS_REGION = 1
        RATES_REGION = 2
        SPIKE_HISTORY_REGION = 3
        PROVENANCE_REGION = 4
        PROFILER_REGION = 5
        TDMA_REGION = 6
        SDRAM_EDGE_PARAMS = 7

    PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "PROB_FUNC"}

    _PoissonStruct = Struct([
        DataType.UINT32,  # Start Scaled
        DataType.UINT32,  # End Scaled
        DataType.UINT32,  # Next Scaled
        DataType.UINT32,  # is_fast_source
        DataType.U032,  # exp^(-spikes_per_tick)
        DataType.S1615,  # sqrt(spikes_per_tick)
        DataType.UINT32,  # inter-spike-interval
        DataType.UINT32])  # timesteps to next spike

    class EXTRA_PROVENANCE_DATA_ENTRIES(Enum):
        """ Entries for the provenance data generated by standard neuron \
            models.
        """
        #: The number of pre-synaptic events
        TDMA_MISSED_SLOTS = 0

    # The maximum timestep - this is the maximum value of a uint32
    _MAX_TIMESTEP = 0xFFFFFFFF

    # as suggested by MH (between Exp and Knuth)
    SLOW_RATE_PER_TICK_CUTOFF = 0.01

    # between Knuth algorithm and Gaussian approx.
    FAST_RATE_PER_TICK_CUTOFF = 10

    # 1. uint32_t has_key; 2. uint32_t key;
    # 3. uint32_t set_rate_neuron_id_mask;
    # 4. UFRACT seconds_per_tick; 5. REAL ticks_per_second;
    # 6. REAL slow_rate_per_tick_cutoff; 7. REAL fast_rate_per_tick_cutoff;
    # 8. uint32_t first_source_id; 9. uint32_t n_spike_sources;
    # 10. uint32_t max_spikes_per_timestep;
    # 11,12,13,14 mars_kiss64_seed_t (uint[4]) spike_source_seed;
    PARAMS_BASE_WORDS = 14

    # Seed offset in parameters and size on bytes
    SEED_OFFSET_BYTES = 10 * 4
    SEED_SIZE_BYTES = 4 * 4

    def __init__(
            self, resources_required, is_recording, constraints=None,
            label=None, app_vertex=None, vertex_slice=None, slice_index=None):
        # pylint: disable=too-many-arguments
        super().__init__(
            label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=vertex_slice)
        self.__is_recording = is_recording
        self.__resources = resources_required
        self.__change_requires_neuron_parameters_reload = False
        self.__sdram_partition = None
        self.__slice_index = slice_index

    def set_sdram_partition(self, sdram_partition):
        self.__sdram_partition = sdram_partition

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self.__resources

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self):
        return self.POISSON_SPIKE_SOURCE_REGIONS.PROVENANCE_REGION.value

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self):
        return 1

    @overrides(AbstractReceiveBuffersToHost.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        if self.__is_recording:
            return [0]
        return []

    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, txrx, placement):
        return locate_memory_region_for_placement(
            placement,
            self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value,
            txrx)

    @property
    @overrides(AbstractSupportsDatabaseInjection.is_in_injection_mode)
    def is_in_injection_mode(self):
        # pylint: disable=no-value-for-parameter
        return self._is_in_injection_mode()

    @inject_items({"graph": "MachineGraph"})
    def _is_in_injection_mode(self, graph):
        # pylint: disable=arguments-differ
        in_edges = graph.get_edges_ending_at_vertex_with_partition_name(
            self, LIVE_POISSON_CONTROL_PARTITION_ID)
        if len(in_edges) > 1:
            raise ConfigurationException(
                "Poisson source can only have one incoming control")
        return len(in_edges) == 1

    @overrides(AbstractHasProfileData.get_profile_data)
    def get_profile_data(self, transceiver, placement):
        return get_profiling_data(
            self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION.value,
            self.PROFILE_TAG_LABELS, transceiver, placement)

    @overrides(ProvidesProvenanceDataFromMachineImpl.
               parse_extra_provenance_items)
    def parse_extra_provenance_items(self, label, x, y, p, provenance_data):
        n_times_tdma_fell_behind = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.TDMA_MISSED_SLOTS.value]

        yield self._app_vertex.get_tdma_provenance_item(
            x, y, p, label, n_times_tdma_fell_behind)

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "spike_source_poisson.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractMaxSpikes.max_spikes_per_second)
    def max_spikes_per_second(self):
        return self.app_vertex.max_rate

    @overrides(AbstractMaxSpikes.max_spikes_per_ts)
    def max_spikes_per_ts(self):
        return self.app_vertex.max_spikes_per_ts()

    @inject_items({"first_machine_time_step": "FirstMachineTimeStep"})
    @overrides(AbstractRewritesDataSpecification.reload_required,
               additional_arguments={"first_machine_time_step"})
    def reload_required(self, first_machine_time_step):
        # pylint: disable=arguments-differ
        return (self.__change_requires_neuron_parameters_reload or
                first_machine_time_step == 0)

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value):
        self.__change_requires_neuron_parameters_reload = new_value

    @inject_items({
        "routing_info": "RoutingInfos",
        "graph": "MachineGraph",
        "first_machine_time_step": "FirstMachineTimeStep"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={
            "routing_info", "graph", "first_machine_time_step"})
    def regenerate_data_specification(
            self, spec, placement, routing_info, graph,
            first_machine_time_step):
        """
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
        :param ~pacman.model.graphs.machine.MachineGraph graph:
        :param int first_machine_time_step:
        """
        # pylint: disable=too-many-arguments, arguments-differ

        # reserve the neuron parameters data region
        self._reserve_poisson_params_rates_region(placement, spec)

        # write parameters
        self._write_poisson_parameters(
            spec=spec, graph=graph, placement=placement,
            routing_info=routing_info)

        # write rates
        self._write_poisson_rates(spec, first_machine_time_step)

        # end spec
        spec.end_specification()

    @inject_items({
        "routing_info": "RoutingInfos",
        "data_n_time_steps": "DataNTimeSteps",
        "graph": "MachineGraph",
        "first_machine_time_step": "FirstMachineTimeStep"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "routing_info", "data_n_time_steps", "graph",
            "first_machine_time_step"
        }
    )
    def generate_data_specification(
            self, spec, placement, routing_info, data_n_time_steps, graph,
            first_machine_time_step):
        """
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
        :param int data_n_time_steps:
        :param ~pacman.model.graphs.machine.MachineGraph graph:
        :param int first_machine_time_step:
        """
        # pylint: disable=too-many-arguments, arguments-differ

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        # Reserve SDRAM space for memory areas:
        self.reserve_memory_regions(spec, placement)

        # write setup data
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            placement.vertex.get_binary_file_name()))

        # write recording data
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value)
        sdram = self._app_vertex.get_recording_sdram_usage(self.vertex_slice)
        recorded_region_sizes = [sdram.get_total_sdram(data_n_time_steps)]
        spec.write_array(recording_utilities.get_recording_header_array(
            recorded_region_sizes))

        # write parameters
        self._write_poisson_parameters(
            spec, graph, placement, routing_info)

        # write rates
        self._write_poisson_rates(spec, first_machine_time_step)

        # write profile data
        profile_utils.write_profile_region_data(
            spec, self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION.value,
            self._app_vertex.n_profile_samples)

        # write tdma params
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.TDMA_REGION.value)
        spec.write_array(
            self._app_vertex.generate_tdma_data_specification_data(
                self.__slice_index))

        # write SDRAM edge parameters
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SDRAM_EDGE_PARAMS.value)
        if self.__sdram_partition is None:
            spec.write_array([0, 0, 0])
        else:
            size = self.__sdram_partition.get_sdram_size_of_region_for(self)
            proj = self._app_vertex.outgoing_projections[0]
            synapse_info = proj._synapse_information
            spec.write_value(
                self.__sdram_partition.get_sdram_base_address_for(self))
            spec.write_value(size)

            # Work out the offset into the data to write from, based on the
            # synapse type in use
            synapse_type = synapse_info.synapse_type
            offset = synapse_type * self.vertex_slice.n_atoms
            spec.write_value(offset)

            # If we are here, the connector must be one-to-one so create
            # the synapses and then store the scaled weights
            connections = synapse_info.connector.create_synaptic_block(
                None, None, self.vertex_slice, self.vertex_slice, synapse_type,
                synapse_info)
            weight_scales = (
                next(iter(self.__sdram_partition.edges))
                .post_vertex.weight_scales)
            weights = connections["weight"] * weight_scales[synapse_type]
            weights = numpy.rint(numpy.abs(weights)).astype("uint16")
            if len(weights) % 2 != 0:
                padding = numpy.array([0], dtype="uint16")
                weights = numpy.concatenate((weights, padding))
            spec.write_array(weights.view("uint32"))

        # End-of-Spec:
        spec.end_specification()

    def _write_poisson_rates(
            self, spec, first_machine_time_step):
        """ Generate Rate data for Poisson spike sources

        :param ~data_specification.DataSpecification spec:
            the data specification writer
        :param int first_machine_time_step:
            First machine time step to start from the correct index
        """
        spec.comment("\nWriting Rates for {} poisson sources:\n"
                     .format(self.vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.RATES_REGION.value)

        # Extract the data on which to work and convert to appropriate form
        starts = numpy.array(list(_flatten(
            self._app_vertex.start[self.vertex_slice.as_slice]))).astype(
                "float")
        durations = numpy.array(list(_flatten(
            self._app_vertex.duration[self.vertex_slice.as_slice]))).astype(
                "float")
        local_rates = self._app_vertex.rates[self.vertex_slice.as_slice]
        n_rates = numpy.array([len(r) for r in local_rates])
        splits = numpy.cumsum(n_rates)
        rates = numpy.array(list(_flatten(local_rates)))
        time_to_spike = numpy.array(list(_flatten(
            self._app_vertex.time_to_spike[
                self.vertex_slice.as_slice]))).astype("u4")
        rate_change = self._app_vertex.rate_change[self.vertex_slice.as_slice]

        # Convert start times to start time steps
        starts_scaled = self._convert_ms_to_n_timesteps(starts)

        # Convert durations to end time steps, using the maximum for "None"
        # duration (which means "until the end")
        no_duration = numpy.isnan(durations)
        durations_filtered = numpy.where(no_duration, 0, durations)
        ends_scaled = self._convert_ms_to_n_timesteps(
            durations_filtered) + starts_scaled
        ends_scaled = (
            numpy.where(no_duration, self._MAX_TIMESTEP, ends_scaled))

        # Work out the timestep at which the next rate activates, using
        # the maximum value at the end (meaning there is no "next")
        starts_split = numpy.array_split(starts_scaled, splits)
        next_scaled = numpy.concatenate(
            [numpy.append(s[1:], self._MAX_TIMESTEP)
             for s in starts_split[:-1]])

        # Compute the spikes per tick for each rate for each atom
        spikes_per_tick = rates * (
                SpynnakerDataView().simulation_time_step_us /
                MICRO_TO_SECOND_CONVERSION)
        # Determine the properties of the sources
        is_fast_source = spikes_per_tick >= self.SLOW_RATE_PER_TICK_CUTOFF
        is_faster_source = spikes_per_tick >= self.FAST_RATE_PER_TICK_CUTOFF
        not_zero = spikes_per_tick > 0
        # pylint: disable=assignment-from-no-return
        is_slow_source = numpy.logical_not(is_fast_source)

        # Compute the e^-(spikes_per_tick) for fast sources to allow fast
        # computation of the Poisson distribution to get the number of
        # spikes per timestep
        exp_minus_lambda = DataType.U032.encode_as_numpy_int_array(
            numpy.where(is_fast_source, numpy.exp(-1.0 * spikes_per_tick), 0))

        # Compute sqrt(lambda) for "faster" sources to allow Gaussian
        # approximation of the Poisson distribution to get the number of
        # spikes per timestep
        sqrt_lambda = DataType.S1615.encode_as_numpy_int_array(
            numpy.where(is_faster_source, numpy.sqrt(spikes_per_tick), 0))

        # Compute the inter-spike-interval for slow sources to get the
        # average number of timesteps between spikes
        isi_val = numpy.where(
            not_zero & is_slow_source,
            (1.0 / spikes_per_tick).astype(int), 0).astype("uint32")

        # Reuse the time-to-spike read from the machine (if has been run)
        # or don't if the rate has since been changed
        time_to_spike_split = numpy.array_split(time_to_spike, splits)
        time_to_spike = numpy.concatenate(
            [t if rate_change[i] else numpy.repeat(0, len(t))
             for i, t in enumerate(time_to_spike_split[:-1])])

        # Turn the fast source booleans into uint32
        is_fast_source = is_fast_source.astype("uint32")

        # Group together the rate data for the core by rate
        core_data = numpy.dstack((
            starts_scaled, ends_scaled, next_scaled, is_fast_source,
            exp_minus_lambda, sqrt_lambda, isi_val, time_to_spike))[0]

        # Group data by neuron id
        core_data_split = numpy.array_split(core_data, splits)

        # Work out the index where the core should start based on the given
        # first timestep
        ends_scaled_split = numpy.array_split(ends_scaled, splits)
        indices = [numpy.argmax(e > first_machine_time_step)
                   for e in ends_scaled_split[:-1]]

        # Build the final data for this core, and write it
        final_data = numpy.concatenate([
            numpy.concatenate(([len(d), indices[i]], numpy.concatenate(d)))
            for i, d in enumerate(core_data_split[:-1])])
        spec.write_array(final_data)

    def _write_poisson_parameters(self, spec, graph, placement, routing_info):
        """ Generate Parameter data for Poisson spike sources

        :param ~data_specification.DataSpecification spec:
            the data specification writer
        :param ~pacman.model.graphs.machine.MachineGraph graph:
        :param ~pacman.model.placements.Placement placement:
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
        """
        # pylint: disable=too-many-arguments, too-many-locals
        spec.comment("\nWriting Parameters for {} poisson sources:\n"
                     .format(self.vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value)

        # Write Key info for this core:
        key = routing_info.get_first_key_from_pre_vertex(
            placement.vertex, constants.SPIKE_PARTITION_ID)
        spec.write_value(data=1 if key is not None else 0)
        spec.write_value(data=key if key is not None else 0)

        # Write the incoming mask if there is one
        in_edges = graph.get_edges_ending_at_vertex_with_partition_name(
            placement.vertex, constants.LIVE_POISSON_CONTROL_PARTITION_ID)
        if len(in_edges) > 1:
            raise ConfigurationException(
                "Only one control edge can end at a Poisson vertex")
        incoming_mask = 0
        if len(in_edges) == 1:
            in_edge = in_edges[0]

            # Get the mask of the incoming keys
            incoming_mask = \
                routing_info.get_routing_info_for_edge(in_edge).first_mask
            incoming_mask = ~incoming_mask & 0xFFFFFFFF
        spec.write_value(incoming_mask)

        view = SpynnakerDataView()
        # Write the number of seconds per timestep (unsigned long fract)
        spec.write_value(
            data=view.simulation_time_step_us / MICRO_TO_SECOND_CONVERSION,
            data_type=DataType.U032)

        # Write the number of timesteps per second (integer)
        spec.write_value(
            data=int(
                MICRO_TO_SECOND_CONVERSION / view.simulation_time_step_us))

        # Write the slow-rate-per-tick-cutoff (accum)
        spec.write_value(
            data=self.SLOW_RATE_PER_TICK_CUTOFF, data_type=DataType.S1615)

        # Write the fast-rate-per-tick-cutoff (accum)
        spec.write_value(
            data=self.FAST_RATE_PER_TICK_CUTOFF, data_type=DataType.S1615)

        # Write the lo_atom ID
        spec.write_value(data=self.vertex_slice.lo_atom)

        # Write the number of sources
        spec.write_value(data=self.vertex_slice.n_atoms)

        # Write the maximum spikes per tick
        spec.write_value(data=self.max_spikes_per_ts())

        # Write the random seed (4 words), generated randomly!
        for value in self._app_vertex.kiss_seed(self.vertex_slice):
            spec.write_value(data=value)

    def reserve_memory_regions(self, spec, placement):
        """ Reserve memory regions for Poisson source parameters and output\
            buffer.

        :param ~data_specification.DataSpecificationGenerator spec:
            the data specification writer
        :param ~pacman.model.placements.Placement placement:
            the location this vertex resides on in the machine
        :return: None
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value,
            size=SIMULATION_N_BYTES,
            label='setup')

        # reserve poisson parameters and rates DSG region
        self._reserve_poisson_params_rates_region(placement, spec)

        spec.reserve_memory_region(
            region=(
                self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value),
            size=recording_utilities.get_recording_header_size(1),
            label="Recording")

        profile_utils.reserve_profile_region(
            spec, self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION.value,
            self._app_vertex.n_profile_samples)

        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.TDMA_REGION.value,
            label="tdma_region",
            size=self._app_vertex.tdma_sdram_size_in_bytes)

        placement.vertex.reserve_provenance_data_region(spec)

        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.SDRAM_EDGE_PARAMS.value,
            label="sdram edge params",
            size=get_sdram_edge_params_bytes(self.vertex_slice))

    def _reserve_poisson_params_rates_region(self, placement, spec):
        """ Allocate space for the Poisson parameters and rates regions as\
            they can be reused for setters after an initial run

        :param ~pacman.models.placements.Placement placement:
            the location on machine for this vertex
        :param ~data_specification.DataSpecification spec: the DSG writer
        :return: None
        """
        spec.reserve_memory_region(
            region=(
                self.POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value),
            size=self.PARAMS_BASE_WORDS * BYTES_PER_WORD,
            label="PoissonParams")
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.RATES_REGION.value,
            size=get_rates_bytes(
                placement.vertex.vertex_slice, self._app_vertex.rates),
            label='PoissonRates')

    @staticmethod
    def _convert_ms_to_n_timesteps(value):
        return numpy.round(
            value * (MICRO_TO_MILLISECOND_CONVERSION /
                     SpynnakerDataView().simulation_time_step_us)
        ).astype("uint32")

    def poisson_param_region_address(self, placement, transceiver):
        return helpful_functions.locate_memory_region_for_placement(
            placement,
            self.POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value,
            transceiver)

    def poisson_rate_region_address(self, placement, transceiver):
        return helpful_functions.locate_memory_region_for_placement(
            placement,
            self.POISSON_SPIKE_SOURCE_REGIONS.RATES_REGION.value,
            transceiver)

    @overrides(
        AbstractReadParametersBeforeSet.read_parameters_from_machine)
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):

        # locate SDRAM address where parameters are stored
        poisson_params = self.poisson_param_region_address(
            placement, transceiver)
        seed_array = _FOUR_WORDS.unpack_from(transceiver.read_memory(
            placement.x, placement.y, poisson_params + self.SEED_OFFSET_BYTES,
            self.SEED_SIZE_BYTES))
        self._app_vertex.update_kiss_seed(vertex_slice, seed_array)

        # locate SDRAM address where the rates are stored
        poisson_rate_region_sdram_address = (
            self.poisson_rate_region_address(placement, transceiver))

        # get size of poisson params
        size_of_region = get_rates_bytes(vertex_slice, self._app_vertex.rates)

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y,
            poisson_rate_region_sdram_address, size_of_region)

        # For each atom, read the number of rates and the rate parameters
        offset = 0
        for i in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1):
            n_values, = _ONE_WORD.unpack_from(byte_array, offset)
            offset += 4

            # Skip reading the index, as it will be recalculated on data write
            offset += 4

            (_start, _end, _next, is_fast_source, exp_minus_lambda,
             sqrt_lambda, isi, time_to_next_spike) = (
                 self._PoissonStruct.read_data(byte_array, offset, n_values))
            offset += (
                self._PoissonStruct.get_size_in_whole_words(
                    n_values) * BYTES_PER_WORD)

            # Work out the spikes per tick depending on if the source is
            # slow (isi), fast (exp) or faster (sqrt)
            is_fast_source = is_fast_source == 1.0
            spikes_per_tick = numpy.zeros(len(is_fast_source), dtype="float")
            spikes_per_tick[is_fast_source] = numpy.log(
                exp_minus_lambda[is_fast_source]) * -1.0
            is_faster_source = sqrt_lambda > 0
            # pylint: disable=assignment-from-no-return
            spikes_per_tick[is_faster_source] = numpy.square(
                sqrt_lambda[is_faster_source])
            slow_elements = isi > 0
            spikes_per_tick[slow_elements] = 1.0 / isi[slow_elements]

            # Convert spikes per tick to rates
            self._app_vertex.rates.set_value_by_id(
                i,
                spikes_per_tick *
                (MICRO_TO_SECOND_CONVERSION /
                 SpynnakerDataView.simulation_time_step_us))

            # Store the updated time until next spike so that it can be
            # rewritten when the parameters are loaded
            self._app_vertex.time_to_spike.set_value_by_id(
                i, time_to_next_spike)

    @overrides(SendsSynapticInputsOverSDRAM.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge):
        if isinstance(sdram_machine_edge.post_vertex,
                      ReceivesSynapticInputsOverSDRAM):
            return sdram_machine_edge.post_vertex.n_bytes_for_transfer
        raise SynapticConfigurationException(
            "Unknown post vertex type in edge {}".format(sdram_machine_edge))
