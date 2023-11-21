# Copyright (c) 2016 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
from enum import IntEnum
import numpy
from numpy import uint16, uint32
import struct
from typing import (
    Iterable, List, Optional, Sequence, Sized, TypeVar, Union,
    cast, TYPE_CHECKING)

from spinn_utilities.overrides import overrides
from spinnman.model.enums import ExecutableType
from pacman.model.graphs import AbstractEdgePartition
from pacman.model.graphs.machine import (
    MachineVertex, AbstractSDRAMPartition, SDRAMMachineEdge)
from pacman.model.graphs.common import Slice
from pacman.model.resources import AbstractSDRAM
from pacman.model.placements import Placement
from pacman.utilities.utility_calls import get_field_based_keys
from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationBase, DataSpecificationGenerator,
    DataSpecificationReloader)
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.utilities.constants import (
    SIMULATION_N_BYTES, BYTES_PER_WORD, BYTES_PER_SHORT)
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary,
    AbstractRewritesDataSpecification, AbstractGeneratesDataSpecification)
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.interface.profiling import (
    AbstractHasProfileData, ProfileData, profile_utils)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import AbstractMaxSpikes
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models import (
    SendsSynapticInputsOverSDRAM, ReceivesSynapticInputsOverSDRAM)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.utilities.constants import (
    LIVE_POISSON_CONTROL_PARTITION_ID)
if TYPE_CHECKING:
    from .spike_source_poisson_vertex import SpikeSourcePoissonVertex
    from spynnaker.pyNN.models.neural_projections import SynapseInformation
    from spynnaker.pyNN.models.neural_projections.connectors import (
        AbstractGenerateConnectorOnHost)

#: :meta private:
T = TypeVar("T")


def _flatten(alist: Iterable[Union[T, Iterable[T]]]) -> Iterable[T]:
    for item in alist:
        if hasattr(item, "__iter__"):
            yield from _flatten(item)
        else:
            yield item


def get_n_rates(vertex_slice: Slice, rate_data: Sequence[Sized]) -> int:
    """
    How many rates there are to be stored in total.
    """
    return sum(len(rate_data[i]) for i in range(
        vertex_slice.lo_atom, vertex_slice.hi_atom + 1))


def get_params_bytes(n_atoms: int) -> int:
    """
    Gets the size of the Poisson parameters in bytes.

    :param int n_atoms: How many atoms to account for
    :rtype: int
    """
    return (PARAMS_BASE_WORDS + n_atoms) * BYTES_PER_WORD


def get_rates_bytes(n_atoms: int, n_rates: int) -> int:
    """
    Gets the size of the Poisson rates in bytes.

    :param int n_atoms: How many atoms to account for
    :param int n_rates: How many rates to account for
    :rtype: int
    """
    return ((n_atoms * PARAMS_WORDS_PER_NEURON) +
            (n_rates * PARAMS_WORDS_PER_RATE)) * BYTES_PER_WORD


def get_expander_rates_bytes(n_atoms: int, n_rates: int) -> int:
    """
    Gets the size of the Poisson rates in bytes.

    :param int n_atoms: How many atoms to account for
    :param int n_rates: How many rates to account for
    :rtype: int
    """
    return ((n_atoms * EXPANDER_WORDS_PER_NEURON) +
            (n_rates * PARAMS_WORDS_PER_RATE) +
            EXPANDER_HEADER_WORDS) * BYTES_PER_WORD


def get_sdram_edge_params_bytes(vertex_slice: Slice) -> int:
    """
    Gets the size of the Poisson SDRAM region in bytes.

    :param ~pacman.model.graphs.common.Slice vertex_slice:
    :rtype: int
    """
    return SDRAM_EDGE_PARAMS_BASE_BYTES + (
        vertex_slice.n_atoms * SDRAM_EDGE_PARAMS_BYTES_PER_WEIGHT)


def _u3232_to_uint64(array: numpy.ndarray) -> numpy.ndarray:
    """
    Convert data to be written in U3232 to uint64 array.
    """
    return numpy.round(array * float(DataType.U3232.scale)).astype(
        DataType.U3232.numpy_typename)


# 1. uint32_t has_key;
# 2. uint32_t set_rate_neuron_id_mask;
# 3. UFRACT seconds_per_tick; 4. REAL ticks_per_second;
# 5. REAL slow_rate_per_tick_cutoff; 6. REAL fast_rate_per_tick_cutoff;
# 7. unt32_t first_source_id; 8. uint32_t n_spike_sources;
# 9. uint32_t max_spikes_per_timestep;
# 10. uint32_t n_colour_bits;
# 11,12,13,14 mars_kiss64_seed_t (uint[4]) spike_source_seed;
# 15. Rate changed flag
PARAMS_BASE_WORDS = 15

