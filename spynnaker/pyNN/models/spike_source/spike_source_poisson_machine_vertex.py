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
    SIMULATION_N_BYTES, BYTES_PER_WORD, BYTES_PER_SHORT)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineVertex
from pacman.utilities.utility_calls import get_field_based_keys
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary,
    AbstractRewritesDataSpecification, AbstractGeneratesDataSpecification)
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.interface.profiling import (
    AbstractHasProfileData, profile_utils)
from spinn_front_end_common.interface.profiling.profile_utils import (
    get_profiling_data)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_models import AbstractMaxSpikes
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models import (
    SendsSynapticInputsOverSDRAM, ReceivesSynapticInputsOverSDRAM)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.utilities.constants import (
    LIVE_POISSON_CONTROL_PARTITION_ID)


def _flatten(alist):
    for item in alist:
        if hasattr(item, "__iter__"):
            yield from _flatten(item)
        else:
            yield item


def get_n_rates(vertex_slice, rate_data):
    """ How many rates there are to be stored in total
    """
    return sum(len(rate_data[i]) for i in range(
        vertex_slice.lo_atom, vertex_slice.hi_atom + 1))


def get_params_bytes(n_atoms):
    """ Gets the size of the Poisson parameters in bytes

    :param int n_atoms: How many atoms to account for
    :rtype: int
    """
    return (PARAMS_BASE_WORDS + n_atoms) * BYTES_PER_WORD


def get_rates_bytes(n_atoms, n_rates):
    """ Gets the size of the Poisson rates in bytes

    :param int n_atoms: How many atoms to account for
    :param int n_rates: How many rates to account for
    :rtype: int
    """
    return ((n_atoms * PARAMS_WORDS_PER_NEURON) +
            (n_rates * PARAMS_WORDS_PER_RATE)) * BYTES_PER_WORD


def get_expander_rates_bytes(n_atoms, n_rates):
    """ Gets the size of the Poisson rates in bytes

    :param int n_atoms: How many atoms to account for
    :param int n_rates: How many rates to account for
    :rtype: int
    """
    return ((n_atoms * PARAMS_WORDS_PER_NEURON) +
            (n_rates * PARAMS_WORDS_PER_RATE) + 1) * BYTES_PER_WORD


def get_sdram_edge_params_bytes(vertex_slice):
    """ Gets the size of the Poisson SDRAM region in bytes
    :param ~pacman.model.graphs.common.Slice vertex_slice:
    :rtype: int
    """
    return SDRAM_EDGE_PARAMS_BASE_BYTES + (
        vertex_slice.n_atoms * SDRAM_EDGE_PARAMS_BYTES_PER_WEIGHT)


def _u3232_to_uint64(array):
    """ Convert data to be written in U3232 to uint32 array
    """
    return numpy.round(array * float(DataType.U3232.scale)).astype(
        DataType.U3232.numpy_typename)


# 1. uint32_t has_key;
# 2. uint32_t set_rate_neuron_id_mask;
# 3. UFRACT seconds_per_tick; 4. REAL ticks_per_second;
# 5. REAL slow_rate_per_tick_cutoff; 6. REAL fast_rate_per_tick_cutoff;
# 7. unt32_t first_source_id; 8. uint32_t n_spike_sources;
# 9. uint32_t max_spikes_per_timestep;
# 10,11,12,13 mars_kiss64_seed_t (uint[4]) spike_source_seed;
# 14. Rate changed flag
PARAMS_BASE_WORDS = 14

# uint32_t n_rates; uint32_t index
PARAMS_WORDS_PER_NEURON = 2

# unsigned long accum rate, start, duration
PARAMS_WORDS_PER_RATE = 6

# uint32_t count; one per neuron in worst case (= every neuron different)
EXPANDER_WORDS_PER_NEURON = PARAMS_WORDS_PER_NEURON + 1

