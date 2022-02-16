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
import os
import ctypes

from pacman.executor.injection_decorator import inject_items
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
    """ Provenance items from synapse processing
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
    """ A machine vertex for PyNN Populations
    """

    __slots__ = [
        "__change_requires_neuron_parameters_reload",
        "__synaptic_matrices",
        "__key",
        "__ring_buffer_shifts",
        "__weight_scales",
        "__structural_sz",
        "__slice_index",
        "__max_atoms_per_core"]

    INPUT_BUFFER_FULL_NAME = "Times_the_input_buffer_lost_packets"
    DMA_COMPLETE = "DMA's that were completed"
    SPIKES_PROCESSED = "How many spikes were processed"
    N_REWIRES_NAME = "Number_of_rewires"
    N_LATE_SPIKES_NAME = "Number_of_late_spikes"
    MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME = "Max_filled_size_input_buffer"
    BACKGROUND_OVERLOADS_NAME = "Times_the_background_queue_overloaded"
    BACKGROUND_MAX_QUEUED_NAME = "Max_backgrounds_queued"

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
        BIT_FIELD_FILTER = 11
        BIT_FIELD_BUILDER = 12
        BIT_FIELD_KEY_MAP = 13
        RECORDING = 14

    # Regions for this vertex used by common parts
    COMMON_REGIONS = CommonRegions(
        system=REGIONS.SYSTEM.value,
        provenance=REGIONS.PROVENANCE_DATA.value,
        profile=REGIONS.PROFILING.value,
        recording=REGIONS.RECORDING.value)

    # Regions for this vertex used by neuron parts
    NEURON_REGIONS = NeuronRegions(
        neuron_params=REGIONS.NEURON_PARAMS.value,
        neuron_recording=REGIONS.NEURON_RECORDING.value
    )

    # Regions for this vertex used by synapse parts
    SYNAPSE_REGIONS = SynapseRegions(
        synapse_params=REGIONS.SYNAPSE_PARAMS.value,
        pop_table=REGIONS.POPULATION_TABLE.value,
        synaptic_matrix=REGIONS.SYNAPTIC_MATRIX.value,
        synapse_dynamics=REGIONS.SYNAPSE_DYNAMICS.value,
        structural_dynamics=REGIONS.STRUCTURAL_DYNAMICS.value,
        bitfield_builder=REGIONS.BIT_FIELD_BUILDER.value,
        bitfield_key_map=REGIONS.BIT_FIELD_KEY_MAP.value,
        bitfield_filter=REGIONS.BIT_FIELD_FILTER.value,
        connection_builder=REGIONS.CONNECTOR_BUILDER.value
    )

    _PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "DMA_READ",
        2: "INCOMING_SPIKE",
        3: "PROCESS_FIXED_SYNAPSES",
        4: "PROCESS_PLASTIC_SYNAPSES"}

    def __init__(
            self, resources_required, label, constraints, app_vertex,
            vertex_slice, slice_index, ring_buffer_shifts, weight_scales,
            structural_sz, max_atoms_per_core, synaptic_matrices):
        """
        :param ~pacman.model.resources.ResourceContainer resources_required:
            The resources used by the vertex
        :param str label: The label of the vertex
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Constraints for the vertex
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
        :param int n_neuron_bits: The number of bits to use for neuron ids
        :param SynapticMatrices synaptic_matrices: The synaptic matrices
        """
        super(PopulationMachineVertex, self).__init__(
            label, constraints, app_vertex, vertex_slice, resources_required,
            self.COMMON_REGIONS,
            NeuronProvenance.N_ITEMS + SynapseProvenance.N_ITEMS +
            SpikeProcessingProvenance.N_ITEMS + MainProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__key = None
        self.__change_requires_neuron_parameters_reload = False
        self.__slice_index = slice_index
        self.__ring_buffer_shifts = ring_buffer_shifts
        self.__weight_scales = weight_scales
        self.__structural_sz = structural_sz
        self.__max_atoms_per_core = max_atoms_per_core
        self.__synaptic_matrices = synaptic_matrices

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
        """ Get the local binary filename for this vertex.  Static because at
            the time this is needed, the local app_vertex is not set.

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
            label, x, y, p, provenance_data[:NeuronProvenance.N_ITEMS])
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

    @inject_items({
        "routing_info": "RoutingInfos",
        "data_n_time_steps": "DataNTimeSteps"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "routing_info", "data_n_time_steps"
        })
    def generate_data_specification(
            self, spec, placement, routing_info, data_n_time_steps):
        """
        :param routing_info: (injected)
        :param data_n_time_steps: (injected)
        """
        # pylint: disable=arguments-differ
        rec_regions = self._app_vertex.neuron_recorder.get_region_sizes(
            self.vertex_slice, data_n_time_steps)
        rec_regions.extend(self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice, data_n_time_steps))
        self._write_common_data_spec(spec, rec_regions)

        self._write_neuron_data_spec(
            spec, routing_info, self.__ring_buffer_shifts)

        self._write_synapse_data_spec(
            spec, routing_info, self.__ring_buffer_shifts,
            self.__weight_scales, self.__structural_sz)

        # End the writing of this specification:
        spec.end_specification()

    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification)
    def regenerate_data_specification(self, spec, placement):
        # pylint: disable=too-many-arguments, arguments-differ

        # write the neuron params into the new DSG region
        self._write_neuron_parameters(spec, self.__ring_buffer_shifts)

        # close spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification.reload_required)
    def reload_required(self):
        return self.__change_requires_neuron_parameters_reload

    @overrides(AbstractRewritesDataSpecification.set_reload_required)
    def set_reload_required(self, new_value):
        self.__change_requires_neuron_parameters_reload = new_value

    def _parse_spike_processing_provenance(
            self, label, x, y, p, provenance_data):
        """ Extract and yield spike processing provenance

        :param str label: The label of the node
        :param int x: x coordinate of the chip where this core
        :param int y: y coordinate of the core where this core
        :param int p: virtual id of the core
        :param list(int) provenance_data: A list of data items to interpret
        :return: a list of provenance data items
        :rtype: iterator of ProvenanceDataItem
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
