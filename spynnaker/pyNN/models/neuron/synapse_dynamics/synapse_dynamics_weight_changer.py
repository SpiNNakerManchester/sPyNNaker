# Copyright (c) 2021 The University of Manchester
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
from typing import Iterable, List, Optional, Tuple, TYPE_CHECKING, cast

import numpy
from numpy import floating, integer, uint8, uint32, int16
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides
from pacman.utilities.utility_calls import get_n_bits

from spinn_front_end_common.interface.ds import DataSpecificationBase
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.exceptions import (
    SynapticConfigurationException, InvalidParameterType)
from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    NUMPY_CONNECTORS_DTYPE)
from .abstract_plastic_synapse_dynamics import AbstractPlasticSynapseDynamics
from .abstract_generate_on_machine import AbstractGenerateOnMachine
from .abstract_generate_on_machine import MatrixGeneratorID
from .synapse_dynamics_weight_changable import SynapseDynamicsWeightChangable

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)
    from spynnaker.pyNN.models.neuron.synapse_io import MaxRowInfo
    from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
        ConnectionsArray)
    from spynnaker.pyNN.models.neural_projections.connectors import (
        AbstractConnector)
    from spynnaker.pyNN.types import Weight_Types
    from spynnaker.pyNN.models.projection import Projection
    from .abstract_synapse_dynamics import AbstractSynapseDynamics


