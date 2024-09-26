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
from typing import Iterable, List, Optional, Tuple, TYPE_CHECKING

import numpy
from numpy import floating, integer, uint8, uint16, uint32
from numpy.typing import NDArray

from pyNN.standardmodels.synapses import StaticSynapse

from spinn_utilities.overrides import overrides

from spinn_front_end_common.interface.ds import DataSpecificationBase
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)

from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)
from spynnaker.pyNN.types import Weight_Types
from spynnaker.pyNN.types import Weight_Delay_In_Types as _In_Types
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    NUMPY_CONNECTORS_DTYPE)
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .abstract_generate_on_machine import (
    AbstractGenerateOnMachine, MatrixGeneratorID)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
        ConnectionsArray)
    from spynnaker.pyNN.models.neuron.synapse_io import MaxRowInfo
    from .abstract_synapse_dynamics import AbstractSynapseDynamics

# How large are the time-stamps stored with each event
TIME_STAMP_BYTES = BYTES_PER_WORD

# The targets of neuromodulation
NEUROMODULATION_TARGETS = {
    "reward": 0,
    "punishment": 1
}


class SynapseDynamicsWeightChangable(
        AbstractPlasticSynapseDynamics, AbstractGenerateOnMachine):
    """
    The dynamics of a synapse that can be changed simply by the sending of an
    external signal.
    """

    __slots__ = (

        # The maximum weight
        "__weight_max",

        # The minimum weight
        "__weight_min",

        # The map of synapse information to index
        "__synapse_info_to_index",

        # The next index to use for the next projection
        "__next_index")

    def __init__(
            self,
            weight_min: float, weight_max: float,
            weight: _In_Types = StaticSynapse.default_parameters['weight'],
            delay: _In_Types = None):
        """
        :param float weight:
        :param delay: Use ``None`` to get the simulator default minimum delay.
        :type delay: float or None
        """
        super().__init__(delay=delay, weight=weight)
        self.__weight_max = weight_max
        self.__weight_min = weight_min
        self.__synapse_info_to_index = dict()
        self.__next_index = 0

    @property
    def weight_max(self) -> float:
        """ Get the maximum weight allowed to change to
        """
        return self.__weight_max

    @property
    def weight_min(self) -> float:
        """ Get the minimum weight allowed to change to
        """
        return self.__weight_min

    def get_synapse_info_index(self, synapse_info: SynapseInformation) -> int:
        """ Get the row offset for the given synapse information.  Each synapse
            information has a unique row offset which then allows for multiple
            connections to be identified and kept separate.
        """
        if synapse_info not in self.__synapse_info_to_index:
            self.__synapse_info_to_index[synapse_info] = self.__next_index
            self.__next_index += synapse_info.pre_vertex.n_atoms
        return self.__synapse_info_to_index[synapse_info]

    @overrides(AbstractPlasticSynapseDynamics.merge)
    def merge(self, synapse_dynamics: AbstractSynapseDynamics
              ) -> AbstractSynapseDynamics:
        # If dynamics is a WeightChanger, return ourselves, as
        # WeightChanger can't be used by itself
        # Note: hack required to avoid circular import
        # pylint: disable=import-outside-toplevel
        from .synapse_dynamics_weight_changer import (
            SynapseDynamicsWeightChanger)
        if isinstance(synapse_dynamics, SynapseDynamicsWeightChanger):
            return self

        if not isinstance(synapse_dynamics, SynapseDynamicsWeightChangable):
            raise SynapticConfigurationException(
                "Only a WeightChanger and WeightChangable can be combined")

        if not self.is_same_as(synapse_dynamics):
            raise SynapticConfigurationException(
                "Multiple WeightChangables must have the same min and max")
        return self

    @overrides(AbstractPlasticSynapseDynamics.is_same_as)
    def is_same_as(self, synapse_dynamics: AbstractSynapseDynamics) -> bool:
        if not isinstance(synapse_dynamics, SynapseDynamicsWeightChangable):
            return False
        return (synapse_dynamics.weight_max == self.weight_max and
                synapse_dynamics.weight_min == self.weight_min)

    def get_vertex_executable_suffix(self) -> str:
        """
        :rtype: str
        """
        return "_weight_change"

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        """
        :param int n_neurons:
        :param int n_synapse_types:
        :rtype: int
        """
        # The count of items, plus min and max for each synapse type
        return BYTES_PER_WORD + (BYTES_PER_SHORT * 2 * n_synapse_types)

    @overrides(AbstractPlasticSynapseDynamics.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationBase, region: int,
            global_weight_scale: float,
            synapse_weight_scales: NDArray[floating]):
        spec.comment("Writing Plastic Parameters")

        # Switch focus to the region:
        spec.switch_write_focus(region)

        spec.write_value(len(synapse_weight_scales))
        min_weights = (
            synapse_weight_scales * global_weight_scale *
            self.__weight_min)
        max_weights = (
            synapse_weight_scales * global_weight_scale *
            self.__weight_max)
        weights = numpy.dstack((min_weights, max_weights)).flatten().astype(
            uint16).view(uint32)
        spec.write_array(weights)

    def get_n_words_for_plastic_connections(self, n_connections):
        """
        :param int n_connections:
        :rtype: int
        """
        n_words = n_connections // 2
        if n_connections % 2 != 0:
            n_words += 1
        # plastic-plastic has 1 header and then a half-word-weight per
        # connection
        # fixed-plastic has a half-word per connection for the other elements
        return 1 + n_words * 2

    @overrides(AbstractPlasticSynapseDynamics.get_plastic_synaptic_data)
    def get_plastic_synaptic_data(
            self, connections: ConnectionsArray,
            connection_row_indices: NDArray[integer], n_rows: int,
            n_synapse_types: int,
            max_n_synapses: int, max_atoms_per_core: int) -> Tuple[
                List[NDArray[uint32]], List[NDArray[uint32]],
                NDArray[uint32], NDArray[uint32]]:
        n_synapse_type_bits = get_n_bits(n_synapse_types)
        n_neuron_id_bits = get_n_bits(max_atoms_per_core)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1

        # Get the fixed data
        fixed_plastic = (
            (connections["delay"].astype(uint16) <<
             (n_neuron_id_bits + n_synapse_type_bits)) |
            (connections["synapse_type"].astype(uint16) << n_neuron_id_bits) |
            (connections["target"].astype(uint16) & neuron_id_mask))
        fixed_plastic_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_plastic.view(dtype=uint8).reshape((-1, 2)),
            max_n_synapses)
        fp_size = self.get_n_items(fixed_plastic_rows, BYTES_PER_SHORT)
        fp_data = self.get_words(fixed_plastic_rows)

        # Convert the plastic data into groups of bytes per connection and
        # then into rows
        plastic_plastic = numpy.rint(
            numpy.abs(connections["weight"])).astype(uint16)
        plastic_plastic_bytes = plastic_plastic.view(dtype=uint8).reshape(
            (-1, BYTES_PER_SHORT))
        plastic_plastic_row_data = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows, plastic_plastic_bytes,
            max_n_synapses)
        # TODO: Get the synapse info index and add to the row offset
        # row_offset = self.get_synapse_info_index(synapse_info)
        plastic_headers = numpy.arange(n_rows, dtype=uint32).view(
            uint8).reshape((-1, BYTES_PER_WORD))
        plastic_plastic_rows = [
            numpy.concatenate((
                plastic_headers[i], plastic_plastic_row_data[i]))
            for i in range(n_rows)]
        pp_size = self.get_n_items(plastic_plastic_rows, BYTES_PER_WORD)
        pp_data = self.get_words(plastic_plastic_rows)

        return fp_data, pp_data, fp_size, pp_size

    @overrides(
        AbstractPlasticSynapseDynamics.get_n_plastic_plastic_words_per_row)
    def get_n_plastic_plastic_words_per_row(
            self, pp_size: NDArray[uint32]) -> NDArray[integer]:
        # pp_size is in words, so return
        return pp_size

    @overrides(
        AbstractPlasticSynapseDynamics.get_n_fixed_plastic_words_per_row)
    def get_n_fixed_plastic_words_per_row(
            self, fp_size: NDArray[uint32]) -> NDArray[integer]:
        # fp_size is in half-words
        return numpy.ceil(fp_size / 2.0).astype(dtype=uint32)

    @overrides(AbstractPlasticSynapseDynamics.get_n_synapses_in_rows)
    def get_n_synapses_in_rows(self, pp_size: NDArray[uint32],
                               fp_size: NDArray[uint32]) -> NDArray[integer]:
        # Each fixed-plastic synapse is a half-word and fp_size is in half
        # words so just return it
        return fp_size

    @overrides(AbstractPlasticSynapseDynamics.read_plastic_synaptic_data)
    def read_plastic_synaptic_data(
            self, n_synapse_types: int, pp_size: NDArray[uint32],
            pp_data: List[NDArray[uint32]], fp_size: NDArray[uint32],
            fp_data: List[NDArray[uint32]],
            max_atoms_per_core: int) -> ConnectionsArray:
        # pylint: disable=too-many-arguments
        n_rows = len(fp_size)

        n_synapse_type_bits = get_n_bits(n_synapse_types)
        n_neuron_id_bits = get_n_bits(max_atoms_per_core)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1

        data_fixed = numpy.concatenate([
            fp_data[i].view(dtype=uint16)[0:fp_size[i]]
            for i in range(n_rows)])
        pp_without_headers = [
            row.view(dtype=uint8)[BYTES_PER_WORD:] for row in pp_data]
        pp_half_words = numpy.concatenate(
            [pp[:size * BYTES_PER_SHORT]
             for pp, size in zip(pp_without_headers, fp_size)]).view(uint16)

        connections = numpy.zeros(
            data_fixed.size, dtype=NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate(
            [numpy.repeat(i, fp_size[i]) for i in range(len(fp_size))])
        connections["target"] = data_fixed & neuron_id_mask
        connections["weight"] = pp_half_words
        connections["delay"] = data_fixed >> (
            n_neuron_id_bits + n_synapse_type_bits)
        return connections

    @overrides(AbstractPlasticSynapseDynamics.get_weight_mean)
    def get_weight_mean(self, connector: AbstractConnector,
                        synapse_info: SynapseInformation) -> float:
        # Because the weights could all be changed to the maximum, the mean
        # has to be given as the maximum for scaling
        return self.get_weight_maximum(connector, synapse_info)

    @overrides(AbstractPlasticSynapseDynamics.get_weight_variance)
    def get_weight_variance(
           self, connector: AbstractConnector, weights: Weight_Types,
            synapse_info: SynapseInformation) -> float:
        # Because the weights could all be changed to the maximum, the variance
        # has to be given as no variance
        return 0.0

    @overrides(AbstractPlasticSynapseDynamics.get_weight_maximum)
    def get_weight_maximum(self, connector: AbstractConnector,
                           synapse_info: SynapseInformation) -> float:
        return self.__weight_max

    @overrides(AbstractPlasticSynapseDynamics.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        yield 'weight'
        yield 'delay'

    @overrides(AbstractPlasticSynapseDynamics.get_max_synapses)
    def get_max_synapses(self, n_words: int) -> int:
        # Subtract the header size that will always exist
        n_words_space = n_words - BYTES_PER_WORD

        # The remaining space is divided equally into plastic plastic and fixed
        # plastic, but these have to be word aligned, so e.g. 5 words space
        # would be 2.5 words per section, which allows for 5 connections in
        # theory, but 5 connections would require word alignment at 3 words per
        # section, so we round down instead and get 4 connections
        return 2 * (n_words_space // 2)

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_id)
    def gen_matrix_id(self) -> int:
        # We can use the STDP generation routine, with the addition that
        # each row header has the pre-neuron-id in it (i.e. the row number)
        return MatrixGeneratorID.STDP_MATRIX.value

    @overrides(AbstractGenerateOnMachine.gen_matrix_params)
    def gen_matrix_params(
            self, synaptic_matrix_offset: int, delayed_matrix_offset: int,
            app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation, max_row_info: MaxRowInfo,
            max_pre_atoms_per_core: int, max_post_atoms_per_core: int
            ) -> NDArray[uint32]:
        vertex = app_edge.post_vertex
        n_synapse_type_bits = get_n_bits(
            vertex.neuron_impl.get_n_synapse_types())
        n_synapse_index_bits = get_n_bits(max_post_atoms_per_core)
        max_delay = app_edge.post_vertex.splitter.max_support_delay()
        max_delay_bits = get_n_bits(max_delay)
        half_word = 0
        n_half_words = 1
        header_half_words = 2
        write_row_number_to_header = 1
        # We need to use the "global" dynamics object to get the offset
        dynamics = app_edge.post_vertex.synapse_dynamics
        row_offset = dynamics.get_synapse_info_index(synapse_info)
        return numpy.array([
            synaptic_matrix_offset, delayed_matrix_offset,
            max_row_info.undelayed_max_n_synapses,
            max_row_info.delayed_max_n_synapses,
            max_row_info.undelayed_max_words, max_row_info.delayed_max_words,
            synapse_info.synapse_type, n_synapse_type_bits,
            n_synapse_index_bits, app_edge.n_delay_stages + 1,
            max_delay, max_delay_bits, app_edge.pre_vertex.n_atoms,
            max_pre_atoms_per_core, header_half_words,
            n_half_words, half_word, write_row_number_to_header, row_offset],
            dtype=uint32)

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_params_size_in_bytes)
    def gen_matrix_params_size_in_bytes(self) -> int:
        return 19 * BYTES_PER_WORD

    @property
    @overrides(AbstractPlasticSynapseDynamics.changes_during_run)
    def changes_during_run(self) -> bool:
        return True

    @property
    @overrides(AbstractPlasticSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self) -> bool:
        return True

    @property
    @overrides(AbstractPlasticSynapseDynamics.pad_to_length)
    def pad_to_length(self) -> Optional[int]:
        return None
