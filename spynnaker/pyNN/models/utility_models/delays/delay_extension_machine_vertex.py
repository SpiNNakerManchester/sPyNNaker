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
from typing import Sequence, TYPE_CHECKING

from spinnman.model.enums import ExecutableType
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.constants import SIMULATION_N_BYTES
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineVertex
from pacman.model.resources import AbstractSDRAM
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl, ProvenanceWriter)
from spinn_front_end_common.abstract_models import (
    AbstractHasAssociatedBinary, AbstractGeneratesDataSpecification)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from .delay_extension_vertex import DelayExtensionVertex
if TYPE_CHECKING:
    from pacman.model.placements import Placement
    from spinn_front_end_common.interface.ds import DataSpecificationGenerator


class DelayExtensionMachineVertex(
        MachineVertex, ProvidesProvenanceDataFromMachineImpl,
        AbstractHasAssociatedBinary, AbstractGeneratesDataSpecification):
    """
    Vertex that implements a delay extension.
    Not expected to be directly referenced in user code.
    """

    __slots__ = (
        "__sdram",
        "__drop_late_spikes")

    class _DELAY_EXTENSION_REGIONS(IntEnum):
        """
        Region indices.
        """
        SYSTEM = 0
        DELAY_PARAMS = 1
        PROVENANCE_REGION = 2
        TDMA_REGION = 3

    class EXTRA_PROVENANCE_DATA_ENTRIES(IntEnum):
        """
        Indices into raw provenance data about delay extension vertices.
        """
        #: The number of packets received
        N_PACKETS_RECEIVED = 0
        #: The number of packets processed
        N_PACKETS_PROCESSED = 1
        #: The number of packets added to a send queue
        N_PACKETS_ADDED = 2
        #: The number of packets sent
        N_PACKETS_SENT = 3
        #: The number of times a buffer overflowed
        N_BUFFER_OVERFLOWS = 4
        #: The number of delays
        N_DELAYS = 5
        #: The number of packets lost due to saturation
        N_PACKETS_LOST_DUE_TO_COUNT_SATURATION = 6
        #: The number of packets with bad neuron IDs
        N_PACKETS_WITH_INVALID_NEURON_IDS = 7
        #: The number of packets lost due to an invalid key
        N_PACKETS_DROPPED_DUE_TO_INVALID_KEY = 8
        #: The number of packets that arrived too late
        N_LATE_SPIKES = 9
        #: The maximum number of packets queued for background processing
        MAX_BACKGROUND_QUEUED = 10
        #: The number of times the background queue overflowed
        N_BACKGROUND_OVERLOADS = 11

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

    def __init__(self, sdram: AbstractSDRAM, label, vertex_slice,
                 app_vertex=None):
        """
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The SDRAM required by the vertex
        :param str label: The name of the vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the vertex
        :param ~pacman.model.graphs.application.ApplicationVertex app_vertex:
            The application vertex that caused this machine vertex to be
            created. If `None`, there is no such application vertex.
        """
        super().__init__(
            label, app_vertex=app_vertex, vertex_slice=vertex_slice)
        self.__sdram = sdram

    @property
    @overrides(MachineVertex.app_vertex)
    def app_vertex(self) -> DelayExtensionVertex:
        assert isinstance(self._app_vertex, DelayExtensionVertex)
        return self._app_vertex

    @property
    @overrides(ProvidesProvenanceDataFromMachineImpl._provenance_region_id)
    def _provenance_region_id(self) -> int:
        return self._DELAY_EXTENSION_REGIONS.PROVENANCE_REGION

    @property
    @overrides(
        ProvidesProvenanceDataFromMachineImpl._n_additional_data_items)
    def _n_additional_data_items(self) -> int:
        return self.N_EXTRA_PROVENANCE_DATA_ENTRIES

    @property
    @overrides(MachineVertex.sdram_required)
    def sdram_required(self) -> AbstractSDRAM:
        return self.__sdram

    @overrides(ProvidesProvenanceDataFromMachineImpl.
               parse_extra_provenance_items)
    def parse_extra_provenance_items(
            self, label: str, x: int, y: int, p: int,
            provenance_data: Sequence[int]):
        (n_received, n_processed, n_added, n_sent, n_overflows, n_delays,
         n_sat, n_bad_neuron, n_bad_keys, n_late_spikes, max_bg,
         n_bg_overloads) = provenance_data

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
            elif self.app_vertex.drop_late_spikes:
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
    def get_n_keys_for_partition(self, partition_id: str) -> int:
        n_keys = super().get_n_keys_for_partition(partition_id)
        v = self.app_vertex
        n_colours = 2 ** v.n_colour_bits
        return n_keys * v.n_delay_stages * n_colours

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self) -> str:
        return "delay_extension.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self) -> ExecutableType:
        return ExecutableType.USES_SIMULATION_INTERFACE

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(
            self, spec: DataSpecificationGenerator, placement: Placement):
        vertex = placement.vertex

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        delay_params_sz = self.app_vertex.delay_params_size()

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.SYSTEM,
            size=SIMULATION_N_BYTES, label='setup')

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS,
            size=delay_params_sz, label='delay_params')

        # reserve region for provenance
        self.reserve_provenance_data_region(spec)

        self._write_setup_info(spec, vertex.get_binary_file_name())

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        routing_infos = SpynnakerDataView.get_routing_infos()
        key = routing_infos.get_first_key_from_pre_vertex(
            vertex, SPIKE_PARTITION_ID)

        srcs = self.app_vertex.source_vertex.splitter.get_out_going_vertices(
            SPIKE_PARTITION_ID)
        for source_vertex in srcs:
            if source_vertex.vertex_slice == self.vertex_slice:
                r_info = routing_infos.get_routing_info_from_pre_vertex(
                    source_vertex, SPIKE_PARTITION_ID)
                assert (r_info is not None)
                incoming_key = r_info.key
                incoming_mask = r_info.mask
                break

        self.write_delay_parameters(
            spec, self.vertex_slice, key, incoming_key, incoming_mask)

        # End-of-Spec:
        spec.end_specification()

    def _write_setup_info(self, spec, binary_name):
        """
        :param ~data_specification.DataSpecificationGenerator spec:
        :param str binary_name: the binary name
        """
        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(self._DELAY_EXTENSION_REGIONS.SYSTEM)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            binary_name))

    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask):
        """
        Generate Delay Parameter data.

        :param ~data_specification.DataSpecificationGenerator spec:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int key:
        :param int incoming_key:
        :param int incoming_mask:
        """
        # pylint: disable=too-many-arguments

        # Write spec with commands to construct required delay region:
        spec.comment(
            f"Writing Delay Parameters for {vertex_slice.n_atoms} Neurons:\n")

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS)

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

        app_vertex = self.app_vertex
        # Write the number of blocks of delays:
        spec.write_value(data=app_vertex.n_delay_stages)

        # write the delay per delay stage
        spec.write_value(data=app_vertex.delay_per_stage)

        # write whether to throw away spikes
        spec.write_value(data=int(app_vertex.drop_late_spikes))

        # Write the number of colour bits
        spec.write_value(data=app_vertex.n_colour_bits)
