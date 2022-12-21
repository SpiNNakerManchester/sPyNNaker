# Copyright (c) 2021-2022 The University of Manchester
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
import ctypes
from collections import namedtuple

from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import get_config_int
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.abstract_models import (
    SendsSynapticInputsOverSDRAM, ReceivesSynapticInputsOverSDRAM)
from .population_machine_common import CommonRegions, PopulationMachineCommon

# Size of SDRAM params = 1 word for address + 1 word for size
#  + 1 word for time to send
SDRAM_PARAMS_SIZE = 3 * BYTES_PER_WORD

# Identifiers for local only shared regions
LOCAL_ONLY_FIELDS = [
    "local_only", "local_only_params"]
LocalOnlyRegions = namedtuple(
    "SynapseRegions", LOCAL_ONLY_FIELDS)


class LocalOnlyProvenance(ctypes.LittleEndianStructure):
    _fields_ = [
        # The maximum number of spikes received in a time step
        ("max_spikes_per_timestep", ctypes.c_uint32),
        # The number of packets that were dropped due to being late
        ("n_spikes_dropped", ctypes.c_uint32),
        # A count of the times that the synaptic input circular buffers
        # overflowed
        ("n_spikes_lost_from_input", ctypes.c_uint32),
        # The maximum size of the spike input buffer during simulation
        ("max_size_input_buffer", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class PopulationMachineLocalOnlySynapsesVertexCommon(
        PopulationMachineCommon,
        SendsSynapticInputsOverSDRAM):
    """ A machine vertex for PyNN Populations
    """

    __slots__ = [
        "__sdram_partition"]

    INPUT_BUFFER_FULL_NAME = "Times_the_input_buffer_lost_packets"
    N_LATE_SPIKES_NAME = "Number_of_late_spikes"
    MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME = "Max_filled_size_input_buffer"
    MAX_SPIKES_PER_TIME_STEP_NAME = "Max_spikes_per_time_step"
    BACKGROUND_OVERLOADS_NAME = "Times_the_background_queue_overloaded"
    BACKGROUND_MAX_QUEUED_NAME = "Max_backgrounds_queued"

    class REGIONS(Enum):
        """Regions for populations."""
        SYSTEM = 0
        PROVENANCE_DATA = 1
        PROFILING = 2
        RECORDING = 3
        LOCAL_ONLY = 4
        LOCAL_ONLY_PARAMS = 5
        SDRAM_EDGE_PARAMS = 6

    # Regions for this vertex used by common parts
    COMMON_REGIONS = CommonRegions(
        system=REGIONS.SYSTEM.value,
        provenance=REGIONS.PROVENANCE_DATA.value,
        profile=REGIONS.PROFILING.value,
        recording=REGIONS.RECORDING.value)

    _PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "DMA_READ",
        2: "INCOMING_SPIKE"}

    def __init__(
            self, sdram, label, app_vertex, vertex_slice):
        """
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The sdram used by the vertex
        :param str label: The label of the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        :param list(int) weight_scales:
            The scaling to apply to weights to store them in the synapses
        """
        super(PopulationMachineLocalOnlySynapsesVertexCommon, self).__init__(
            label, app_vertex, vertex_slice, sdram,
            self.COMMON_REGIONS,
            LocalOnlyProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__sdram_partition = None

    def set_sdram_partition(self, sdram_partition):
        """ Set the SDRAM partition.  Must only be called once per instance

        :param ~pacman.model.graphs.machine\
                .SourceSegmentedSDRAMMachinePartition sdram_partition:
            The SDRAM partition to receive synapses from
        """
        if self.__sdram_partition is not None:
            raise SynapticConfigurationException(
                "Trying to set SDRAM partition more than once")
        self.__sdram_partition = sdram_partition

    @staticmethod
    def __get_binary_file_name(app_vertex):
        """ Get the local binary filename for this vertex.  Static because at
            the time this is needed, the local app_vertex is not set.

        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :rtype: str
        """
        # Reunite title and extension and return
        return "local_only" + app_vertex.synapse_executable_suffix + ".aplx"

    @overrides(PopulationMachineCommon.parse_extra_provenance_items)
    def parse_extra_provenance_items(self, label, x, y, p, provenance_data):
        self._parse_local_only_provenance(
            label, x, y, p, provenance_data)

    @overrides(PopulationMachineCommon.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        ids = self._app_vertex.neuron_recorder.recorded_ids_by_slice(
            self.vertex_slice)
        ids.extend(self._app_vertex.synapse_recorder.recorded_ids_by_slice(
            self.vertex_slice))
        return ids

    def _write_sdram_edge_spec(self, spec):
        """ Write information about SDRAM Edge

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

    @overrides(SendsSynapticInputsOverSDRAM.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge):
        if isinstance(sdram_machine_edge.post_vertex,
                      ReceivesSynapticInputsOverSDRAM):
            return sdram_machine_edge.post_vertex.n_bytes_for_transfer
        raise SynapticConfigurationException(
            "Unknown post vertex type in edge {}".format(sdram_machine_edge))

    def _parse_local_only_provenance(
            self, label, x, y, p, provenance_data):
        """ Extract and yield local-only provenance

        :param str label: The label of the node
        :param int x: x coordinate of the chip where this core
        :param int y: y coordinate of the core where this core
        :param int p: virtual id of the core
        :param list(int) provenance_data: A list of data items to interpret
        :return: a list of provenance data items
        :rtype: iterator of ProvenanceDataItem
        """
        prov = LocalOnlyProvenance(*provenance_data)

        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, self.MAX_SPIKES_PER_TIME_STEP_NAME,
                prov.max_spikes_per_timestep)
            db.insert_core(
                x, y, p, self.INPUT_BUFFER_FULL_NAME,
                prov.n_spikes_lost_from_input)
            db.insert_core(
                x, y, p, self.N_LATE_SPIKES_NAME,
                prov.n_spikes_dropped)
            db.insert_core(
                x, y, p, self.MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME,
                prov.max_size_input_buffer)

            if prov.n_spikes_lost_from_input > 0:
                db.insert_report(
                    f"The input buffer for {label} lost packets on "
                    f"{prov.n_spikes_lost_from_input} occasions. This is "
                    "often sign that the system is running too quickly for "
                    "the number of neurons per core.  Please increase the "
                    "timer_tic or time_scale_factor or decrease the number "
                    "of neurons per core.")

            if prov.n_spikes_dropped > 0:
                if self._app_vertex.drop_late_spikes:
                    db.insert_report(
                        f"On {label}, {prov.n_spikes_dropped} packets were "
                        "dropped from the input buffer, because they arrived "
                        "too late to be processed in a given time step. Try "
                        "increasing the time_scale_factor located within the "
                        ".spynnaker.cfg file or in the pynn.setup() method.")
                else:
                    db.insert_report(
                        f"On {label}, {prov.n_spikes_dropped} packets arrived "
                        "too late to be processed in a given time step. Try "
                        "increasing the time_scale_factor located within the "
                        ".spynnaker.cfg file or in the pynn.setup() method.")
