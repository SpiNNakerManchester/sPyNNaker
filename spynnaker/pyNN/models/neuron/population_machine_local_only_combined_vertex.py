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

from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification, AbstractRewritesDataSpecification)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from .population_machine_common import CommonRegions, PopulationMachineCommon
from .population_machine_neurons import (
    NeuronRegions, PopulationMachineNeurons, NeuronProvenance)


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


class PopulationMachineLocalOnlyCombinedVertex(
        PopulationMachineCommon,
        PopulationMachineNeurons,
        AbstractGeneratesDataSpecification,
        AbstractRewritesDataSpecification):
    """ A machine vertex for PyNN Populations
    """

    __slots__ = [
        "__change_requires_neuron_parameters_reload",
        "__key",
        "__ring_buffer_shifts",
        "__weight_scales",
        "__slice_index"]

    # log_n_neurons, log_n_synapse_types, log_max_delay, input_buffer_size,
    # clear_input_buffer
    LOCAL_ONLY_SIZE = 5 * BYTES_PER_WORD

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
        NEURON_PARAMS = 4
        CURRENT_SOURCE_PARAMS = 5
        NEURON_RECORDING = 6
        LOCAL_ONLY = 7
        LOCAL_ONLY_PARAMS = 8

    # Regions for this vertex used by common parts
    COMMON_REGIONS = CommonRegions(
        system=REGIONS.SYSTEM.value,
        provenance=REGIONS.PROVENANCE_DATA.value,
        profile=REGIONS.PROFILING.value,
        recording=REGIONS.RECORDING.value)

    # Regions for this vertex used by neuron parts
    NEURON_REGIONS = NeuronRegions(
        neuron_params=REGIONS.NEURON_PARAMS.value,
        current_source_params=REGIONS.CURRENT_SOURCE_PARAMS.value,
        neuron_recording=REGIONS.NEURON_RECORDING.value
    )

    _PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "DMA_READ",
        2: "INCOMING_SPIKE"}

    def __init__(
            self, resources_required, label, constraints, app_vertex,
            vertex_slice, slice_index, ring_buffer_shifts, weight_scales):
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
        :param int all_syn_block_sz: The maximum size of the synapses in bytes
        :param int structural_sz: The size of the structural data
        """
        super(PopulationMachineLocalOnlyCombinedVertex, self).__init__(
            label, constraints, app_vertex, vertex_slice, resources_required,
            self.COMMON_REGIONS,
            NeuronProvenance.N_ITEMS +
            LocalOnlyProvenance.N_ITEMS + MainProvenance.N_ITEMS,
            self._PROFILE_TAG_LABELS, self.__get_binary_file_name(app_vertex))
        self.__key = None
        self.__change_requires_neuron_parameters_reload = False
        self.__slice_index = slice_index
        self.__ring_buffer_shifts = ring_buffer_shifts
        self.__weight_scales = weight_scales

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
    def parse_extra_provenance_items(self, label, x, y, p, provenance_data):
        proc_offset = NeuronProvenance.N_ITEMS
        end_proc_offset = proc_offset + LocalOnlyProvenance.N_ITEMS
        self._parse_neuron_provenance(
            label, x, y, p, provenance_data[:NeuronProvenance.N_ITEMS])
        self._parse_local_only_provenance(
            label, x, y, p, provenance_data[proc_offset:end_proc_offset])

        main_prov = MainProvenance(*provenance_data[-MainProvenance.N_ITEMS:])
        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, self.BACKGROUND_MAX_QUEUED_NAME,
                main_prov.max_background_queued)
            if main_prov.max_background_queued > 1:
                db.insert_report(
                    f"A maximum of {main_prov.max_background_queued}"
                    f" background tasks were queued on {label}.  Try"
                    " increasing the time_scale_factor located within the"
                    " .spynnaker.cfg file or in the pynn.setup() method.")
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
        # pylint: disable=arguments-differ
        rec_regions = self._app_vertex.neuron_recorder.get_region_sizes(
            self.vertex_slice)
        rec_regions.extend(self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice))
        self._write_common_data_spec(spec, rec_regions)

        self._write_neuron_data_spec(spec, self.__ring_buffer_shifts)

        self.__write_local_only_data(spec)

        self._app_vertex.synapse_dynamics.write_parameters(
            spec, self.REGIONS.LOCAL_ONLY_PARAMS.value,
            self._app_vertex.incoming_projections, self, self.__weight_scales)

        # End the writing of this specification:
        spec.end_specification()

    def __write_local_only_data(self, spec):
        spec.reserve_memory_region(
            self.REGIONS.LOCAL_ONLY.value, self.LOCAL_ONLY_SIZE, "local_only")
        spec.switch_write_focus(self.REGIONS.LOCAL_ONLY.value)
        log_n_neurons = get_n_bits(self._vertex_slice.n_atoms)
        log_n_synapse_types = get_n_bits(
            self._app_vertex.neuron_impl.get_n_synapse_types())
        # Delay is always 1
        log_max_delay = 1

        spec.write_value(log_n_neurons)
        spec.write_value(log_n_synapse_types)
        spec.write_value(log_max_delay)
        spec.write_value(self._app_vertex.incoming_spike_buffer_size)
        spec.write_value(int(self._app_vertex.drop_late_spikes))

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