# uint32_t n_rates; uint32_t index
PARAMS_WORDS_PER_NEURON = 2

# unsigned long accum rate, start, duration
PARAMS_WORDS_PER_RATE = 6

# uint32_t count; one per neuron in worst case (= every neuron different)
EXPANDER_WORDS_PER_NEURON = PARAMS_WORDS_PER_NEURON + 1

# uint32_t n_items
EXPANDER_HEADER_WORDS = 2

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
        AbstractHasProfileData,
        AbstractHasAssociatedBinary, AbstractRewritesDataSpecification,
        AbstractGeneratesDataSpecification,
        SendsSynapticInputsOverSDRAM):
    """
    Vertex that implements a Poisson-distributed spike source.
    """

    __slots__ = (
        "__buffered_sdram_per_timestep",
        "__is_recording",
        "__minimum_buffer_sdram",
        "__sdram",
        "__sdram_partition",
        "__rate_changed")

    class POISSON_SPIKE_SOURCE_REGIONS(IntEnum):
        """
        Memory region IDs for the the Poisson source code.
        """
        #: System control information (simulation timestep, etc.)
        SYSTEM_REGION = 0
        #: The parameters for the Poisson generator.
        POISSON_PARAMS_REGION = 1
        #: Spike rates (and the times at which they apply).
        RATES_REGION = 2
        #: Record of when spikes were actually sent.
        SPIKE_HISTORY_REGION = 3
        #: Provenance data.
        PROVENANCE_REGION = 4
        #: Profiler data.
        PROFILER_REGION = 5
        #: Parameters for an SDRAM edge.
        SDRAM_EDGE_PARAMS = 6
        #: Data for the on-chip connection generator binaries.
        EXPANDER_REGION = 7

    PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "PROB_FUNC"}

    # The maximum timestep - this is the maximum value of a uint32
    _MAX_TIMESTEP = 0xFFFFFFFF

    # as suggested by MH (between Exp and Knuth)
    SLOW_RATE_PER_TICK_CUTOFF = 0.01

    # between Knuth algorithm and Gaussian approx.
    FAST_RATE_PER_TICK_CUTOFF = 10

    # Seed offset in parameters and size on bytes
    SEED_SIZE_BYTES = 4 * BYTES_PER_WORD
    SEED_OFFSET_BYTES = (PARAMS_BASE_WORDS * 4) - SEED_SIZE_BYTES

    def __init__(
            self, sdram: AbstractSDRAM, is_recording: bool,
            label: Optional[str], app_vertex: SpikeSourcePoissonVertex,
            vertex_slice: Slice):
        # pylint: disable=too-many-arguments
        super().__init__(
            label, app_vertex=app_vertex, vertex_slice=vertex_slice)
        self.__is_recording = is_recording
        self.__sdram = sdram
        self.__sdram_partition: Optional[AbstractSDRAMPartition] = None
        self.__rate_changed = True

    @property
    def _pop_vertex(self) -> SpikeSourcePoissonVertex:
        return cast('SpikeSourcePoissonVertex', self.app_vertex)

    def set_sdram_partition(self, sdram_partition: AbstractSDRAMPartition):
        self.__sdram_partition = sdram_partition

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self) -> AbstractSDRAM:
        return self.__sdram

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self) -> int:
        return self.POISSON_SPIKE_SOURCE_REGIONS.PROVENANCE_REGION

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self) -> int:
        return 0

    @overrides(AbstractReceiveBuffersToHost.get_recorded_region_ids)
    def get_recorded_region_ids(self) -> List[int]:
        if self.__is_recording:
            return [0]
        return []

    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, placement: Placement) -> int:
        return locate_memory_region_for_placement(
            placement, self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION)

    @overrides(AbstractHasProfileData.get_profile_data)
    def get_profile_data(self, placement: Placement) -> ProfileData:
        return profile_utils.get_profiling_data(
            self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION,
            self.PROFILE_TAG_LABELS, placement)

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self) -> str:
        return "spike_source_poisson.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self) -> ExecutableType:
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractMaxSpikes.max_spikes_per_second)
    def max_spikes_per_second(self) -> float:
        return self._pop_vertex.max_rate

    @overrides(AbstractMaxSpikes.max_spikes_per_ts)
    def max_spikes_per_ts(self) -> float:
        return self._pop_vertex.max_spikes_per_ts()

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self) -> bool:
        if self.__rate_changed:
            return True
        return SpynnakerDataView.get_first_machine_time_step() == 0

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value: bool):
        self.__rate_changed = new_value

    @overrides(AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(
            self, spec: DataSpecificationReloader, placement: Placement):
        # write rates
        self._write_poisson_rates(spec)

        # end spec
        spec.end_specification()

    @staticmethod
    def __conn(synapse_info: SynapseInformation
               ) -> AbstractGenerateConnectorOnHost:
        return cast(
            'AbstractGenerateConnectorOnHost', synapse_info.connector)

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(
            self, spec: DataSpecificationGenerator, placement: Placement):
        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")
        # if we are here, the rates have changed!
        self.__rate_changed = True

        # write setup data
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION,
            size=SIMULATION_N_BYTES, label='setup')
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name()))

        # write recording data
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION,
            size=recording_utilities.get_recording_header_size(1),
            label="Recording")
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION)
        sdram = self._pop_vertex.get_recording_sdram_usage(self.vertex_slice)
        recorded_region_sizes = [sdram.get_total_sdram(
            SpynnakerDataView.get_max_run_time_steps())]
        spec.write_array(recording_utilities.get_recording_header_array(
            recorded_region_sizes))

        # Write provenence space
        self.reserve_provenance_data_region(spec)

        # write parameters
        self._write_poisson_parameters(spec)

        # write rates
        self._write_poisson_rates(spec)

        # write profile data
        profile_utils.reserve_profile_region(
            spec, self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION,
            self._pop_vertex.n_profile_samples)
        profile_utils.write_profile_region_data(
            spec, self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION,
            self._pop_vertex.n_profile_samples)

        # write SDRAM edge parameters
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.SDRAM_EDGE_PARAMS,
            label="sdram edge params",
            size=get_sdram_edge_params_bytes(self.vertex_slice))
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SDRAM_EDGE_PARAMS)
        if self.__sdram_partition is None:
            spec.write_array([0, 0, 0])
        else:
            size = self.__sdram_partition.get_sdram_size_of_region_for(self)
            proj = self._pop_vertex.outgoing_projections[0]
            # pylint: disable=protected-access
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
            connections = self.__conn(synapse_info).create_synaptic_block(
                (), self.vertex_slice, synapse_type, synapse_info)
            weight_scales = (
                next(iter(cast(AbstractEdgePartition,
                               self.__sdram_partition).edges))
                .post_vertex.weight_scales)
            weights = connections["weight"] * weight_scales[synapse_type]
            weights = numpy.rint(numpy.abs(weights)).astype(uint16)
            if len(weights) % 2 != 0:
                padding = numpy.array([0], dtype=uint16)
                weights = numpy.concatenate((weights, padding))
            spec.write_array(weights.view(uint32))

        # End-of-Spec:
        spec.end_specification()

    def _write_poisson_rates(self, spec: DataSpecificationBase):
        """
        Generate Rate data for Poisson spike sources.

        :param ~data_specification.DataSpecification spec:
            the data specification writer
        """
        spec.comment(
            f"\nWriting Rates for {self.vertex_slice.n_atoms} "
            "poisson sources:\n")

        n_atoms = self.vertex_slice.n_atoms
        n_rates = n_atoms * self._pop_vertex.max_n_rates
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.RATES_REGION,
            size=get_rates_bytes(n_atoms, n_rates), label='PoissonRates')

        # List starts with n_items, so start with 0.  Use arrays to allow
        # numpy concatenation to work.
        data_items: List[Union[Sequence[int], numpy.ndarray]] = list()
        data_items.append([int(self.__rate_changed)])
        data_items.append([0])
        n_items = 0
        data = self._pop_vertex.data
        ids = self.vertex_slice.get_raster_ids()
        for (start, stop, item) in data.iter_ranges_by_ids(ids):
            count = stop - start
            items = numpy.dstack(
                (_u3232_to_uint64(item['rates']),
                 _u3232_to_uint64(item['starts']),
                 _u3232_to_uint64(item['durations']))
                )[0]
            data_items.extend([[count], [len(items)], [0],
                               numpy.ravel(items).view(uint32)])
            n_items += 1
        data_items[1] = [n_items]
        data_to_write = numpy.concatenate(data_items)
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.EXPANDER_REGION,
            size=get_expander_rates_bytes(n_atoms, n_rates), label='Expander')
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.EXPANDER_REGION)
        spec.write_array(data_to_write)

        self.__rate_changed = False

    def _write_poisson_parameters(self, spec: DataSpecificationBase):
        """
        Generate Parameter data for Poisson spike sources.

        :param ~data_specification.DataSpecification spec:
            the data specification writer
        """
        spec.comment(
            f"\nWriting parameters for {self.vertex_slice.n_atoms} "
            "Poisson sources:\n")

        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION,
            size=get_params_bytes(self.vertex_slice.n_atoms),
            label="PoissonParams")
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION)

        # Write Key info for this core:
        routing_info = SpynnakerDataView.get_routing_infos()
        key = routing_info.get_first_key_from_pre_vertex(
            self, constants.SPIKE_PARTITION_ID)
        keys: Union[Sequence[int], numpy.ndarray]
        if key is None:
            spec.write_value(0)
            keys = [0] * self.vertex_slice.n_atoms
        else:
            spec.write_value(1)
            keys = get_field_based_keys(
                key, self.vertex_slice, self._pop_vertex.n_colour_bits)

        # Write the incoming mask if there is one
        incoming_mask = 0
        if self._pop_vertex.incoming_control_edge is not None:
            routing_info = SpynnakerDataView.get_routing_infos()
            r_info = routing_info.get_routing_info_from_pre_vertex(
                self._pop_vertex.incoming_control_edge.pre_vertex,
                LIVE_POISSON_CONTROL_PARTITION_ID)
            if r_info:
                incoming_mask = ~r_info.mask & 0xFFFFFFFF
        spec.write_value(incoming_mask)

        # Write the number of seconds per timestep (unsigned long fract)
        spec.write_value(
            data=SpynnakerDataView.get_simulation_time_step_s(),
            data_type=DataType.U032)

        # Write the number of timesteps per ms (accum)
        spec.write_value(
            data=SpynnakerDataView.get_simulation_time_step_per_ms(),
            data_type=DataType.U1616)

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

        # Write the number of colour bits
        spec.write_value(data=self._pop_vertex.n_colour_bits)

        # Write the random seed (4 words), generated randomly!
        spec.write_array(self._pop_vertex.kiss_seed(self.vertex_slice))

        spec.write_array(keys)

    def set_rate_changed(self) -> None:
        self.__rate_changed = True

    def __poisson_rate_region_address(self, placement: Placement) -> int:
        return helpful_functions.locate_memory_region_for_placement(
            placement, self.POISSON_SPIKE_SOURCE_REGIONS.RATES_REGION)

    def read_parameters_from_machine(self, placement: Placement):
        # It is only worth updating the rates when there is a control edge
        # that can change them
        if self._pop_vertex.incoming_control_edge is not None:
            # locate SDRAM address where the rates are stored
            poisson_rate_region_sdram_address = (
                self.__poisson_rate_region_address(placement))

            # get size of poisson params
            n_atoms = self.vertex_slice.n_atoms
            n_rates = n_atoms * self._pop_vertex.max_n_rates
            size_of_region = get_rates_bytes(n_atoms, n_rates)

            # get data from the machine
            byte_array = SpynnakerDataView.read_memory(
                placement.x, placement.y,
                poisson_rate_region_sdram_address, size_of_region)

            # For each atom, read the number of rates and the rate parameters
            offset = 0
            for i in range(self.vertex_slice.lo_atom,
                           self.vertex_slice.hi_atom + 1):
                n_rates, = _ONE_WORD.unpack_from(byte_array, offset)
                # Skip the count and index
                offset += PARAMS_WORDS_PER_NEURON * BYTES_PER_WORD
                rates: List[float] = list()
                for _ in range(n_rates):
                    rate_int = _ONE_WORD.unpack_from(byte_array, offset)[0]
                    rates.append(rate_int / DataType.S1615.scale)
                    # Skip the start and duration as they can't change
                    offset += PARAMS_WORDS_PER_RATE * BYTES_PER_WORD
                self._pop_vertex.rates.set_value_by_id(i, numpy.array(rates))

    @overrides(SendsSynapticInputsOverSDRAM.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge: SDRAMMachineEdge):
        if isinstance(sdram_machine_edge.post_vertex,
                      ReceivesSynapticInputsOverSDRAM):
            return sdram_machine_edge.post_vertex.n_bytes_for_transfer
        raise SynapticConfigurationException(
            f"Unknown post vertex type in edge {sdram_machine_edge}")

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id: str) -> int:
        return self.vertex_slice.n_atoms << self._pop_vertex.n_colour_bits
