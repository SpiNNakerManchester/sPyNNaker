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

from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification)
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from .population_machine_common import CommonRegions, PopulationMachineCommon
from .population_machine_neurons import (
    NeuronRegions, PopulationMachineNeurons, NeuronProvenance)
from .population_machine_synapses import (
    SynapseRegions, PopulationMachineSynapses)
from .population_machine_synapses_provenance import SynapseProvenance


class SpikeProcessingProvenance(ctypes.LittleEndianStructure):
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
        ("max_size_input_buffer", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class MainProvenance(ctypes.LittleEndianStructure):
    """
    Provenance items from synapse processing.
    """
    _fields_ = [
        # the maximum number of background tasks queued
        ("max_background_queued", ctypes.c_uint32),
        # the number of times the background queue overloaded
        ("n_background_overloads", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class PopulationMachineVertex(
        PopulationMachineCommon,
        PopulationMachineNeurons,
        PopulationMachineSynapses,
        AbstractGeneratesDataSpecification,
        AbstractRewritesDataSpecification):
    """
    A machine vertex for PyNN Populations.
    """

    __slots__ = (
        "__synaptic_matrices",
        "__neuron_data",
        "__key",
        "__ring_buffer_shifts",
        "__weight_scales",
        "__structural_sz",
        "__slice_index",
        "__max_atoms_per_core",
        "__regenerate_neuron_data",
        "__regenerate_synapse_data")

    INPUT_BUFFER_FULL_NAME = "Times_the_input_buffer_lost_packets"
    DMA_COMPLETE = "DMA's that were completed"
    SPIKES_PROCESSED = "How many spikes were processed"
    N_REWIRES_NAME = "Number_of_rewires"
    N_LATE_SPIKES_NAME = "Number_of_late_spikes"
    MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME = "Max_filled_size_input_buffer"
    BACKGROUND_OVERLOADS_NAME = "Times_the_background_queue_overloaded"
    BACKGROUND_MAX_QUEUED_NAME = "Max_backgrounds_queued"

    class REGIONS(IntEnum):
        """
        Regions for populations.
        """
        SYSTEM = 0
        CORE_PARAMS = 1
        NEURON_PARAMS = 2
        CURRENT_SOURCE_PARAMS = 3
        SYNAPSE_PARAMS = 4
        POPULATION_TABLE = 5
        SYNAPTIC_MATRIX = 6
        SYNAPSE_DYNAMICS = 7
        STRUCTURAL_DYNAMICS = 8
        NEURON_RECORDING = 9
        PROVENANCE_DATA = 10
        PROFILING = 11
        CONNECTOR_BUILDER = 12
        NEURON_BUILDER = 13
        BIT_FIELD_FILTER = 14
        RECORDING = 15
        INITIAL_VALUES = 16

    # Regions for this vertex used by common parts
    COMMON_REGIONS = CommonRegions(
        REGIONS.SYSTEM,
        REGIONS.PROVENANCE_DATA,
        REGIONS.PROFILING,
        REGIONS.RECORDING)

    # Regions for this vertex used by neuron parts
    NEURON_REGIONS = NeuronRegions(
        REGIONS.CORE_PARAMS,
        REGIONS.NEURON_PARAMS,
        REGIONS.CURRENT_SOURCE_PARAMS,
        REGIONS.NEURON_RECORDING,
        REGIONS.NEURON_BUILDER,
        REGIONS.INITIAL_VALUES)

    # Regions for this vertex used by synapse parts
    SYNAPSE_REGIONS = SynapseRegions(
        REGIONS.SYNAPSE_PARAMS,
        REGIONS.POPULATION_TABLE,
        REGIONS.SYNAPTIC_MATRIX,
        REGIONS.SYNAPSE_DYNAMICS,
        REGIONS.STRUCTURAL_DYNAMICS,
        REGIONS.BIT_FIELD_FILTER,
        REGIONS.CONNECTOR_BUILDER)

    _PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "DMA_READ",
        2: "INCOMING_SPIKE",
        3: "PROCESS_FIXED_SYNAPSES",
        4: "PROCESS_PLASTIC_SYNAPSES"}

    def __init__(
            self, sdram, label, app_vertex, vertex_slice, slice_index,
            ring_buffer_shifts, weight_scales,
            structural_sz, max_atoms_per_core, synaptic_matrices, neuron_data):
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
        :param int structural_sz: The size of the structural data
        :param int n_neuron_bits: The number of bits to use for neuron IDs
        :param SynapticMatrices synaptic_matrices: The synaptic matrices
        :param NeuronData neuron_data: The handler of neuron data
        """
        super().__init__(
            label, app_vertex, vertex_slice, sdram,
            self.COMMON_REGIONS,
            NeuronProvenance.N_ITEMS + SynapseProvenance.N_ITEMS +
            SpikeProcessingProvenance.N_ITEMS + MainProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__key = None
        self.__slice_index = slice_index
        self.__ring_buffer_shifts = ring_buffer_shifts
        self.__weight_scales = weight_scales
        self.__structural_sz = structural_sz
        self.__max_atoms_per_core = max_atoms_per_core
        self.__synaptic_matrices = synaptic_matrices
        self.__neuron_data = neuron_data
        self.__regenerate_neuron_data = False
        self.__regenerate_synapse_data = False

    @property
    @overrides(PopulationMachineNeurons._slice_index)
    def _slice_index(self):
        return self.__slice_index

    @property
    @overrides(PopulationMachineNeurons._key)
    def _key(self):
        return self.__key

    @overrides(PopulationMachineNeurons._set_key)
    def _set_key(self, key):
        self.__key = key

    @property
    @overrides(PopulationMachineNeurons._neuron_regions)
    def _neuron_regions(self):
        return self.NEURON_REGIONS

    @property
    @overrides(PopulationMachineNeurons._neuron_data)
    def _neuron_data(self):
        return self.__neuron_data

    @property
    @overrides(PopulationMachineSynapses._synapse_regions)
    def _synapse_regions(self):
        return self.SYNAPSE_REGIONS

    @property
    @overrides(PopulationMachineSynapses._synaptic_matrices)
    def _synaptic_matrices(self):
        return self.__synaptic_matrices

    @property
    @overrides(PopulationMachineSynapses._max_atoms_per_core)
    def _max_atoms_per_core(self):
        return self.__max_atoms_per_core

    @staticmethod
    def __get_binary_file_name(app_vertex):
        """
        Get the local binary filename for this vertex.  Static because at
        the time this is needed, the local `app_vertex` is not set.

        :param AbstractPopulationVertex app_vertex:
            The associated application vertex
        :rtype: str
        """
        # Split binary name into title and extension
        name, ext = os.path.splitext(app_vertex.neuron_impl.binary_name)

        # Reunite title and extension and return
        return name + app_vertex.synapse_executable_suffix + ext

    @overrides(PopulationMachineCommon.parse_extra_provenance_items)
    def parse_extra_provenance_items(
            self, label, x, y, p, provenance_data):
        syn_offset = NeuronProvenance.N_ITEMS
        proc_offset = syn_offset + SynapseProvenance.N_ITEMS
        end_proc_offset = proc_offset + SpikeProcessingProvenance.N_ITEMS
        self._parse_neuron_provenance(
            x, y, p, provenance_data[:NeuronProvenance.N_ITEMS])
        self._parse_synapse_provenance(
            label, x, y, p, provenance_data[syn_offset:proc_offset])
        self._parse_spike_processing_provenance(
            label, x, y, p, provenance_data[proc_offset:end_proc_offset])

        main_prov = MainProvenance(*provenance_data[-MainProvenance.N_ITEMS:])

        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, self.BACKGROUND_MAX_QUEUED_NAME,
                main_prov.max_background_queued)
            if main_prov.max_background_queued > 1:
                db.insert_report(
                    f"A maximum of {main_prov.max_background_queued} "
                    f"background tasks were queued on {label}.  "
                    f"Try increasing the time_scale_factor located within "
                    f"the .spynnaker.cfg file or in the pynn.setup() method.")

            db.insert_core(
                x, y, p, self.BACKGROUND_OVERLOADS_NAME,
                main_prov.n_background_overloads)
            if main_prov.n_background_overloads > 0:
                db.insert_report(
                    "The background queue overloaded "
                    f"{main_prov.n_background_overloads} times on {label}."
                    " Try increasing the time_scale_factor located within"
                    " the .spynnaker.cfg file or in the pynn.setup() method.")

    @overrides(PopulationMachineCommon.get_recorded_region_ids)
    def get_recorded_region_ids(self):
        ids = self._app_vertex.neuron_recorder.recorded_ids_by_slice(
            self.vertex_slice)
        ids.extend(self._app_vertex.synapse_recorder.recorded_ids_by_slice(
            self.vertex_slice))
        return ids

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(self, spec, placement):
        rec_regions = self._app_vertex.neuron_recorder.get_region_sizes(
            self.vertex_slice)
        rec_regions.extend(self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice))
        self._write_common_data_spec(spec, rec_regions)

        self._write_neuron_data_spec(spec, self.__ring_buffer_shifts)

        self._write_synapse_data_spec(
            spec, self.__ring_buffer_shifts,
            self.__weight_scales, self.__structural_sz)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(self, spec, placement):
        if self.__regenerate_neuron_data:
            self._rewrite_neuron_data_spec(spec)
            self.__regenerate_neuron_data = False

        if self.__regenerate_synapse_data:
            self._write_synapse_data_spec(
                spec, self.__ring_buffer_shifts,
                self.__weight_scales, self.__structural_sz)
            self.__regenerate_synapse_data = False

        # close spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self):
        return self.__regenerate_neuron_data or self.__regenerate_synapse_data

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value):
        # These are set elsewhere once data is generated
        pass

    def _parse_spike_processing_provenance(
            self, label, x, y, p, provenance_data):
        """
        Extract and yield spike processing provenance.

        :param str label: The label of the node
        :param int x: x coordinate of the chip where this core
        :param int y: y coordinate of the core where this core
        :param int p: virtual id of the core
        :param list(int) provenance_data: A list of data items to interpret
        """
        prov = SpikeProcessingProvenance(*provenance_data)

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

            db.insert_core(
                x, y, p, self.DMA_COMPLETE, prov.n_dmas_complete)

            db.insert_core(
                x, y, p, self.SPIKES_PROCESSED, prov.n_spikes_processed)

            db.insert_core(
                x, y, p, self.N_REWIRES_NAME, prov.n_rewires)

            db.insert_core(
                x, y, p, self.N_LATE_SPIKES_NAME,
                prov.n_late_packets)

            if prov.n_late_packets > 0:
                if self._app_vertex.drop_late_spikes:
                    db.insert_report(
                        f"On {label}, {prov.n_late_packets} packets were "
                        f"dropped from the input buffer, because they "
                        f"arrived too late to be processed in a given time "
                        f"step. Try increasing the time_scale_factor located "
                        f"within the .spynnaker.cfg file or in the "
                        f"pynn.setup() method.")
                else:
                    db.insert_report(
                        f"On {label}, {prov.n_late_packets} packets arrived "
                        f"too late to be processed in a given time step. "
                        "Try increasing the time_scale_factor located within "
                        "the .spynnaker.cfg file or in the pynn.setup() "
                        "method.")

            db.insert_core(
                x, y, p, self.MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME,
                prov.max_size_input_buffer)

    @overrides(PopulationMachineNeurons.set_do_neuron_regeneration)
    def set_do_neuron_regeneration(self):
        self.__regenerate_neuron_data = True
        self.__neuron_data.reset_generation()

    @overrides(PopulationMachineSynapses.set_do_synapse_regeneration)
    def set_do_synapse_regeneration(self):
        self.__regenerate_synapse_data = True

    @overrides(PopulationMachineCommon.get_n_keys_for_partition)
    def get_n_keys_for_partition(self, partition_id):
        n_colours = 2 ** self._app_vertex.n_colour_bits
        return self._vertex_slice.n_atoms * n_colours