# uint32_t n_items
EXPANDER_HEADER_WORDS = 1

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

    __slots__ = [
        "__buffered_sdram_per_timestep",
        "__is_recording",
        "__minimum_buffer_sdram",
        "__sdram",
        "__sdram_partition",
        "__rate_changed"]

    class POISSON_SPIKE_SOURCE_REGIONS(Enum):
        SYSTEM_REGION = 0
        POISSON_PARAMS_REGION = 1
        RATES_REGION = 2
        SPIKE_HISTORY_REGION = 3
        PROVENANCE_REGION = 4
        PROFILER_REGION = 5
        SDRAM_EDGE_PARAMS = 6
        EXPANDER_REGION = 7

    PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "PROB_FUNC"}

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

    # Seed offset in parameters and size on bytes
    SEED_SIZE_BYTES = 4 * BYTES_PER_WORD
    SEED_OFFSET_BYTES = (PARAMS_BASE_WORDS * 4) - SEED_SIZE_BYTES

    def __init__(
            self, sdram, is_recording,
            label=None, app_vertex=None, vertex_slice=None):
        # pylint: disable=too-many-arguments
        super().__init__(
            label, app_vertex=app_vertex, vertex_slice=vertex_slice)
        self.__is_recording = is_recording
        self.__sdram = sdram
        self.__sdram_partition = None
        self.__rate_changed = True

    def set_sdram_partition(self, sdram_partition):
        self.__sdram_partition = sdram_partition

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self):
        return self.__sdram

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
    def get_recording_region_base_address(self, placement):
        return locate_memory_region_for_placement(
            placement,
            self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value)

    @overrides(AbstractHasProfileData.get_profile_data)
    def get_profile_data(self, placement):
        return get_profiling_data(
            self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION.value,
            self.PROFILE_TAG_LABELS, placement)

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

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self):
        # pylint: disable=arguments-differ
        if self.__rate_changed:
            return True
        return SpynnakerDataView.get_first_machine_time_step() == 0

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value):
        self.__rate_changed = new_value

    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(self, spec, placement):
        # pylint: disable=too-many-arguments, arguments-differ

        # write rates
        self._write_poisson_rates(spec)

        # end spec
        spec.end_specification()

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(self, spec, placement):
        """
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
        :param int data_n_time_steps:
        :param int first_machine_time_step:
        """
        # pylint: disable=too-many-arguments, arguments-differ

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        # write setup data
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value,
            size=SIMULATION_N_BYTES,
            label='setup')
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SYSTEM_REGION.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name()))

        # write recording data
        spec.reserve_memory_region(
            region=(
                self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value),
            size=recording_utilities.get_recording_header_size(1),
            label="Recording")
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SPIKE_HISTORY_REGION.value)
        sdram = self._app_vertex.get_recording_sdram_usage(self.vertex_slice)
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
            spec, self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION.value,
            self._app_vertex.n_profile_samples)
        profile_utils.write_profile_region_data(
            spec, self.POISSON_SPIKE_SOURCE_REGIONS.PROFILER_REGION.value,
            self._app_vertex.n_profile_samples)

        # write SDRAM edge parameters
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.SDRAM_EDGE_PARAMS.value,
            label="sdram edge params",
            size=get_sdram_edge_params_bytes(self.vertex_slice))
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.SDRAM_EDGE_PARAMS.value)
        if self.__sdram_partition is None:
            spec.write_array([0, 0, 0])
        else:
            size = self.__sdram_partition.get_sdram_size_of_region_for(self)
            proj = self._app_vertex.outgoing_projections[0]
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
            connections = synapse_info.connector.create_synaptic_block(
                None, self.vertex_slice, synapse_type, synapse_info)
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

    def _write_poisson_rates(self, spec):
        """ Generate Rate data for Poisson spike sources

        :param ~data_specification.DataSpecification spec:
            the data specification writer
        """
        spec.comment("\nWriting Rates for {} poisson sources:\n"
                     .format(self.vertex_slice.n_atoms))

        n_atoms = self.vertex_slice.n_atoms
        n_rates = n_atoms * self._app_vertex.max_n_rates
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.RATES_REGION.value,
            size=get_rates_bytes(n_atoms, n_rates), label='PoissonRates')

        # List starts with n_items, so start with 0.  Use arrays to allow
        # numpy concatenation to work.
        data_items = list()
        data_items.append([int(self.__rate_changed)])
        data_items.append([0])
        n_items = 0
        data = self._app_vertex.data
        ids = self.vertex_slice.get_raster_ids(self.app_vertex.atoms_shape)
        for (start, stop, item) in data.iter_ranges_by_ids(ids):
            count = stop - start
            items = numpy.dstack(
                (_u3232_to_uint64(item['rates']),
                 _u3232_to_uint64(item['starts']),
                 _u3232_to_uint64(item['durations']))
                )[0]
            data_items.extend([[count], [len(items)], [0],
                               numpy.ravel(items).view("uint32")])
            n_items += 1
        data_items[1] = [n_items]
        data_to_write = numpy.concatenate(data_items)
        spec.reserve_memory_region(
            region=self.POISSON_SPIKE_SOURCE_REGIONS.EXPANDER_REGION.value,
            size=len(data_to_write) * BYTES_PER_WORD, label='Expander')
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.EXPANDER_REGION.value)
        spec.write_array(data_to_write)

        self.__rate_changed = False

    def _write_poisson_parameters(self, spec):
        """ Generate Parameter data for Poisson spike sources

        :param ~data_specification.DataSpecification spec:
            the data specification writer
        """
        # pylint: disable=too-many-arguments
        spec.comment("\nWriting Parameters for {} poisson sources:\n"
                     .format(self.vertex_slice.n_atoms))

        spec.reserve_memory_region(
            region=(
                self.POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value),
            size=get_params_bytes(self.vertex_slice.n_atoms),
            label="PoissonParams")
        spec.switch_write_focus(
            self.POISSON_SPIKE_SOURCE_REGIONS.POISSON_PARAMS_REGION.value)

        # Write Key info for this core:
        routing_info = SpynnakerDataView.get_routing_infos()
        key = routing_info.get_first_key_from_pre_vertex(
            self, constants.SPIKE_PARTITION_ID)
        if key is None:
            spec.write_value(0)
            keys = [0] * self.vertex_slice.n_atoms
        else:
            spec.write_value(1)
            keys = get_field_based_keys(key, self.vertex_slice)

        # Write the incoming mask if there is one
        incoming_mask = 0
        if self._app_vertex.incoming_control_edge is not None:
            routing_info = SpynnakerDataView.get_routing_infos()
            r_info = routing_info.get_routing_info_from_pre_vertex(
                self._app_vertex.incoming_control_edge.pre_vertex,
                LIVE_POISSON_CONTROL_PARTITION_ID)
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

        # Write the random seed (4 words), generated randomly!
        spec.write_array(self._app_vertex.kiss_seed(self.vertex_slice))

        spec.write_array(keys)

    def set_rate_changed(self):
        self.__rate_changed = True

    def __poisson_rate_region_address(self, placement):
        return helpful_functions.locate_memory_region_for_placement(
            placement,
            self.POISSON_SPIKE_SOURCE_REGIONS.RATES_REGION.value)

    def read_parameters_from_machine(self, placement):

        # It is only worth updating the rates when there is a control edge
        # that can change them
        if self._app_vertex.incoming_control_edge is not None:

            # locate SDRAM address where the rates are stored
            poisson_rate_region_sdram_address = (
                self.__poisson_rate_region_address(placement))

            # get size of poisson params
            n_atoms = self._vertex_slice.n_atoms
            n_rates = n_atoms * self._app_vertex.max_n_rates
            size_of_region = get_rates_bytes(n_atoms, n_rates)

            # get data from the machine
            byte_array = SpynnakerDataView.read_memory(
                placement.x, placement.y,
                poisson_rate_region_sdram_address, size_of_region)

            # For each atom, read the number of rates and the rate parameters
            offset = 0
            for i in range(self._vertex_slice.lo_atom,
                           self._vertex_slice.hi_atom + 1):
                n_rates, = _ONE_WORD.unpack_from(byte_array, offset)
                # Skip the count and index
                offset += PARAMS_WORDS_PER_NEURON * BYTES_PER_WORD
                rates = list()
                for _ in range(n_rates):
                    rate_int = _ONE_WORD.unpack_from(byte_array, offset)[0]
                    rates.append(rate_int / DataType.S1615.scale)
                    # Skip the start and duration as they can't change
                    offset += PARAMS_WORDS_PER_RATE * BYTES_PER_WORD
                self._app_vertex.rates.set_value_by_id(i, rates)

    @overrides(SendsSynapticInputsOverSDRAM.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge):
        if isinstance(sdram_machine_edge.post_vertex,
                      ReceivesSynapticInputsOverSDRAM):
            return sdram_machine_edge.post_vertex.n_bytes_for_transfer
        raise SynapticConfigurationException(
            "Unknown post vertex type in edge {}".format(sdram_machine_edge))

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id):
        return self._vertex_slice.n_atoms * 16
