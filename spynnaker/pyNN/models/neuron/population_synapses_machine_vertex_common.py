# Copyright (c) 2017 The University of Manchester
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
from enum import Enum
import ctypes

from spinn_utilities.overrides import overrides
from spinn_utilities.abstract_base import abstractmethod
from spinn_utilities.config_holder import get_config_int
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.abstract_models import (
    ReceivesSynapticInputsOverSDRAM, SendsSynapticInputsOverSDRAM)
from .population_machine_common import CommonRegions, PopulationMachineCommon
from .population_machine_synapses import SynapseRegions
from .population_machine_synapses_provenance import SynapseProvenance

# Size of SDRAM params = 1 word for address + 1 word for size
#  + 1 word for time to send
SDRAM_PARAMS_SIZE = 3 * BYTES_PER_WORD

# Size of the Key config params = 1 work for key + 1 word for mask
#  + 1 word for spike mask + 1 word for colour shift
#  + 1 word for self connection boolean
KEY_CONFIG_SIZE = 5 * BYTES_PER_WORD


class SpikeProcessingFastProvenance(ctypes.LittleEndianStructure):
    _fields_ = [
        # A count of the times that the synaptic input circular buffers
        # overflowed
        ("n_buffer_overflows", ctypes.c_uint32),
        # The number of DMA transfers done
        ("n_dmas_complete", ctypes.c_uint32),
        # The number of spikes successfully processed
        ("n_spikes_processed", ctypes.c_uint32),
        # The number of rewirings performed.
        ("n_rewires", ctypes.c_uint32),
        # The number of packets that were dropped due to being late
        ("n_late_packets", ctypes.c_uint32),
        # The maximum size of the spike input buffer during simulation
        ("max_size_input_buffer", ctypes.c_uint32),
        # The maximum number of spikes in a time step
        ("max_spikes_received", ctypes.c_uint32),
        # The maximum number of spikes processed in a time step
        ("max_spikes_processed", ctypes.c_uint32),
        # The number of times the transfer time over ran
        ("n_transfer_timer_overruns", ctypes.c_uint32),
        # The number of times a time step was skipped entirely
        ("n_skipped_time_steps", ctypes.c_uint32),
        # The maximum overrun of a transfer
        ("max_transfer_timer_overrun", ctypes.c_uint32),
        # The earliest time a spike was received
        ("earliest_receive", ctypes.c_uint32),
        # The latest time a spike was received
        ("latest_receive", ctypes.c_uint32),
        # The maximum overflow of spikes in a time step
        ("max_spikes_overflow", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class PopulationSynapsesMachineVertexCommon(
        PopulationMachineCommon,
        SendsSynapticInputsOverSDRAM):
    """
    Common parts of a machine vertex for the synapses of a Population.
    """

    INPUT_BUFFER_FULL_NAME = "Times_the_input_buffer_lost_packets"
    DMA_COMPLETE = "DMA's that were completed"
    SPIKES_PROCESSED = "How many spikes were processed"
    N_REWIRES_NAME = "Number_of_rewires"
    N_LATE_SPIKES_NAME = "Number_of_late_spikes"
    MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME = "Max_filled_size_input_buffer"
    MAX_SPIKES_RECEIVED = "Max_spikes_received_in_time_step"
    MAX_SPIKES_PROCESSED = "Max_spikes_processed_in_time_step"
    N_TRANSFER_TIMER_OVERRUNS = "Times_the_transfer_did_not_complete_in_time"
    N_SKIPPED_TIME_STEPS = "Times_a_time_step_was_skipped"
    MAX_TRANSFER_TIMER_OVERRUNS = "Max_transfer_overrun"
    EARLIEST_RECEIVE = "Earliest_receive_time"
    LATEST_RECEIVE = "Latest_receive_time"
    MAX_SPIKE_OVERFLOW = "Max_spike_overflow_in_time_step"

    __slots__ = [
        "__sdram_partition",
        "__neuron_vertex",
        "__partition_id"]

    class REGIONS(Enum):
        """
        Regions for populations.
        """
        SYSTEM = 0
        PROVENANCE_DATA = 1
        PROFILING = 2
        RECORDING = 3
        SYNAPSE_PARAMS = 4
        SYNAPTIC_MATRIX = 5
        POPULATION_TABLE = 6
        SYNAPSE_DYNAMICS = 7
        STRUCTURAL_DYNAMICS = 8
        BIT_FIELD_FILTER = 9
        SDRAM_EDGE_PARAMS = 10
        KEY_REGION = 11
        CONNECTOR_BUILDER = 12

    # Regions for this vertex used by common parts
    COMMON_REGIONS = CommonRegions(
        system=REGIONS.SYSTEM.value,
        provenance=REGIONS.PROVENANCE_DATA.value,
        profile=REGIONS.PROFILING.value,
        recording=REGIONS.RECORDING.value)

    # Regions for this vertex used by synapse parts
    SYNAPSE_REGIONS = SynapseRegions(
        synapse_params=REGIONS.SYNAPSE_PARAMS.value,
        pop_table=REGIONS.POPULATION_TABLE.value,
        synaptic_matrix=REGIONS.SYNAPTIC_MATRIX.value,
        synapse_dynamics=REGIONS.SYNAPSE_DYNAMICS.value,
        structural_dynamics=REGIONS.STRUCTURAL_DYNAMICS.value,
        bitfield_filter=REGIONS.BIT_FIELD_FILTER.value,
        connection_builder=REGIONS.CONNECTOR_BUILDER.value
    )

    _PROFILE_TAG_LABELS = {
        0: "TIMER_SYNAPSES",
        1: "DMA_READ",
        2: "INCOMING_SPIKE",
        3: "PROCESS_FIXED_SYNAPSES",
        4: "PROCESS_PLASTIC_SYNAPSES"}

    def __init__(
            self, sdram, label, app_vertex,  vertex_slice):
        """
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The SDRAM used by the vertex
        :param str label: The label of the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        """
        super().__init__(
            label, app_vertex, vertex_slice, sdram, self.COMMON_REGIONS,
            SynapseProvenance.N_ITEMS + SpikeProcessingFastProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__sdram_partition = None
        self.__neuron_vertex = None
        self.__partition_id = None

    def set_sdram_partition(self, sdram_partition):
        """
        Set the SDRAM partition.  Must only be called once per instance.

        :param sdram_partition:
            The SDRAM partition to receive synapses from
        :type sdram_partition:
            ~pacman.model.graphs.machine.SourceSegmentedSDRAMMachinePartition
        """
        if self.__sdram_partition is not None:
            raise SynapticConfigurationException(
                "Trying to set SDRAM partition more than once")
        self.__sdram_partition = sdram_partition

    def set_neuron_vertex_and_partition_id(self, neuron_vertex, partition_id):
        """
        Set the neuron vertex and partition ID for the case with a
        self-connection.

        :param ~pacman.model.graphs.machine.MachineEdge neuron_to_synapse_edge:
            The edge that we will receive spikes from
        """
        self.__neuron_vertex = neuron_vertex
        self.__partition_id = partition_id

    @staticmethod
    def __get_binary_file_name(app_vertex):
        """
        Get the local binary filename for this vertex.  Static because at
        the time this is needed, the local `app_vertex` is not set.

        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :rtype: str
        """
        # Reunite title and extension and return
        return "synapses" + app_vertex.synapse_executable_suffix + ".aplx"

    @overrides(PopulationMachineCommon.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        ids = self._app_vertex.synapse_recorder.recorded_ids_by_slice(
            self.vertex_slice)
        return ids

    def _write_sdram_edge_spec(self, spec):
        """
        Write information about SDRAM Edge.

        :param DataSpecificationGenerator spec:
            The generator of the specification to write
        """
        send_size = self.__sdram_partition.get_sdram_size_of_region_for(self)
        spec.reserve_memory_region(
            region=self.REGIONS.SDRAM_EDGE_PARAMS.value,
            size=SDRAM_PARAMS_SIZE, label="SDRAM Params")
        spec.switch_write_focus(self.REGIONS.SDRAM_EDGE_PARAMS.value)
        spec.write_value(
            self.__sdram_partition.get_sdram_base_address_for(self))
        spec.write_value(send_size)
        spec.write_value(get_config_int(
            "Simulation", "transfer_overhead_clocks"))

    def _write_key_spec(self, spec):
        """
        Write key configuration region.

        :param DataSpecificationGenerator spec:
            The generator of the specification to write
        """
        spec.reserve_memory_region(
            region=self.REGIONS.KEY_REGION.value, size=KEY_CONFIG_SIZE,
            label="Key Config")
        spec.switch_write_focus(self.REGIONS.KEY_REGION.value)
        if self.__neuron_vertex is None:
            # No Key = make sure it doesn't match; i.e. spike & 0x0 != 0x1
            spec.write_value(1)
            spec.write_value(0)
            spec.write_value(0)
            spec.write_value(0)
        else:
            routing_info = SpynnakerDataView.get_routing_infos()
            r_info = routing_info.get_routing_info_from_pre_vertex(
                self.__neuron_vertex, self.__partition_id)
            spec.write_value(r_info.key)
            spec.write_value(r_info.mask)
            spec.write_value(~r_info.mask & 0xFFFFFFFF)
            spec.write_value(self._app_vertex.n_colour_bits)
            spec.write_value(int(self._app_vertex.self_projection is not None))

    @overrides(SendsSynapticInputsOverSDRAM.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge):
        if isinstance(sdram_machine_edge.post_vertex,
                      ReceivesSynapticInputsOverSDRAM):
            return sdram_machine_edge.post_vertex.n_bytes_for_transfer
        raise SynapticConfigurationException(
            f"Unknown post vertex type in edge {sdram_machine_edge}")

    @overrides(PopulationMachineCommon.parse_extra_provenance_items)
    def parse_extra_provenance_items(self, label, x, y, p, provenance_data):
        proc_offset = SynapseProvenance.N_ITEMS
        self._parse_synapse_provenance(
            label, x, y, p, provenance_data[:proc_offset])
        self._parse_spike_processing_fast_provenance(
            label, x, y, p, provenance_data[proc_offset:])

    @abstractmethod
    def _parse_synapse_provenance(self, label, x, y, p, provenance_data):
        """
        Extract and yield synapse provenance.

        :param str label: The label of the node
        :param int x: x coordinate of the chip where this core
        :param int y: y coordinate of the core where this core
        :param int p: virtual id of the core
        :param list(int) provenance_data: A list of data items to interpret
        """

    def _parse_spike_processing_fast_provenance(
            self, label, x, y, p, provenance_data):
        """
        Extract and yield spike processing provenance.

        :param str label: The label of the node
        :param int x: x coordinate of the chip where this core
        :param int y: y coordinate of the core where this core
        :param int p: virtual id of the core
        :param list(int) provenance_data: A list of data items to interpret
        """
        prov = SpikeProcessingFastProvenance(*provenance_data)

        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, self.INPUT_BUFFER_FULL_NAME,
                prov.n_buffer_overflows)
            if prov.n_buffer_overflows > 0:
                db.insert_report(
                    f"The input buffer for {label} lost packets on "
                    f"{prov.n_buffer_overflows} occasions. This is often a "
                    "sign that the system is running too quickly for the "
                    "number of neurons per core.  "
                    "Please increase the timer_tic or time_scale_factor or "
                    "decrease the number of neurons per core.")

            db.insert_core(x, y, p, self.DMA_COMPLETE, prov.n_dmas_complete)

            db.insert_core(
                x, y, p, self.SPIKES_PROCESSED, prov.n_spikes_processed)

            db.insert_core(
                x, y, p, self.N_REWIRES_NAME, prov.n_rewires)

            db.insert_core(
                x, y, p, self.N_LATE_SPIKES_NAME, prov.n_late_packets)
            if prov.n_late_packets == 0:
                pass
            elif self._app_vertex.drop_late_spikes:
                db.insert_report(
                    f"On {label}, {prov.n_late_packets} packets (maximum of "
                    f" {prov.max_spikes_overflow} per time step) were dropped "
                    "from the input buffer, because they arrived too late to "
                    "be processed in a given time step. Try increasing the "
                    "time_scale_factor located within the .spynnaker.cfg file "
                    "or in the pynn.setup() method.")
            else:
                db.insert_report(
                    f"On {label}, {prov.n_late_packets} packets (maximum of "
                    f" {prov.max_spikes_overflow} per time step) arrived too "
                    "late to be processed in a given time step. "
                    "Try increasing the time_scale_factor located within the"
                    " .spynnaker.cfg file or in the pynn.setup() method.")

            db.insert_core(
                x, y, p, self.MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME,
                prov.max_size_input_buffer)

            db.insert_core(
                x, y, p, self.MAX_SPIKES_RECEIVED, prov.max_spikes_received)

            db.insert_core(
                x, y, p, self.MAX_SPIKES_PROCESSED, prov.max_spikes_processed)

            db.insert_core(
                x, y, p, self.N_TRANSFER_TIMER_OVERRUNS,
                prov.n_transfer_timer_overruns)
            if prov.n_transfer_timer_overruns > 0:
                db.insert_report(
                    f"On {label}, the transfer of synaptic inputs to SDRAM "
                    f"did not end before the next timer tick started "
                    f"{prov.n_transfer_timer_overruns} times with a maximum "
                    f"overrun of {prov.max_transfer_timer_overrun}.  "
                    f"Try increasing transfer_overhead_clocks in your "
                    f".spynnaker.cfg file.")

            db.insert_core(
                x, y, p, self.N_SKIPPED_TIME_STEPS, prov.n_skipped_time_steps)
            if prov.n_skipped_time_steps > 0:
                db.insert_report(
                    f"On {label}, synaptic processing did not start on"
                    f" {prov.n_skipped_time_steps} time steps.  "
                    f"Try increasing the time_scale_factor located within the "
                    f".spynnaker.cfg file or in the pynn.setup() method.")

            db.insert_core(
                x, y, p, self.MAX_TRANSFER_TIMER_OVERRUNS,
                prov.max_transfer_timer_overrun)

            db.insert_core(
                x, y, p, self.EARLIEST_RECEIVE, prov.earliest_receive)
            db.insert_core(
                x, y, p, self.LATEST_RECEIVE, prov.latest_receive)
            db.insert_core(
                x, y, p, self.MAX_SPIKE_OVERFLOW, prov.max_spikes_overflow)
