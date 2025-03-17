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

from typing import List, Mapping, Optional, Sequence, Tuple, Union
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary

from spinn_front_end_common.interface.ds import DataType

from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertex)
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.models.neural_projections import (
        SynapseInformation)
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex, \
    AbstractPyNNNeuronModel
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractNeuronImpl, AbstractStandardNeuronComponent)
from spynnaker.pyNN.models.neuron.input_types import AbstractInputType
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamics)
from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType
from spynnaker.pyNN.models.neuron.threshold_types import (
    AbstractThresholdType)
from spynnaker.pyNN.models.populations import Population
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType

class MockPopulation(Population):

    def __init__(self, size, label, vertex=None):
        self._size = size
        self._label = label
        self._mock_vertex = vertex
        if vertex is None:
            self._mock_vertex = MockVertex()

    @property
    @overrides(Population.size)
    def size(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return "Population {}".format(self._label)

    @property
    @overrides(Population._vertex)
    def _vertex(self) -> PopulationApplicationVertex:
        return self._mock_vertex


class MockVertex(PopulationApplicationVertex):

    @overrides(PopulationApplicationVertex.get_key_ordered_indices)
    def get_key_ordered_indices(
            self, indices: Optional[NDArray] = None) -> NDArray:
        assert indices is not None
        return indices

    @property
    @overrides(PopulationApplicationVertex.n_colour_bits)
    def n_colour_bits(self) -> int:
        raise NotImplementedError

    @property
    @overrides(PopulationApplicationVertex.n_atoms)
    def n_atoms(self) -> int:
        raise NotImplementedError


class MockNeuronImp(AbstractNeuronImpl):
    @property
    @overrides(AbstractNeuronImpl.model_name)
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @overrides(AbstractNeuronImpl.binary_name)
    def binary_name(self) -> str:
        raise NotImplementedError

    @property
    @overrides(AbstractNeuronImpl.structs)
    def structs(self) -> Sequence[Struct]:
        raise NotImplementedError

    @overrides(AbstractNeuronImpl.get_global_weight_scale)
    def get_global_weight_scale(self) -> float:
        raise NotImplementedError

    @overrides(AbstractNeuronImpl.get_n_synapse_types)
    def get_n_synapse_types(self) -> int:
        raise NotImplementedError

    @overrides(AbstractNeuronImpl.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        raise NotImplementedError

    @overrides(AbstractNeuronImpl.get_synapse_targets)
    def get_synapse_targets(self) -> Sequence[str]:
        raise NotImplementedError

    @overrides(AbstractNeuronImpl.get_recordable_variables)
    def get_recordable_variables(self) -> Sequence[str]:
        return []

    @overrides(AbstractNeuronImpl.get_recordable_units)
    def get_recordable_units(self, variable: str) -> str:
        raise NotImplementedError

    @overrides(AbstractNeuronImpl.get_recordable_data_types)
    def get_recordable_data_types(self) -> Mapping[str, DataType]:
        return {}

    @overrides(AbstractNeuronImpl.is_recordable)
    def is_recordable(self, variable: str) -> bool:
        raise NotImplementedError

    @overrides(AbstractNeuronImpl.get_recordable_variable_index)
    def get_recordable_variable_index(self, variable: str) -> int:
        raise NotImplementedError

    @overrides(AbstractNeuronImpl.add_parameters)
    def add_parameters(self, parameters: RangeDictionary) -> None:
        pass

    @overrides(AbstractNeuronImpl.add_state_variables)
    def add_state_variables(self,
                            state_variables: RangeDictionary) -> None:
        pass

    @overrides(AbstractNeuronImpl.get_units)
    def get_units(self, variable: str) -> str:
        raise NotImplementedError

    @property
    @overrides(AbstractNeuronImpl.is_conductance_based)
    def is_conductance_based(self) -> bool:
        raise NotImplementedError


class MockApvVertex(AbstractPopulationVertex):

    def __init__(
            self, *, n_neurons: int = 1, label: str = "test",
            max_atoms_per_core: Union[int, Tuple[int, ...]] = 255,
            spikes_per_second: Optional[float] = None,
            ring_buffer_sigma: Optional[float] = None,
            max_expected_summed_weight: Optional[List[float]] = None,
            incoming_spike_buffer_size: Optional[int] = None,
            neuron_impl: Optional[AbstractNeuronImpl] = None,
            pynn_model: Optional[AbstractPyNNNeuronModel] = None,
            drop_late_spikes: bool = False,
            splitter: Optional[SplitterAbstractPopulationVertex] = None,
            seed: Optional[int] = None, n_colour_bits: Optional[int] = None,
            extra_partitions: Optional[List[str]] = None):
        if neuron_impl is None:
            if pynn_model is not None:
                neuron_impl = pynn_model._model
            else:
                neuron_impl = MockNeuronImp()
        if pynn_model is None:
            pynn_model = AbstractPyNNNeuronModel(model=neuron_impl)
        super().__init__(
            n_neurons=n_neurons, label=label,
            max_atoms_per_core=max_atoms_per_core,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            max_expected_summed_weight=max_expected_summed_weight,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            neuron_impl=neuron_impl,
            pynn_model=pynn_model, drop_late_spikes=drop_late_spikes,
            splitter=splitter, seed=seed, n_colour_bits=n_colour_bits,
            extra_partitions=extra_partitions)


class MockSynapseDynamics(AbstractSynapseDynamics):

    @overrides(AbstractSynapseDynamics.merge)
    def merge(self, synapse_dynamics: AbstractSynapseDynamics
              ) -> AbstractSynapseDynamics:
        raise NotImplementedError

    @overrides(AbstractSynapseDynamics.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self) -> str:
        raise NotImplementedError

    @property
    @overrides(AbstractSynapseDynamics.changes_during_run)
    def changes_during_run(self) -> bool:
        raise NotImplementedError

    @property
    @overrides(AbstractSynapseDynamics.is_combined_core_capable)
    def is_combined_core_capable(self) -> bool:
        raise NotImplementedError


class MockConnector(AbstractConnector):

    @overrides(AbstractConnector.get_delay_maximum)
    def get_delay_maximum(
            self, synapse_info: SynapseInformation) -> float:
        raise NotImplementedError

    @overrides(AbstractConnector.get_delay_minimum)
    def get_delay_minimum(
            self, synapse_info: SynapseInformation) -> Optional[float]:
        raise NotImplementedError

    @overrides(AbstractConnector.get_n_connections_from_pre_vertex_maximum)
    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms: int, synapse_info: SynapseInformation,
            min_delay: Optional[float] = None,
            max_delay: Optional[float] = None) -> int:
        raise NotImplementedError

    @overrides(AbstractConnector.get_n_connections_to_post_vertex_maximum)
    def get_n_connections_to_post_vertex_maximum(
            self, synapse_info: SynapseInformation) -> int:
        raise NotImplementedError

    @overrides(AbstractConnector.get_weight_maximum)
    def get_weight_maximum(self, synapse_info: SynapseInformation) -> float:
        raise NotImplementedError


class MockNeuronComponent(AbstractStandardNeuronComponent):
    def __init__(self) -> None:
        super().__init__([], {})

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]) -> None:
        pass

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(
            self, state_variables: RangeDictionary[float]) -> None:
        pass


class MockInputType(MockNeuronComponent, AbstractInputType):

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self) -> float:
       raise NotImplementedError


class MockThresholdType(MockNeuronComponent, AbstractThresholdType):
    pass


class MockSynapseType(MockNeuronComponent, AbstractSynapseType):
    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self) -> int:
        raise NotImplementedError
        return 0

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self) -> Sequence[str]:
        raise NotImplementedError
        return []

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        raise NotImplementedError
        return None