class SynapseDynamicsWeightChanger(
        AbstractPlasticSynapseDynamics, AbstractGenerateOnMachine):
    """
    Synapses that target a weight change
    """

    __slots__ = ["__post_vertex", "__synapse_info"]

    def __init__(self, weight_change: float, projection: Projection):
        """
        :param float weight_change:
            The positive or negative change in weight to apply on each spike
        :param Projection projection:
            The projection that this synapse dynamics is being added to
        """
        super().__init__(delay=1, weight=weight_change)
        # pylint: disable=protected-access
        self.__synapse_info = projection._synapse_information
        if not isinstance(self.__synapse_info.synapse_dynamics,
                          SynapseDynamicsWeightChangable):
            raise SynapticConfigurationException(
                "A changer can only affect a changeable projection")
        # Note: we store the post vertex here rather than the dynamics, as the
        # dynamics can change over time
        # Import here required to avoid circular imports
        # pylint: disable=import-outside-toplevel
        from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
        self.__post_vertex = cast(AbstractPopulationVertex,
                                  self.__synapse_info.post_vertex)

    @overrides(AbstractPlasticSynapseDynamics.merge)
    def merge(self, synapse_dynamics: AbstractSynapseDynamics
              ) -> AbstractSynapseDynamics:
        # This must replace something that supports weight change,
        # so it can't be the first thing to be merged!
        raise SynapticConfigurationException(
            "Weight Changer synapses can only be added where an existing"
            " projection has already been added which supports"
            " weight changes")

    @overrides(AbstractPlasticSynapseDynamics.is_same_as)
    def is_same_as(self, synapse_dynamics: AbstractSynapseDynamics) -> bool:
        # Shouldn't ever come up, but if it does, it is False!
        return False

    @overrides(AbstractPlasticSynapseDynamics.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self) -> str:
        return "_weight_change"

    @overrides(AbstractPlasticSynapseDynamics
               .get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_neurons: int, n_synapse_types: int) -> int:
        # Should never be asked!
        return 0

    @overrides(AbstractPlasticSynapseDynamics.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationBase, region: int,
            global_weight_scale: float,
            synapse_weight_scales: NDArray[floating]):
        # Should never be asked!
        pass

    @overrides(AbstractPlasticSynapseDynamics.get_value)
    def get_value(self, key: str) -> float:
        if hasattr(self, key):
            return getattr(self, key)
        raise InvalidParameterType(
            f"Type {type(self)} does not have parameter {key}")

    @overrides(AbstractPlasticSynapseDynamics.set_value)
    def set_value(self, key: str, value: float):
        if hasattr(self, key):
            setattr(self, key, value)
        raise InvalidParameterType(
            f"Type {type(self)} does not have parameter {key}")

    @overrides(AbstractPlasticSynapseDynamics
               .get_n_words_for_plastic_connections)
    def get_n_words_for_plastic_connections(self, n_connections: int) -> int:
        # 1 for flag and pre-spike identifier
        pp_size_words = 1
        # 1 for each connection
        fp_size_words = n_connections
        return pp_size_words + fp_size_words

    @overrides(AbstractPlasticSynapseDynamics.get_plastic_synaptic_data)
    def get_plastic_synaptic_data(
            self, connections: ConnectionsArray,
            connection_row_indices: NDArray[integer], n_rows: int,
            n_synapse_types: int,
            max_n_synapses: int, max_atoms_per_core: int) -> Tuple[
                NDArray[uint32], NDArray[uint32], NDArray[uint32],
                NDArray[uint32]]:
        # pylint: disable=too-many-arguments
        weights = numpy.rint(numpy.abs(connections["weight"]))
        n_neuron_id_bits = get_n_bits(max_atoms_per_core)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1
        fixed_plastic = (
            ((weights.astype(uint32) & 0xFFFF) << 16) |
            (connections["synapse_type"].astype(uint32) << n_neuron_id_bits) |
            (connections["target"] & neuron_id_mask))
        fixed_plastic_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_plastic.view(dtype=uint8).reshape((-1, BYTES_PER_WORD)),
            max_n_synapses)

        flags = 0x80000000 | numpy.arange(n_rows, dtype=uint32)

        fp_size = self.get_n_items(fixed_plastic_rows, BYTES_PER_WORD)
        fp_data = numpy.vstack([
            fixed_row.view(uint32) for fixed_row in fixed_plastic_rows])
        pp_data = flags.astype(uint32)
        pp_size = numpy.ones(n_rows, dtype=uint32)

        return fp_data, pp_data, fp_size, pp_size

    @overrides(
        AbstractPlasticSynapseDynamics.get_n_plastic_plastic_words_per_row)
    def get_n_plastic_plastic_words_per_row(
            self, pp_size: NDArray[integer]) -> NDArray[integer]:
        # pp_size is in words, so just return
        return pp_size

    @overrides(
        AbstractPlasticSynapseDynamics.get_n_fixed_plastic_words_per_row)
    def get_n_fixed_plastic_words_per_row(
            self, fp_size: NDArray[integer]) -> NDArray[integer]:
        # fp_size is in words, so just return
        return fp_size

    @overrides(AbstractPlasticSynapseDynamics.get_n_synapses_in_rows)
    def get_n_synapses_in_rows(
            self, pp_size: NDArray[integer],
            fp_size: NDArray[integer]) -> NDArray[integer]:
        # Each fixed-plastic synapse is a word and fp_size is in words so just
        # return it
        return fp_size

    @overrides(AbstractPlasticSynapseDynamics.read_plastic_synaptic_data)
    def read_plastic_synaptic_data(
            self, n_synapse_types: int,
            pp_size: NDArray[uint32], pp_data: List[NDArray[uint32]],
            fp_size: NDArray[uint32], fp_data: List[NDArray[uint32]],
            max_atoms_per_core: int) -> ConnectionsArray:
        data = numpy.concatenate(fp_data)
        weight = ((data >> 16) & 0xFFFF).astype(int16)
        n_neuron_id_bits = get_n_bits(max_atoms_per_core)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1
        connections = numpy.zeros(data.size, dtype=NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate(
            [numpy.repeat(i, fp_size[i]) for i in range(len(fp_size))])
        connections["target"] = data & neuron_id_mask
        connections["weight"] = weight
        connections["delay"] = 1
        return connections

    @overrides(AbstractPlasticSynapseDynamics.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        yield 'weight'

    @overrides(AbstractPlasticSynapseDynamics.get_max_synapses)
    def get_max_synapses(self, n_words: int) -> int:
        # One word is static, the rest is for synapses
        return n_words - 1

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_id)
    def gen_matrix_id(self) -> int:
        return MatrixGeneratorID.CHANGE_WEIGHT_MATRIX.value

    @overrides(AbstractGenerateOnMachine.gen_matrix_params)
    def gen_matrix_params(
            self, synaptic_matrix_offset: int, delayed_matrix_offset: int,
            app_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation, max_row_info: MaxRowInfo,
            max_pre_atoms_per_core: int,
            max_post_atoms_per_core: int) -> NDArray[uint32]:
        # pylint: disable=unused-argument
        vertex = app_edge.post_vertex
        n_synapse_type_bits = get_n_bits(
            vertex.neuron_impl.get_n_synapse_types())
        n_synapse_index_bits = get_n_bits(max_post_atoms_per_core)
        # We need to use the "global" dynamics object to get the offset
        dynamics = cast(SynapseDynamicsWeightChangable,
                        app_edge.post_vertex.synapse_dynamics)
        row_offset = dynamics.get_synapse_info_index(self.__synapse_info)
        return numpy.array([
            synaptic_matrix_offset, max_row_info.undelayed_max_words,
            max_row_info.undelayed_max_n_synapses,
            app_edge.pre_vertex.n_atoms, self.__synapse_info.synapse_type,
            n_synapse_type_bits, n_synapse_index_bits, row_offset],
            dtype=uint32)

    @property
    @overrides(AbstractGenerateOnMachine.
               gen_matrix_params_size_in_bytes)
    def gen_matrix_params_size_in_bytes(self) -> int:
        return 8 * BYTES_PER_WORD

    @property
    @overrides(AbstractPlasticSynapseDynamics.changes_during_run)
    def changes_during_run(self) -> bool:
        return False

    @property
    @overrides(AbstractPlasticSynapseDynamics.pad_to_length)
    def pad_to_length(self) -> None:
        return None

    @overrides(AbstractPlasticSynapseDynamics.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        return 0

    @property
    @overrides(AbstractPlasticSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self) -> bool:
        return True

    @overrides(AbstractPlasticSynapseDynamics.get_weight_maximum)
    def get_weight_maximum(
            self, connector: AbstractConnector,
            synapse_info: SynapseInformation) -> float:
        return self.__post_vertex.synapse_dynamics.get_weight_maximum(
            self.__synapse_info.connector, self.__synapse_info)

    @overrides(AbstractPlasticSynapseDynamics.get_weight_mean)
    def get_weight_mean(
            self, connector: AbstractConnector,
            synapse_info: SynapseInformation) -> float:
        return self.get_weight_maximum(connector, synapse_info)

    @overrides(AbstractPlasticSynapseDynamics.get_weight_variance)
    def get_weight_variance(
            self, connector: AbstractConnector, weights: Weight_Types,
            synapse_info: SynapseInformation) -> float:
        return 0.0

    @overrides(AbstractPlasticSynapseDynamics.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation):
        if (application_edge.pre_vertex.n_atoms !=
                self.__synapse_info.pre_vertex.n_atoms):
            raise SynapticConfigurationException(
                "The pre-Population of this projection must have the same"
                " number of atoms as the pre-Population of the projection"
                " whose weights are to be changed")
        if application_edge.post_vertex != self.__synapse_info.post_vertex:
            raise SynapticConfigurationException(
                "The post-Population of this projection must be the same as"
                " the post-Population of the projection whose weights are to"
                " be changed")
        if synapse_info.synapse_type != self.__synapse_info.synapse_type:
            raise SynapticConfigurationException(
                "The synapse type of the projection must be the same as the"
                " synapse type of the projection whose weights are to be"
                " changed")
        AbstractPlasticSynapseDynamics.validate_connection(
            self, application_edge, synapse_info)
