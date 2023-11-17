# Copyright (c) 2015 The University of Manchester
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
import numpy
from numpy import uint8, uint32, integer
from numpy.typing import NDArray
from pyNN.standardmodels.synapses import StaticSynapse
from typing import Iterable, List, Optional, Tuple, TYPE_CHECKING
from spinn_utilities.overrides import overrides
from pacman.model.graphs.common import Slice
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    NUMPY_CONNECTORS_DTYPE)
from .abstract_static_synapse_dynamics import AbstractStaticSynapseDynamics
from .abstract_generate_on_machine import (
    AbstractGenerateOnMachine, MatrixGeneratorID)
from .synapse_dynamics_neuromodulation import SynapseDynamicsNeuromodulation
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.types import Weight_Delay_In_Types as _Weight
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
if TYPE_CHECKING:
    from .abstract_synapse_dynamics import AbstractSynapseDynamics
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.neuron.synapse_io import MaxRowInfo
    from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
        ConnectionsArray)


class SynapseDynamicsStatic(
        AbstractStaticSynapseDynamics,
        AbstractGenerateOnMachine):
    """
    The dynamics of a synapse that does not change over time.
    """

    __slots__ = (
        # padding to add to a synaptic row for synaptic rewiring
        "__pad_to_length")

    def __init__(
            self, weight: _Weight = StaticSynapse.default_parameters['weight'],
            delay: Optional[float] = None,
            pad_to_length: Optional[int] = None):

        """
        :param float weight:
        :param delay: Use ``None`` to get the simulator default minimum delay.
        :type delay: float or None
        :param int pad_to_length:
        """
        super(AbstractStaticSynapseDynamics, self).__init__(
            delay=delay, weight=weight)
        self.__pad_to_length = pad_to_length

    @overrides(AbstractStaticSynapseDynamics.merge)
    def merge(self, synapse_dynamics: AbstractSynapseDynamics
              ) -> AbstractSynapseDynamics:
        # Neuromodulation shouldn't be used without STDP
        if isinstance(synapse_dynamics, SynapseDynamicsNeuromodulation):
            raise SynapticConfigurationException(
                "Neuromodulation can only be added when an STDP projection"
                " has already been added")

        # We can always override a static synapse dynamics with a more
        # complex model
        return synapse_dynamics

    @overrides(AbstractStaticSynapseDynamics.is_same_as)
    def is_same_as(self, synapse_dynamics: AbstractSynapseDynamics) -> bool:
        return isinstance(synapse_dynamics, SynapseDynamicsStatic)

    @overrides(AbstractStaticSynapseDynamics.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self) -> str:
        return ""

    @overrides(AbstractStaticSynapseDynamics.
               get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_neurons, n_synapse_types) -> int:
        return 0

    @overrides(AbstractStaticSynapseDynamics.write_parameters)
    def write_parameters(
            self, spec, region, global_weight_scale, synapse_weight_scales):
        # Nothing to do here
        pass

    @overrides(
        AbstractStaticSynapseDynamics.get_n_words_for_static_connections)
    def get_n_words_for_static_connections(self, n_connections: int) -> int:
        if (self.__pad_to_length is not None and
                n_connections < self.__pad_to_length):
            n_connections = self.__pad_to_length
        return n_connections

    @overrides(AbstractStaticSynapseDynamics.get_static_synaptic_data)
    def get_static_synaptic_data(
            self, connections: ConnectionsArray,
            connection_row_indices: NDArray[integer], n_rows: int,
            post_vertex_slice: Slice, n_synapse_types: int,
            max_n_synapses: int, max_atoms_per_core: int) -> Tuple[
                List[NDArray], NDArray]:
        n_neuron_id_bits = get_n_bits(max_atoms_per_core)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1
        n_synapse_type_bits = get_n_bits(n_synapse_types)

        fixed_fixed = (
            ((numpy.rint(numpy.abs(connections["weight"])).astype(uint32) &
              0xFFFF) << 16) |
            (connections["delay"].astype(uint32) <<
             (n_neuron_id_bits + n_synapse_type_bits)) |
            (connections["synapse_type"].astype(uint32) << n_neuron_id_bits) |
            ((connections["target"] - post_vertex_slice.lo_atom) &
             neuron_id_mask))
        fixed_fixed_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_fixed.view(uint8).reshape((-1, BYTES_PER_WORD)),
            max_n_synapses)
        ff_size = self.get_n_items(fixed_fixed_rows, BYTES_PER_WORD)
        if self.__pad_to_length is not None:
            # Pad the data
            fixed_fixed_rows = self._pad_row(fixed_fixed_rows, BYTES_PER_WORD)
        ff_data = [fixed_row.view(uint32) for fixed_row in fixed_fixed_rows]

        return ff_data, ff_size

    def _pad_row(self, rows, no_bytes_per_connection):
        """
        :param list(~numpy.ndarray) rows:
        :param int no_bytes_per_connection:
        :rtype: list(~numpy.ndarray)
        """
        return [
            numpy.concatenate([
                row, numpy.zeros(numpy.clip(
                    no_bytes_per_connection * self.__pad_to_length -
                    row.size, 0, None)).astype(dtype=uint8)]).view(uint8)
            for row in rows]  # Row elements are (individual) bytes

    @overrides(AbstractStaticSynapseDynamics.get_n_static_words_per_row)
    def get_n_static_words_per_row(self, ff_size: NDArray) -> NDArray:
        # The sizes are in words, so just return them
        return ff_size

    @overrides(AbstractStaticSynapseDynamics.get_n_synapses_in_rows)
    def get_n_synapses_in_rows(self, ff_size: NDArray) -> NDArray:
        # Each word is a synapse and sizes are in words, so just return them
        return ff_size

    @overrides(AbstractStaticSynapseDynamics.read_static_synaptic_data)
    def read_static_synaptic_data(
            self, post_vertex_slice, n_synapse_types, ff_size, ff_data,
            max_atoms_per_core):
        n_synapse_type_bits = get_n_bits(n_synapse_types)
        n_neuron_id_bits = get_n_bits(max_atoms_per_core)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1

        data = numpy.concatenate(ff_data)
        connections = numpy.zeros(data.size, dtype=NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate(
            [numpy.repeat(i, ff_size[i]) for i in range(len(ff_size))])
        connections["target"] = (
            (data & neuron_id_mask) + post_vertex_slice.lo_atom)
        connections["weight"] = (data >> 16) & 0xFFFF
        connections["delay"] = (data & 0xFFFF) >> (
            n_neuron_id_bits + n_synapse_type_bits)

        return connections

    @overrides(AbstractStaticSynapseDynamics.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        return ('weight', 'delay')

    @overrides(AbstractStaticSynapseDynamics.get_max_synapses)
    def get_max_synapses(self, n_words):
        return n_words

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_id)
    def gen_matrix_id(self):
        return MatrixGeneratorID.STATIC_MATRIX.value

    @overrides(AbstractGenerateOnMachine.gen_matrix_params)
    def gen_matrix_params(
            self, synaptic_matrix_offset: int, delayed_matrix_offset: int,
            app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation, max_row_info: MaxRowInfo,
            max_pre_atoms_per_core: int,
            max_post_atoms_per_core: int) -> NDArray[uint32]:
        vertex = app_edge.post_vertex
        n_synapse_type_bits = get_n_bits(
            vertex.neuron_impl.get_n_synapse_types())
        n_synapse_index_bits = get_n_bits(max_post_atoms_per_core)
        max_delay = vertex.splitter.max_support_delay()
        max_delay_bits = get_n_bits(max_delay)
        return numpy.array([
            synaptic_matrix_offset, delayed_matrix_offset,
            max_row_info.undelayed_max_words, max_row_info.delayed_max_words,
            synapse_info.synapse_type, n_synapse_type_bits,
            n_synapse_index_bits, app_edge.n_delay_stages + 1,
            max_delay, max_delay_bits, app_edge.pre_vertex.n_atoms,
            max_pre_atoms_per_core],
            dtype=uint32)

    @property
    @overrides(AbstractGenerateOnMachine.
               gen_matrix_params_size_in_bytes)
    def gen_matrix_params_size_in_bytes(self):
        return 12 * BYTES_PER_WORD

    @property
    @overrides(AbstractStaticSynapseDynamics.changes_during_run)
    def changes_during_run(self):
        return False

    @property
    @overrides(AbstractStaticSynapseDynamics.pad_to_length)
    def pad_to_length(self):
        return self.__pad_to_length

    @property
    @overrides(AbstractStaticSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self):
        return True
