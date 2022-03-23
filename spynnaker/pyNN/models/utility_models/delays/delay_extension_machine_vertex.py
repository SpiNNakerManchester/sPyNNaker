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

from pacman.executor.injection_decorator import inject_items
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, SIMULATION_N_BYTES)
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl, ProvenanceWriter)
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary, AbstractGeneratesDataSpecification)
from spinn_front_end_common.utilities.utility_objs import ExecutableType

#  1. has_key 2. key 3. incoming_key 4. incoming_mask 5. n_atoms
#  6. n_delay_stages, 7. the number of delay supported by each delay stage
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID

_EXPANDER_BASE_PARAMS_SIZE = 3 * BYTES_PER_WORD

DELAY_EXPANDER_APLX = "delay_expander.aplx"


class DelayExtensionMachineVertex(
        MachineVertex, ProvidesProvenanceDataFromMachineImpl,
        AbstractHasAssociatedBinary, AbstractGeneratesDataSpecification):

    __slots__ = [
        "__resources",
        "__slice_index",
        "__drop_late_spikes"]

    class _DELAY_EXTENSION_REGIONS(Enum):
        SYSTEM = 0
        DELAY_PARAMS = 1
        PROVENANCE_REGION = 2
        EXPANDER_REGION = 3
        TDMA_REGION = 4

    class EXTRA_PROVENANCE_DATA_ENTRIES(Enum):
        N_PACKETS_RECEIVED = 0
        N_PACKETS_PROCESSED = 1
        N_PACKETS_ADDED = 2
        N_PACKETS_SENT = 3
        N_BUFFER_OVERFLOWS = 4
        N_DELAYS = 5
        N_TIMES_TDMA_FELL_BEHIND = 6
        N_PACKETS_LOST_DUE_TO_COUNT_SATURATION = 7
        N_PACKETS_WITH_INVALID_NEURON_IDS = 8
        N_PACKETS_DROPPED_DUE_TO_INVALID_KEY = 9
        N_LATE_SPIKES = 10
        MAX_BACKGROUND_QUEUED = 11
        N_BACKGROUND_OVERLOADS = 12

    N_EXTRA_PROVENANCE_DATA_ENTRIES = len(EXTRA_PROVENANCE_DATA_ENTRIES)

    COUNT_SATURATION_NAME = "saturation_count"
    INVALID_NEURON_ID_COUNT_NAME = "invalid_neuron_count"
    INVALID_KEY_COUNT_NAME = "invalid_key_count"
    N_PACKETS_RECEIVED_NAME = "Number_of_packets_received"
    N_PACKETS_PROCESSED_NAME = "Number_of_packets_processed"
    MISMATCH_ADDED_FROM_PROCESSED_NAME = (
        "Number_of_packets_added_to_delay_slot")
    N_PACKETS_SENT_NAME = "Number_of_packets_sent"
    INPUT_BUFFER_LOST_NAME = "Times_the_input_buffer_lost_packets"
    N_LATE_SPIKES_NAME = "Number_of_late_spikes"
    DELAYED_FOR_TRAFFIC_NAME = "Number_of_times_delayed_to_spread_traffic"
    BACKGROUND_OVERLOADS_NAME = "Times_the_background_queue_overloaded"
    BACKGROUND_MAX_QUEUED_NAME = "Max_backgrounds_queued"

    def __init__(self, resources_required, label, constraints=None,
                 app_vertex=None, vertex_slice=None, slice_index=None):
        """
        :param ~pacman.model.resources.ResourceContainer resources_required:
            The resources required by the vertex
        :param str label: The optional name of the vertex
        :param iterable(~pacman.model.constraints.AbstractConstraint) \
                constraints:
            The optional initial constraints of the vertex
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            The application vertex that caused this machine vertex to be
            created. If None, there is no such application vertex.
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the application vertex that this machine vertex
            implements.
        """
        super().__init__(
            label, constraints=constraints, app_vertex=app_vertex,
            vertex_slice=vertex_slice)
        self.__slice_index = slice_index
        self.__resources = resources_required

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self):
        return self._DELAY_EXTENSION_REGIONS.PROVENANCE_REGION.value

    @property
    @overrides(
        ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self):
        return self.N_EXTRA_PROVENANCE_DATA_ENTRIES

    @property
    @overrides(MachineVertex.resources_required)
    def resources_required(self):
        return self.__resources

    @overrides(ProvidesProvenanceDataFromMachineImpl.
               parse_extra_provenance_items)
    def parse_extra_provenance_items(self, label, x, y, p, provenance_data):
        (n_received, n_processed, n_added, n_sent, n_overflows, n_delays,
         n_tdma_behind, n_sat, n_bad_neuron, n_bad_keys, n_late_spikes,
         max_bg, n_bg_overloads) = provenance_data

        self._app_vertex.get_tdma_provenance_item(
            x, y, p, label, n_tdma_behind)
        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, self.COUNT_SATURATION_NAME, n_sat)
            if n_sat != 0:
                db.insert_report(
                    f"The delay extension {label} has dropped {n_sat} packets "
                    f"because during certain time steps a neuron was asked to "
                    f"spike more than 256 times. This causes a saturation on "
                    f"the count tracker which is a uint8. "
                    f"Reduce the packet rates, or modify the delay extension "
                    f"to have larger counters.")

            db.insert_core(
                x, y, p, self.INVALID_NEURON_ID_COUNT_NAME,
                n_bad_neuron)
            if n_bad_neuron != 0:
                db.insert_report(
                    f"The delay extension {label} has dropped {n_bad_neuron} "
                    f"packets because their neuron id was not valid. "
                    f"This is likely a routing issue. "
                    f"Please fix and try again")

            db.insert_core(
                x, y, p, self.INVALID_KEY_COUNT_NAME, n_bad_keys)
            if n_bad_keys != 0:
                db.insert_report(
                    f"The delay extension {label} has dropped {n_bad_keys} "
                    f"packets due to the packet key being invalid. "
                    f"This is likely a routing issue. "
                    f"Please fix and try again")

            db.insert_core(x, y, p, self.N_PACKETS_RECEIVED_NAME, n_received)

            db.insert_core(x, y, p, self.N_PACKETS_PROCESSED_NAME,
                           n_processed)
            if n_received != n_processed:
                db.insert_report(
                    f"The delay extension {label} only processed "
                    f"{n_processed} of {n_received} received packets.  "
                    f"This could indicate a fault.")

            db.insert_core(
                x, y, p, self.MISMATCH_ADDED_FROM_PROCESSED_NAME, n_added)
            if n_added != n_processed:
                db.insert_report(
                    f"The delay extension {label} only added {n_added} of "
                    f"{n_processed} processed packets.  This could indicate "
                    f"a routing or filtering fault")

            db.insert_core(x, y, p, self.N_PACKETS_SENT_NAME, n_sent)

            db.insert_core(
                x, y, p, self.INPUT_BUFFER_LOST_NAME, n_overflows)
            if n_overflows > 0:
                db.insert_report(
                    f"The input buffer for {label} lost packets on "
                    f"{n_overflows} occasions. This is often a sign that the "
                    f"system is running too quickly for the number of "
                    f"neurons per core.  "
                    f"Please increase the timer_tic or time_scale_factor "
                    f"or decrease the number of neurons per core.")

            db.insert_core(x, y, p, self.DELAYED_FOR_TRAFFIC_NAME, n_delays)

            db.insert_core(x, y, p, self.N_LATE_SPIKES_NAME, n_late_spikes)
            if n_late_spikes == 0:
                pass
            elif self._app_vertex.drop_late_spikes:
                db.insert_report(
                    f"On {label}, {n_late_spikes} packets were dropped from "
                    f"the input buffer, because they arrived too late to be "
                    f"processed in a given time step. "
                    "Try increasing the time_scale_factor located within the "
                    ".spynnaker.cfg file or in the pynn.setup() method.")
            else:
                db.insert_report(
                    f"On {label}, {n_late_spikes} packets arrived too late to "
                    f"be processed in a given time step. Try increasing the "
                    "time_scale_factor located within the .spynnaker.cfg file "
                    "or in the pynn.setup() method.")

            db.insert_core(
                x, y, p, self.BACKGROUND_MAX_QUEUED_NAME, max_bg)
            if max_bg > 1:
                db.insert_report(
                    f"On {label}, a maximum of {max_bg} background tasks "
                    f"were queued. Try increasing the time_scale_factor "
                    f"located within the .spynnaker.cfg file or in the "
                    f"pynn.setup() method.")

            db.insert_core(
                x, y, p, self.BACKGROUND_OVERLOADS_NAME, n_bg_overloads)
            if n_bg_overloads > 0:
                db.insert_report(
                    f"On {label}, the background queue overloaded "
                    f"{n_bg_overloads} times. "
                    f"Try increasing the time_scale_factor located within the "
                    ".spynnaker.cfg file or in the pynn.setup() method.")

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, _partition):
        return self._vertex_slice.n_atoms * self.app_vertex.n_delay_stages

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "delay_extension.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    @inject_items({
        "machine_graph": "MachineGraph",
        "routing_infos": "RoutingInfos"})
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_graph", "routing_infos"})
    def generate_data_specification(
            self, spec, placement, machine_graph, routing_infos):
        """
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        :param ~pacman.model.routing_info.RoutingInfo routing_infos:
        """
        # pylint: disable=arguments-differ

        vertex = placement.vertex

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        delay_params_sz = self._app_vertex.delay_params_size(
            self._vertex_slice)

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.SYSTEM.value,
            size=SIMULATION_N_BYTES, label='setup')

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value,
            size=delay_params_sz, label='delay_params')

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.TDMA_REGION.value,
            size=self._app_vertex.tdma_sdram_size_in_bytes, label="tdma data")

        # reserve region for provenance
        self.reserve_provenance_data_region(spec)

        self._write_setup_info(spec, vertex.get_binary_file_name())

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = routing_infos.get_first_key_from_pre_vertex(
            vertex, SPIKE_PARTITION_ID)

        incoming_key = 0
        incoming_mask = 0
        incoming_edges = machine_graph.get_edges_ending_at_vertex(
            vertex)

        for incoming_edge in incoming_edges:
            incoming_slice = incoming_edge.pre_vertex.vertex_slice
            if (incoming_slice.lo_atom == self._vertex_slice.lo_atom and
                    incoming_slice.hi_atom == self._vertex_slice.hi_atom):
                r_info = routing_infos.get_routing_info_for_edge(incoming_edge)
                incoming_key = r_info.first_key
                incoming_mask = r_info.first_mask

        self.write_delay_parameters(
            spec, self._vertex_slice, key, incoming_key, incoming_mask)

        generator_data = self._app_vertex.delay_generator_data(
            self._vertex_slice)
        if generator_data is not None:
            expander_size = sum(data.size for data in generator_data)
            expander_size += _EXPANDER_BASE_PARAMS_SIZE
            spec.reserve_memory_region(
                region=self._DELAY_EXTENSION_REGIONS.EXPANDER_REGION.value,
                size=expander_size, label='delay_expander')
            spec.switch_write_focus(
                self._DELAY_EXTENSION_REGIONS.EXPANDER_REGION.value)
            spec.write_value(len(generator_data))
            spec.write_value(self._vertex_slice.lo_atom)
            spec.write_value(self._vertex_slice.n_atoms)
            for data in generator_data:
                spec.write_array(data.gen_data)

        # add tdma data
        spec.switch_write_focus(
            self._DELAY_EXTENSION_REGIONS.TDMA_REGION.value)
        spec.write_array(
            self._app_vertex.generate_tdma_data_specification_data(
                self.__slice_index))

        # End-of-Spec:
        spec.end_specification()

    def _write_setup_info(self, spec, binary_name):
        """
        :param ~data_specification.DataSpecificationGenerator spec:
        :param str binary_name: the binary name
        """
        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(self._DELAY_EXTENSION_REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            binary_name))

    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask):
        """ Generate Delay Parameter data

        :param ~data_specification.DataSpecificationGenerator spec:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int key:
        :param int incoming_key:
        :param int incoming_mask:
        """
        # pylint: disable=too-many-arguments

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(
            self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value)

        # Write header info to the memory region:
        # Write Key info for this core and the incoming key and mask:
        if key is None:
            spec.write_value(0)
            spec.write_value(0)
        else:
            spec.write_value(1)
            spec.write_value(data=key)
        spec.write_value(data=incoming_key)
        spec.write_value(data=incoming_mask)

        # Write the number of neurons in the block:
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=self._app_vertex.n_delay_stages)

        # write the delay per delay stage
        spec.write_value(data=self._app_vertex.delay_per_stage)

        # write whether to throw away spikes
        spec.write_value(data=int(self._app_vertex.drop_late_spikes))

        # Write the actual delay blocks (create a new one if it doesn't exist)
        spec.write_array(array_values=self._app_vertex.delay_blocks_for(
            self._vertex_slice).delay_block)

    def gen_on_machine(self):
        """ Determine if the given slice needs to be generated on the machine

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: bool
        """
        return self.app_vertex.gen_on_machine(self.vertex_slice)
