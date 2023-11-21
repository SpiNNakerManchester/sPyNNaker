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
from enum import IntEnum
import os
import ctypes
from numpy import floating
from numpy.typing import NDArray
from typing import List, Optional, Sequence

from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import (
    MachineVertex, SDRAMMachineEdge, SourceSegmentedSDRAMMachinePartition)
from pacman.model.graphs.common import Slice
from pacman.model.resources import AbstractSDRAM
from pacman.model.placements import Placement
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification)
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spinn_front_end_common.interface.ds import (
    DataSpecificationGenerator, DataSpecificationReloader)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.abstract_models import (
    ReceivesSynapticInputsOverSDRAM, SendsSynapticInputsOverSDRAM)
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from .population_machine_common import CommonRegions, PopulationMachineCommon
from .population_machine_neurons import (
    NeuronRegions, PopulationMachineNeurons, NeuronProvenance)
from .abstract_population_vertex import AbstractPopulationVertex
from spynnaker.pyNN.models.neuron.neuron_data import NeuronData

# Size of SDRAM params = 1 word for address + 1 word for size
# + 1 word for n_neurons + 1 word for n_synapse_types
# + 1 word for number of synapse vertices
# + 1 word for number of neuron bits needed
SDRAM_PARAMS_SIZE = 6 * BYTES_PER_WORD


class NeuronMainProvenance(ctypes.LittleEndianStructure):
    """
    Provenance items from synapse processing.
    """
    _fields_ = [
        # the maximum number of times the timer tick didn't complete in time
        ("n_timer_overruns", ctypes.c_uint32),
    ]

    N_ITEMS = len(_fields_)


