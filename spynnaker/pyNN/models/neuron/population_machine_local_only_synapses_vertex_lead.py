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
import ctypes

from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from .population_machine_local_only_synapses_vertex_common import (
    PopulationMachineLocalOnlySynapsesVertexCommon)


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


class PopulationMachineLocalOnlySynapsesVertexLead(
        PopulationMachineLocalOnlySynapsesVertexCommon,
        AbstractGeneratesDataSpecification):
    """ A machine vertex for PyNN Populations
    """

    __slots__ = [
        "__weight_scales",
        "__max_atoms_per_core",
        "__synapse_references"]

    # log_n_neurons, log_n_synapse_types, log_max_delay, input_buffer_size,
    # clear_input_buffer, update key, update mask
    LOCAL_ONLY_SIZE = 7 * BYTES_PER_WORD

    _PROFILE_TAG_LABELS = {
        0: "TIMER",
        1: "DMA_READ",
        2: "INCOMING_SPIKE"}

    def __init__(
            self, sdram, label, app_vertex, vertex_slice,
            weight_scales, max_atoms_per_core, synapse_references):
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
        super(PopulationMachineLocalOnlySynapsesVertexLead, self).__init__(
            sdram, label, app_vertex, vertex_slice)
        self.__weight_scales = weight_scales
        self.__max_atoms_per_core = max_atoms_per_core
        self.__synapse_references = synapse_references

    @overrides(AbstractGeneratesDataSpecification.generate_data_specification)
    def generate_data_specification(self, spec, placement):
        # pylint: disable=arguments-differ
        rec_regions = self._app_vertex.synapse_recorder.get_region_sizes(
            self.vertex_slice)
        self._write_common_data_spec(spec, rec_regions)
        self._write_sdram_edge_spec(spec)

        self.__write_local_only_data(spec)

        self._app_vertex.synapse_dynamics.write_parameters(
            spec, self.REGIONS.LOCAL_ONLY_PARAMS.value, self,
            self.__weight_scales, self.__synapse_references.local_only_params)

        # End the writing of this specification:
        spec.end_specification()

    def __write_local_only_data(self, spec):
        spec.reserve_memory_region(
            self.REGIONS.LOCAL_ONLY.value, self.LOCAL_ONLY_SIZE, "local_only",
            reference=self.__synapse_references.local_only)
        spec.switch_write_focus(self.REGIONS.LOCAL_ONLY.value)
        log_n_max_atoms = get_n_bits(self.__max_atoms_per_core)
        log_n_synapse_types = get_n_bits(
            self._app_vertex.neuron_impl.get_n_synapse_types())
        # Delay is always 1
        log_max_delay = 1

        spec.write_value(log_n_max_atoms)
        spec.write_value(log_n_synapse_types)
        spec.write_value(log_max_delay)
        spec.write_value(self._app_vertex.incoming_spike_buffer_size)
        spec.write_value(int(self._app_vertex.drop_late_spikes))

        key, mask = self._app_vertex.synapse_dynamics.control_key_and_mask
        if key is None:
            key = 0xFFFFFFFF
            mask = 0
        spec.write_value(key)
        spec.write_value(mask)
