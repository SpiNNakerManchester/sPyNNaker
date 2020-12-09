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
from enum import Enum
from collections import namedtuple
import ctypes

from pacman.executor.injection_decorator import inject_items
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spinn_front_end_common.interface.buffer_management.buffer_models import (
    AbstractReceiveBuffersToHost)
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary, AbstractRecordable,
    AbstractSupportsBitFieldGeneration,
    AbstractSupportsBitFieldRoutingCompression,
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification)
from spinn_front_end_common.interface.profiling import (
    AbstractHasProfileData, profile_utils)
from spinn_front_end_common.interface.profiling.profile_utils import (
    get_profiling_data)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.utilities.constants import SIMULATION_N_BYTES
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.utilities import constants, bit_field_utilities
from spynnaker.pyNN.models.abstract_models import (
    AbstractSynapseExpandable, AbstractReadParametersBeforeSet)
from .synaptic_matrices import SynapticMatrices


class NeuronProvenance(ctypes.LittleEndianStructure):
    """ Provenance items from neuron processing
    """
    _fields_ = [
        # The timer tick at the end of simulation
        ("current_timer_tick", ctypes.c_uint32),
        # The number of misses of TDMA time slots
        ("n_tdma_misses", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class SynapseProvenance(ctypes.LittleEndianStructure):
    """ Provenance items from synapse processing
    """
    _fields_ = [
        # A count of presynaptic events.
        ("n_pre_synaptic_events", ctypes.c_uint32),
        # A count of synaptic saturations.
        ("n_saturations", ctypes.c_uint32),
        # A count of the times that the synaptic input circular buffers
        # overflowed
        ("n_buffer_overflows", ctypes.c_uint32),
        # The number of STDP weight saturations.
        ("n_plastic_saturations", ctypes.c_uint32),
        ("n_ghost_searches", ctypes.c_uint32),
        ("n_failed_bitfield_reads", ctypes.c_uint32),
        ("n_dmas_complete", ctypes.c_uint32),
        ("n_spikes_processed", ctypes.c_uint32),
        ("n_invalid_pop_table_hits", ctypes.c_uint32),
        ("n_filtered_by_bitfield", ctypes.c_uint32),
        # The number of rewirings performed.
        ("n_rewires", ctypes.c_uint32),
        ("n_late_packets", ctypes.c_uint32),
        ("max_size_input_buffer", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


NeuronRegions = namedtuple(
    "NeuronRegions",
    ["neuron_params", "neuron_recording"])

SynapseRegions = namedtuple(
    "SynapseRegions",
    ["synapse_params", "direct_matrix", "pop_table", "synaptic_matrix",
     "synapse_dynamics", "structural_dynamics", "bitfield_builder",
     "bitfield_key_map", "bitfield_filter", "connection_builder"])


class PopulationMachineVertex(
        MachineVertex, AbstractReceiveBuffersToHost,
        AbstractHasAssociatedBinary, ProvidesProvenanceDataFromMachineImpl,
        AbstractRecordable, AbstractHasProfileData,
        AbstractSupportsBitFieldGeneration,
        AbstractSupportsBitFieldRoutingCompression,
        AbstractGeneratesDataSpecification, AbstractSynapseExpandable,
        AbstractRewritesDataSpecification, AbstractReadParametersBeforeSet):

    __slots__ = [
        "__binary_file_name",
        "__recorded_region_ids",
        "__resources",
        "__change_requires_neuron_parameters_reload",
        "__synaptic_matrices"]

    class REGIONS(Enum):
        """Regions for populations."""
        SYSTEM = 0
        NEURON_PARAMS = 1
        SYNAPSE_PARAMS = 2
        POPULATION_TABLE = 3
        SYNAPTIC_MATRIX = 4
        SYNAPSE_DYNAMICS = 5
        STRUCTURAL_DYNAMICS = 6
        NEURON_RECORDING = 7
        PROVENANCE_DATA = 8
        PROFILING = 9
        CONNECTOR_BUILDER = 10
        DIRECT_MATRIX = 11
        BIT_FIELD_FILTER = 12
        BIT_FIELD_BUILDER = 13
        BIT_FIELD_KEY_MAP = 14

    NEURON_REGIONS = NeuronRegions(
        neuron_params=REGIONS.NEURON_PARAMS.value,
        neuron_recording=REGIONS.NEURON_RECORDING.value
    )

    SYNAPSE_REGIONS = SynapseRegions(
        synapse_params=REGIONS.SYNAPSE_PARAMS.value,
        direct_matrix=REGIONS.DIRECT_MATRIX.value,
        pop_table=REGIONS.POPULATION_TABLE.value,
        synaptic_matrix=REGIONS.SYNAPTIC_MATRIX.value,
        synapse_dynamics=REGIONS.SYNAPSE_DYNAMICS.value,
        structural_dynamics=REGIONS.STRUCTURAL_DYNAMICS.value,
        bitfield_builder=REGIONS.BIT_FIELD_BUILDER.value,
        bitfield_key_map=REGIONS.BIT_FIELD_KEY_MAP.value,
        bitfield_filter=REGIONS.BIT_FIELD_FILTER.value,
        connection_builder=REGIONS.CONNECTOR_BUILDER.value
    )

    SATURATION_COUNT_NAME = "Times_synaptic_weights_have_saturated"
    SATURATION_COUNT_MESSAGE = (
        "The weights from the synapses for {} on {}, {}, {} saturated "
        "{} times. If this causes issues you can increase the "
        "spikes_per_second and / or ring_buffer_sigma "
        "values located within the .spynnaker.cfg file.")

    INPUT_BUFFER_FULL_NAME = "Times_the_input_buffer_lost_packets"
    INPUT_BUFFER_FULL_MESSAGE = (
        "The input buffer for {} on {}, {}, {} lost packets on {} "
        "occasions. This is often a sign that the system is running "
        "too quickly for the number of neurons per core.  Please "
        "increase the timer_tic or time_scale_factor or decrease the "
        "number of neurons per core.")

    TOTAL_PRE_SYNAPTIC_EVENT_NAME = "Total_pre_synaptic_events"
    LAST_TIMER_TICK_NAME = "Last_timer_tic_the_core_ran_to"
    N_RE_WIRES_NAME = "Number_of_rewires"

    SATURATED_PLASTIC_WEIGHTS_NAME = (
        "Times_plastic_synaptic_weights_have_saturated")
    SATURATED_PLASTIC_WEIGHTS_MESSAGE = (
        "The weights from the plastic synapses for {} on {}, {}, {} "
        "saturated {} times. If this causes issue increase the "
        "spikes_per_second and / or ring_buffer_sigma values located "
        "within the .spynnaker.cfg file.")

    _N_LATE_SPIKES_NAME = "Number_of_late_spikes"
    _N_LATE_SPIKES_MESSAGE_DROP = (
        "{} packets from {} on {}, {}, {} were dropped from the input buffer, "
        "because they arrived too late to be processed in a given time step. "
        "Try increasing the time_scale_factor located within the "
        ".spynnaker.cfg file or in the pynn.setup() method.")
    _N_LATE_SPIKES_MESSAGE_NO_DROP = (
        "{} packets from {} on {}, {}, {} arrived too late to be processed in"
        " a given time step. "
        "Try increasing the time_scale_factor located within the "
        ".spynnaker.cfg file or in the pynn.setup() method.")

    _MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME = "Max_filled_size_input_buffer"

    _PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "DMA_READ",
        2: "INCOMING_SPIKE",
        3: "PROCESS_FIXED_SYNAPSES",
        4: "PROCESS_PLASTIC_SYNAPSES"}

    # x words needed for a bitfield covering 256 atoms
    WORDS_TO_COVER_256_ATOMS = 8

    # provenance data items
    BIT_FIELD_FILTERED_PACKETS = \
        "How many packets were filtered by the bitfield filterer."
    INVALID_MASTER_POP_HITS = "Invalid Master Pop hits"
    SPIKES_PROCESSED = "how many spikes were processed"
    DMA_COMPLETE = "DMA's that were completed"
    BIT_FIELDS_NOT_READ = "N bit fields not able to be read into DTCM"
    GHOST_SEARCHES = "Number of failed pop table searches"
    PLASTIC_WEIGHT_SATURATION = "Times_plastic_synaptic_weights_have_saturated"
    LAST_TIMER_TICK = "Last_timer_tic_the_core_ran_to"
    TOTAL_PRE_SYNAPTIC_EVENTS = "Total_pre_synaptic_events"
    LOST_INPUT_BUFFER_PACKETS = "Times_the_input_buffer_lost_packets"

    def __init__(
            self, resources_required, recorded_region_ids, label, constraints,
            app_vertex, vertex_slice, binary_file_name):
        """
        :param ~pacman.model.resources.ResourceContainer resources_required:
        :param iterable(int) recorded_region_ids:
        :param str label:
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        :param str binary_file_name: binary name to be run for this verte
        """
        MachineVertex.__init__(
            self, label, constraints, app_vertex, vertex_slice)
        self.__binary_file_name = binary_file_name
        AbstractRecordable.__init__(self)
        self.__recorded_region_ids = recorded_region_ids
        self.__resources = resources_required
        self.__change_requires_neuron_parameters_reload = False

        self.__synaptic_matrices = SynapticMatrices(
            vertex_slice, app_vertex.neuron_impl.get_n_synapse_types(),
            app_vertex.all_single_syn_size,
            self.SYNAPSE_REGIONS.synaptic_matrix,
            self.SYNAPSE_REGIONS.direct_matrix,
            self.SYNAPSE_REGIONS.pop_table,
            self.SYNAPSE_REGIONS.connection_builder)

    @overrides(AbstractSupportsBitFieldGeneration.bit_field_base_address)
    def bit_field_base_address(self, transceiver, placement):
        return locate_memory_region_for_placement(
            placement=placement, transceiver=transceiver,
            region=self.SYNAPSE_REGIONS.bitfield_filter)

    @overrides(AbstractSupportsBitFieldRoutingCompression.
               key_to_atom_map_region_base_address)
    def key_to_atom_map_region_base_address(self, transceiver, placement):
        return locate_memory_region_for_placement(
            placement=placement, transceiver=transceiver,
            region=self.SYNAPSE_REGIONS.bitfield_key_map)

    @overrides(AbstractSupportsBitFieldGeneration.bit_field_builder_region)
    def bit_field_builder_region(self, transceiver, placement):
        return locate_memory_region_for_placement(
            placement=placement, transceiver=transceiver,
            region=self.SYNAPSE_REGIONS.bitfield_builder)

    @overrides(AbstractSupportsBitFieldRoutingCompression.
               regeneratable_sdram_blocks_and_sizes)
    def regeneratable_sdram_blocks_and_sizes(self, transceiver, placement):
        synaptic_matrix_base_address = locate_memory_region_for_placement(
            placement=placement, transceiver=transceiver,
            region=self.SYNAPSE_REGIONS.synaptic_matrix)
        return [(
            self.__synaptic_matrices.host_generated_block_addr +
            synaptic_matrix_base_address,
            self.__synaptic_matrices.on_chip_generated_matrix_size)]

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self.__resources

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self):
        return self.REGIONS.PROVENANCE_DATA.value

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self):
        return NeuronProvenance.N_ITEMS + SynapseProvenance.N_ITEMS

    @overrides(AbstractRecordable.is_recording)
    def is_recording(self):
        return len(self.__recorded_region_ids) > 0

    @overrides(ProvidesProvenanceDataFromMachineImpl.
               get_provenance_data_from_machine)
    def get_provenance_data_from_machine(self, transceiver, placement):
        provenance_data = self._read_provenance_data(transceiver, placement)
        provenance_items = self._read_basic_provenance_items(
            provenance_data, placement)
        prov_list_from_machine = self._get_remaining_provenance_data_items(
            provenance_data)

        # translate into provenance data items
        self._append_neuron_provenance(
            provenance_items, prov_list_from_machine, 0, placement)
        self._append_synapse_provenance(
            provenance_items, prov_list_from_machine, NeuronProvenance.N_ITEMS,
            placement)

        return provenance_items

    def _append_neuron_provenance(
            self, provenance_items, prov_list_from_machine, offset, placement):
        """ Extract and add neuron provenance to the list of provenance items

        :param
            list(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)\
            provenance_items: The items already read, to append to
        :param list(int) prov_list_from_machine:
            The values read from the machine to be decoded
        :param int offset: Where in the list from the machine to start reading
        :param ~pacman.model.placements.Placement placement:
            Which vertex are we retrieving from, and where was it
        """
        neuron_prov = NeuronProvenance(
            *prov_list_from_machine[offset:NeuronProvenance.N_ITEMS + offset])
        _, x, y, p, names = self._get_placement_details(placement)

        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.LAST_TIMER_TICK_NAME),
            neuron_prov.current_timer_tick))
        provenance_items.append(self._app_vertex.get_tdma_provenance_item(
            names, x, y, p, neuron_prov.n_tdma_misses))

    def _append_synapse_provenance(
            self, provenance_items, prov_list_from_machine, offset, placement):
        """ Extract and add synapse provenance to the list of provenance items

        :param
            list(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)\
            provenance_items: The items already read, to append to
        :param list(int) prov_list_from_machine:
            The values read from the machine to be decoded
        :param int offset: Where in the list from the machine to start reading
        :param ~pacman.model.placements.Placement placement:
            Which vertex are we retrieving from, and where was it
        """
        synapse_prov = SynapseProvenance(
            *prov_list_from_machine[offset:SynapseProvenance.N_ITEMS + offset])
        label, x, y, p, names = self._get_placement_details(placement)

        times_timer_tic_overran = 0
        for item in provenance_items:
            if item.names[-1] == self._TIMER_TICK_OVERRUN:
                times_timer_tic_overran = item.value

        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.SATURATION_COUNT_NAME),
            synapse_prov.n_saturations, report=synapse_prov.n_saturations > 0,
            message=self.SATURATION_COUNT_MESSAGE.format(
                label, x, y, p, synapse_prov.n_saturations)))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.INPUT_BUFFER_FULL_NAME),
            synapse_prov.n_buffer_overflows,
            report=synapse_prov.n_buffer_overflows > 0,
            message=self.INPUT_BUFFER_FULL_MESSAGE.format(
                label, x, y, p, synapse_prov.n_buffer_overflows)))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.TOTAL_PRE_SYNAPTIC_EVENT_NAME),
            synapse_prov.n_pre_synaptic_events))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.SATURATED_PLASTIC_WEIGHTS_NAME),
            synapse_prov.n_plastic_saturations,
            report=synapse_prov.n_plastic_saturations > 0,
            message=self.SATURATED_PLASTIC_WEIGHTS_MESSAGE.format(
                label, x, y, p, synapse_prov.n_plastic_saturations)))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.N_RE_WIRES_NAME),
            synapse_prov.n_rewires))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.GHOST_SEARCHES),
            synapse_prov.n_ghost_searches,
            report=synapse_prov.n_ghost_searches > 0,
            message=(
                "The number of failed population table searches for {} on {},"
                " {}, {} was {}. If this number is large relative to the "
                "predicted incoming spike rate, try increasing source and "
                "target neurons per core".format(
                    label, x, y, p, synapse_prov.n_ghost_searches))))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.BIT_FIELDS_NOT_READ),
            synapse_prov.n_failed_bitfield_reads, report=False,
            message=(
                "The filter for stopping redundant DMA's couldn't be fully "
                "filled in, it failed to read {} entries, which means it "
                "required a max of {} extra bytes of DTCM (assuming cores "
                "have at max 255 neurons. Try reducing neurons per core, or "
                "size of buffers, or neuron params per neuron etc.".format(
                    synapse_prov.n_failed_bitfield_reads,
                    synapse_prov.n_failed_bitfield_reads *
                    self.WORDS_TO_COVER_256_ATOMS))))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.DMA_COMPLETE),
            synapse_prov.n_dmas_complete))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.SPIKES_PROCESSED),
            synapse_prov.n_spikes_processed))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self.INVALID_MASTER_POP_HITS),
            synapse_prov.n_invalid_pop_table_hits,
            report=synapse_prov.n_invalid_pop_table_hits > 0,
            message=(
                "There were {} keys which were received by core {}:{}:{} which"
                " had no master pop entry for it. This is a error, which most "
                "likely strives from bad routing.".format(
                    synapse_prov.n_invalid_pop_table_hits, x, y, p))))
        provenance_items.append((ProvenanceDataItem(
            self._add_name(names, self.BIT_FIELD_FILTERED_PACKETS),
            synapse_prov.n_filtered_by_bitfield,
            report=(synapse_prov.n_filtered_by_bitfield > 0 and (
                        synapse_prov.n_buffer_overflows > 0 or
                        times_timer_tic_overran > 0)),
            message=(
                "There were {} packets received by {}:{}:{} that were "
                "filtered by the Bitfield filterer on the core. These packets "
                "were having to be stored and processed on core, which means "
                "the core may not be running as efficiently as it could. "
                "Please adjust the network or the mapping so that these "
                "packets are filtered in the router to improve "
                "performance.".format(
                    synapse_prov.n_filtered_by_bitfield, x, y, p)))))
        late_message = (
            self._N_LATE_SPIKES_MESSAGE_DROP
            if self._app_vertex.drop_late_spikes
            else self._N_LATE_SPIKES_MESSAGE_NO_DROP)
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self._N_LATE_SPIKES_NAME),
            synapse_prov.n_late_packets,
            report=synapse_prov.n_late_packets > 0,
            message=late_message.format(
                synapse_prov.n_late_packets, label, x, y, p)))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, self._MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME),
            synapse_prov.max_size_input_buffer, report=False))

    @overrides(AbstractReceiveBuffersToHost.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        return self.__recorded_region_ids

    @overrides(AbstractReceiveBuffersToHost.get_recording_region_base_address)
    def get_recording_region_base_address(self, txrx, placement):
        return locate_memory_region_for_placement(
            placement, self.NEURON_REGIONS.neuron_recording, txrx)

    @overrides(AbstractHasProfileData.get_profile_data)
    def get_profile_data(self, transceiver, placement):
        return get_profiling_data(
            self.REGIONS.PROFILING.value,
            self._PROFILE_TAG_LABELS, transceiver, placement)

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return self.__binary_file_name

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "machine_graph": "MemoryMachineGraph",
        "routing_info": "MemoryRoutingInfos",
        "data_n_time_steps": "DataNTimeSteps",
        "n_key_map": "MemoryMachinePartitionNKeysMap"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor",
            "machine_graph", "routing_info",
            "data_n_time_steps", "n_key_map"
        })
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            machine_graph, routing_info, data_n_time_steps,
            n_key_map):
        """
        :param machine_time_step: (injected)
        :param time_scale_factor: (injected)
        :param application_graph: (injected)
        :param machine_graph: (injected)
        :param routing_info: (injected)
        :param data_n_time_steps: (injected)
        :param n_key_map: (injected)
        """
        # pylint: disable=too-many-arguments, arguments-differ

        spec.comment("\n*** Spec for block of {} neurons ***\n".format(
            self._app_vertex.neuron_impl.model_name))

        # Write the setup region
        spec.reserve_memory_region(
            region=self.REGIONS.SYSTEM.value, size=SIMULATION_N_BYTES,
            label='System')
        spec.switch_write_focus(self.REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.__binary_file_name, machine_time_step, time_scale_factor))

        # Reserve memory for provenance
        self.reserve_provenance_data_region(spec)

        # write profile data
        profile_utils.reserve_profile_region(
            spec, self.REGIONS.PROFILING.value,
            self._app_vertex.n_profile_samples)
        profile_utils.write_profile_region_data(
            spec, self.REGIONS.PROFILING.value,
            self._app_vertex.n_profile_samples)

        self._write_neuron_data_spec(
            spec, routing_info, data_n_time_steps, self.NEURON_REGIONS)
        self._write_synapse_data_spec(
            spec, machine_time_step, routing_info, machine_graph, n_key_map,
            self.SYNAPSE_REGIONS)

        # End the writing of this specification:
        spec.end_specification()

    def _write_neuron_data_spec(
            self, spec, routing_info, data_n_time_steps, regions):
        # Write the neuron parameters with the key
        self._write_neuron_parameters(
            spec, regions.neuron_params, routing_info)

        # Write the neuron recording region
        spec.reserve_memory_region(
            region=regions.neuron_recording,
            size=self._app_vertex.neuron_recorder.get_static_sdram_usage(
                self.vertex_slice),
            label="neuron recording")
        self._app_vertex.neuron_recorder.write_neuron_recording_region(
            spec, regions.neuron_recording, self.vertex_slice,
            data_n_time_steps)

    def _write_synapse_data_spec(
            self, spec, machine_time_step, routing_info, machine_graph,
            n_key_map, regions):

        # Write the synapse parameters
        self._write_synapse_parameters(
            spec, regions.synapse_params, machine_time_step)

        # Write the synaptic matrices
        all_syn_block_sz = self._app_vertex.get_synapses_size(
            self.vertex_slice)
        weight_scales = self._app_vertex.get_weight_scales(machine_time_step)
        self.__synaptic_matrices.write_synaptic_data(
            spec, self, all_syn_block_sz, weight_scales, routing_info,
            machine_graph)

        # Write any synapse dynamics
        synapse_dynamics = self._app_vertex.synapse_dynamics
        synapse_dynamics_sz = self._app_vertex.get_synapse_dynamics_size(
            self.vertex_slice)
        if synapse_dynamics_sz > 0:
            spec.reserve_memory_region(
                region=regions.synapse_dynamics, size=synapse_dynamics_sz,
                label='synapseDynamicsParams')
            synapse_dynamics.write_parameters(
                spec, regions.synapse_dynamics, machine_time_step,
                weight_scales)

            if isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural):
                structural_sz = self._app_vertex.get_structural_dynamics_size(
                    self.vertex_slice)
                spec.reserve_memory_region(
                    region=regions.structural_dynamics, size=structural_sz,
                    label='synapseDynamicsStructuralParams')
                synapse_dynamics.write_structural_parameters(
                    spec, regions.structural_dynamics,
                    machine_time_step, weight_scales, machine_graph, self,
                    routing_info, self.__synaptic_matrices)

        # write up the bitfield builder data
        # reserve bit field region
        bit_field_utilities.reserve_bit_field_regions(
            spec, machine_graph, n_key_map, self, regions.bitfield_builder,
            regions.bitfield_filter, regions.bitfield_key_map)
        bit_field_utilities.write_bitfield_init_data(
            spec, self, machine_graph, routing_info,
            n_key_map, regions.bitfield_builder, regions.pop_table,
            regions.synaptic_matrix, regions.direct_matrix,
            regions.bitfield_filter, regions.bitfield_key_map,
            regions.structural_dynamics,
            isinstance(synapse_dynamics, AbstractSynapseDynamicsStructural))

    @inject_items({"routing_info": "MemoryRoutingInfos"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={"routing_info"})
    def regenerate_data_specification(self, spec, placement, routing_info):
        # pylint: disable=too-many-arguments, arguments-differ

        # write the neuron params into the new DSG region
        self._write_neuron_parameters(
            spec, self.NEURON_REGIONS.neuron_params, routing_info)

        # close spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self):
        return self.__change_requires_neuron_parameters_reload

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value):
        self.__change_requires_neuron_parameters_reload = new_value

    @staticmethod
    def neuron_region_sdram_address(placement, transceiver):
        return helpful_functions.locate_memory_region_for_placement(
                placement, PopulationMachineVertex.REGIONS.NEURON_PARAMS.value,
                transceiver)

    def _write_neuron_parameters(self, spec, region_id, routing_info):

        self._app_vertex.update_state_variables()

        # pylint: disable=too-many-arguments
        n_atoms = self.vertex_slice.n_atoms
        spec.comment("\nWriting Neuron Parameters for {} Neurons:\n".format(
            n_atoms))

        # Reserve and switch to the memory region
        params_size = self._app_vertex.get_sdram_usage_for_neuron_params(
            self.vertex_slice)
        spec.reserve_memory_region(
            region=region_id, size=params_size, label='NeuronParams')
        spec.switch_write_focus(region_id)

        # store the tdma data here for this slice.
        data = self._app_vertex.generate_tdma_data_specification_data(
            self._app_vertex.vertex_slices.index(self.vertex_slice))
        spec.write_array(data)

        # Write whether the key is to be used, and then the key, or 0 if it
        # isn't to be used
        key = routing_info.get_first_key_from_pre_vertex(
            self, constants.SPIKE_PARTITION_ID)
        if key is None:
            spec.write_value(data=0)
            spec.write_value(data=0)
        else:
            spec.write_value(data=1)
            spec.write_value(data=key)

        # Write the number of neurons in the block:
        spec.write_value(data=n_atoms)

        # Write the neuron parameters
        neuron_data = self._app_vertex.neuron_impl.get_data(
            self._app_vertex.parameters, self._app_vertex.state_variables,
            self.vertex_slice)
        spec.write_array(neuron_data)

    def _write_synapse_parameters(self, spec, region_id, machine_time_step):
        # Reserve space
        spec.reserve_memory_region(
            region=region_id, size=self._app_vertex.get_synapse_params_size(),
            label='SynapseParams')

        # Get values
        n_neurons = self.vertex_slice.n_atoms
        n_synapse_types = self._app_vertex.neuron_impl.get_n_synapse_types()

        # Write synapse parameters
        spec.switch_write_focus(region_id)
        spec.write_value(n_neurons)
        spec.write_value(n_synapse_types)
        spec.write_value(n_neurons.bit_length())
        spec.write_value(n_synapse_types.bit_length())
        spec.write_value(int(self._app_vertex.drop_late_spikes))
        spec.write_value(self._app_vertex.incoming_spike_buffer_size)
        spec.write_array(self._app_vertex.get_ring_buffer_shifts(
            machine_time_step))

    @overrides(AbstractSynapseExpandable.gen_on_machine)
    def gen_on_machine(self):
        return self.__synaptic_matrices.gen_on_machine

    @overrides(AbstractSynapseExpandable.read_generated_connection_holders)
    def read_generated_connection_holders(self, transceiver, placement):
        self.__synaptic_matrices.read_generated_connection_holders(
            transceiver, placement)

    @overrides(AbstractReadParametersBeforeSet.read_parameters_from_machine)
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):

        # locate SDRAM address to where the neuron parameters are stored
        neuron_region_sdram_address = self.neuron_region_sdram_address(
            placement, transceiver)

        # shift past the extra stuff before neuron parameters that we don't
        # need to read
        neuron_parameters_sdram_address = (
            neuron_region_sdram_address +
            self._app_vertex.tdma_sdram_size_in_bytes +
            self._app_vertex.BYTES_TILL_START_OF_GLOBAL_PARAMETERS)

        # get size of neuron params
        size_of_region = self._app_vertex.get_sdram_usage_for_neuron_params(
            vertex_slice)
        size_of_region -= (
            self._app_vertex.BYTES_TILL_START_OF_GLOBAL_PARAMETERS +
            self._app_vertex.tdma_sdram_size_in_bytes)

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y, neuron_parameters_sdram_address,
            size_of_region)

        # update python neuron parameters with the data
        self._app_vertex.neuron_impl.read_data(
            byte_array, 0, vertex_slice, self._app_vertex.parameters,
            self._app_vertex.state_variables)

    def get_connections_from_machine(
            self, transceiver, placement, app_edge, synapse_info):
        """ Get the connections from the machine for this vertex.

        :param ~spinnman.transceiver.Transceiver transceiver:
            How to read the connection data
        :param ~pacman.model.placement.Placement placements:
            Where the connection data is on the machine
        :param ProjectionApplicationEdge app_edge:
            The edge for which the data is being read
        :param SynapseInformation synapse_info:
            The specific projection within the edge
        """
        return self.__synaptic_matrices.get_connections_from_machine(
            transceiver, placement, app_edge, synapse_info)

    def clear_connection_cache(self):
        """ Flush the cache of connection information; needed for a second run
        """
        self.__synaptic_matrices.clear_connection_cache()