class PopulationNeuronsMachineVertex(
        PopulationMachineCommon,
        PopulationMachineNeurons,
        AbstractGeneratesDataSpecification,
        AbstractRewritesDataSpecification,
        ReceivesSynapticInputsOverSDRAM):
    """
    A machine vertex for the Neurons of PyNN Populations.
    """

    __slots__ = (
        "__key",
        "__sdram_partition",
        "__ring_buffer_shifts",
        "__weight_scales",
        "__slice_index",
        "__neuron_data",
        "__max_atoms_per_core",
        "__regenerate_data")

    class REGIONS(IntEnum):
        """
        Regions for populations.
        """
        SYSTEM = 0
        CORE_PARAMS = 1
        PROVENANCE_DATA = 2
        PROFILING = 3
        RECORDING = 4
        NEURON_PARAMS = 5
        CURRENT_SOURCE_PARAMS = 6
        NEURON_RECORDING = 7
        SDRAM_EDGE_PARAMS = 8
        NEURON_BUILDER = 9
        INITIAL_VALUES = 10

    #: Regions for this vertex used by common parts
    COMMON_REGIONS = CommonRegions(
        REGIONS.SYSTEM,
        REGIONS.PROVENANCE_DATA,
        REGIONS.PROFILING,
        REGIONS.RECORDING)

    #: Regions for this vertex used by neuron parts
    NEURON_REGIONS = NeuronRegions(
        REGIONS.CORE_PARAMS,
        REGIONS.NEURON_PARAMS,
        REGIONS.CURRENT_SOURCE_PARAMS,
        REGIONS.NEURON_RECORDING,
        REGIONS.NEURON_BUILDER,
        REGIONS.INITIAL_VALUES)

    _PROFILE_TAG_LABELS = {
        0: "TIMER_NEURONS"}

    def __init__(
            self, sdram: AbstractSDRAM, label: str,
            app_vertex: AbstractPopulationVertex, vertex_slice: Slice,
            slice_index: int, ring_buffer_shifts: Sequence[int],
            weight_scales: NDArray[floating],
            neuron_data: NeuronData, max_atoms_per_core: int):
        """
        :param ~pacman.model.resources.AbstractSDRAM sdram:
            The SDRAM used by the vertex
        :param str label: The label of the vertex
        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the population that this implements
        :param int slice_index:
            The index of the slice in the ordered list of slices
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        :param list(int) weight_scales:
            The scaling to apply to weights to store them in the synapses
        :param NeuronData neuron_data:
            The handler of neuron data
        :param int max_atoms_per_core:
            The maximum number of atoms per core
        """
        super().__init__(
            label, app_vertex, vertex_slice, sdram, self.COMMON_REGIONS,
            NeuronProvenance.N_ITEMS + NeuronMainProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__key: Optional[int] = None
        self.__sdram_partition: Optional[
            SourceSegmentedSDRAMMachinePartition] = None
        self.__slice_index = slice_index
        self.__ring_buffer_shifts = ring_buffer_shifts
        self.__weight_scales = weight_scales
        self.__neuron_data = neuron_data
        self.__max_atoms_per_core = max_atoms_per_core
        self.__regenerate_data = False

    @property
    def _vertex_slice(self) -> Slice:
        return self.vertex_slice

    @property
    @overrides(PopulationMachineNeurons._slice_index)
    def _slice_index(self) -> int:
        return self.__slice_index

    @property
    @overrides(PopulationMachineNeurons._key)
    def _key(self) -> int:
        if self.__key is None:
            raise RuntimeError("key not yet set")
        return self.__key

    @property
    @overrides(PopulationMachineNeurons._has_key)
    def _has_key(self) -> bool:
        return self.__key is not None

    @overrides(PopulationMachineNeurons._set_key)
    def _set_key(self, key: int):
        self.__key = key

    @property
    @overrides(PopulationMachineNeurons._neuron_regions)
    def _neuron_regions(self) -> NeuronRegions:
        return self.NEURON_REGIONS

    @property
    @overrides(PopulationMachineNeurons._neuron_data)
    def _neuron_data(self) -> NeuronData:
        return self.__neuron_data

    @property
    @overrides(PopulationMachineNeurons._max_atoms_per_core)
    def _max_atoms_per_core(self) -> int:
        return self.__max_atoms_per_core

    def set_sdram_partition(
            self, sdram_partition: SourceSegmentedSDRAMMachinePartition):
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

    @staticmethod
    def __get_binary_file_name(app_vertex: AbstractPopulationVertex) -> str:
        """
        Get the local binary filename for this vertex.  Static because at
        the time this is needed, the local app_vertex is not set.

        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :rtype: str
        """
        # Split binary name into title and extension
        name, ext = os.path.splitext(app_vertex.neuron_impl.binary_name)

        # Reunite title and extension and return
        return name + "_neuron" + ext

    @overrides(PopulationMachineCommon.parse_extra_provenance_items)
    def parse_extra_provenance_items(
            self, label: str, x: int, y: int, p: int,
            provenance_data: Sequence[int]):
        self._parse_neuron_provenance(
            x, y, p, provenance_data[:NeuronProvenance.N_ITEMS])

        neuron_prov = NeuronMainProvenance(
            *provenance_data[-NeuronMainProvenance.N_ITEMS:])

        with ProvenanceWriter() as db:
            db.insert_core(x, y, p, "Timer tick overruns",
                           neuron_prov.n_timer_overruns)
            if neuron_prov.n_timer_overruns > 0:
                db.insert_report(
                    f"Vertex {label} overran on "
                    f"{neuron_prov.n_timer_overruns} timesteps. "
                    f"This may mean that the simulation results are invalid."
                    " Try with fewer neurons per core, increasing the time"
                    " scale factor, or reducing the number of spikes sent")

    @overrides(PopulationMachineCommon.get_recorded_region_ids)
    def get_recorded_region_ids(self) -> List[int]:
        ids = self._pop_vertex.neuron_recorder.recorded_ids_by_slice(
            self.vertex_slice)
        return ids

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(
            self, spec: DataSpecificationGenerator, placement: Placement):
        assert self.__sdram_partition is not None
        rec_regions = self._pop_vertex.neuron_recorder.get_region_sizes(
            self.vertex_slice)
        self._write_common_data_spec(spec, rec_regions)

        self._write_neuron_data_spec(spec, self.__ring_buffer_shifts)

        # Write information about SDRAM
        spec.reserve_memory_region(
            region=self.REGIONS.SDRAM_EDGE_PARAMS,
            size=SDRAM_PARAMS_SIZE, label="SDRAM Params")
        spec.switch_write_focus(self.REGIONS.SDRAM_EDGE_PARAMS)
        spec.write_value(
            self.__sdram_partition.get_sdram_base_address_for(self))
        spec.write_value(self.n_bytes_for_transfer)
        spec.write_value(len(self.__sdram_partition.pre_vertices))

        # End the writing of this specification:
        spec.end_specification()

    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(
            self, spec: DataSpecificationReloader, placement: Placement):
        # Write the other parameters
        self._rewrite_neuron_data_spec(spec)

        # close spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self) -> bool:
        return self.__regenerate_data

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value: bool):
        self.__regenerate_data = new_value

    @property
    @overrides(ReceivesSynapticInputsOverSDRAM.weight_scales)
    def weight_scales(self) -> NDArray[floating]:
        return self.__weight_scales

    @staticmethod
    def get_n_bytes_for_transfer(n_neurons: int, n_synapse_types: int) -> int:
        n_bytes = (2 ** get_n_bits(n_neurons) *
                   n_synapse_types *
                   ReceivesSynapticInputsOverSDRAM.N_BYTES_PER_INPUT)
        # May need to add some padding if not a round number of words
        extra_bytes = n_bytes % BYTES_PER_WORD
        if extra_bytes:
            n_bytes += BYTES_PER_WORD - extra_bytes
        return n_bytes

    @property
    @overrides(ReceivesSynapticInputsOverSDRAM.n_bytes_for_transfer)
    def n_bytes_for_transfer(self) -> int:
        return self.get_n_bytes_for_transfer(
            self.__max_atoms_per_core,
            self._pop_vertex.neuron_impl.get_n_synapse_types())

    @overrides(ReceivesSynapticInputsOverSDRAM.sdram_requirement)
    def sdram_requirement(self, sdram_machine_edge: SDRAMMachineEdge):
        if isinstance(sdram_machine_edge.pre_vertex,
                      SendsSynapticInputsOverSDRAM):
            return self.n_bytes_for_transfer
        raise SynapticConfigurationException(
            f"Unknown pre vertex type in edge {sdram_machine_edge}")

    @overrides(PopulationMachineNeurons.set_do_neuron_regeneration)
    def set_do_neuron_regeneration(self) -> None:
        self.__regenerate_data = True
        self.__neuron_data.reset_generation()

    @overrides(MachineVertex.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id: str) -> int:
        n_colours = 2 ** self._pop_vertex.n_colour_bits
        return self.vertex_slice.n_atoms * n_colours
