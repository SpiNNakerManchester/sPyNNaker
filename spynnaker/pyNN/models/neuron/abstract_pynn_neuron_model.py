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
from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union, Tuple
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron import PopulationVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.utilities.constants import POP_TABLE_MAX_ROW_LENGTH
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.implementations import AbstractNeuronImpl
    from spynnaker.pyNN.extra_algorithms.splitter_components import (
        SplitterPopulationVertex)

# The maximum atoms per core is the master population table row length to
# make it easier when all-to-all-connector is used
DEFAULT_MAX_ATOMS_PER_CORE = POP_TABLE_MAX_ROW_LENGTH

_population_parameters: Dict[str, Any] = {
    "spikes_per_second": None, "ring_buffer_sigma": None,
    "max_expected_summed_weight": None,
    "incoming_spike_buffer_size": None, "drop_late_spikes": None,
    "splitter": None, "seed": None, "n_colour_bits": None,
    "n_synapse_cores": None, "allow_delay_extensions": None,
    "neurons_per_core": None,
}


class AbstractPyNNNeuronModel(AbstractPyNNModel):
    """
    API for a PyNN Neuron Model
    """
    __slots__ = ("__model", )

    # The number of synapse cores for PyNN models that use PopulationVertex
    # or None to determine based on time-step
    _n_synapse_cores: Dict[type, Optional[int]] = {}

    # Whether to allow delay extensions when using PyNN models that use
    # PopulationVertex
    _allow_delay_extensions: Dict[type, bool] = {}

    #: Population parameters for neuron models.
    default_population_parameters = _population_parameters

    @classmethod
    def set_model_n_synapse_cores(cls, n_synapse_cores: Optional[int]) -> None:
        """
        Set the number of synapse cores for a model.

        :param n_synapse_cores:
            The number of synapse cores; 0 to force combined cores, and None to
            allow the system to choose
        """
        cls.verify_may_set(param="n_synapse_cores")
        cls._n_synapse_cores[cls] = n_synapse_cores

    @classmethod
    def get_model_n_synapse_cores(cls) -> Optional[int]:
        """
        :returns: The number of synapse cores for the model.
        """
        return cls._n_synapse_cores.get(cls, None)

    @classmethod
    def set_model_allow_delay_extensions(cls, allow: bool) -> None:
        """
        Set whether to allow delay extensions for a model.

        :param allow: Whether to allow delay extensions
        """
        cls.verify_may_set(param="allow_delay_extensions")
        cls._allow_delay_extensions[cls] = allow

    @classmethod
    def get_model_allow_delay_extensions(cls) -> bool:
        """
        Get whether to allow delay extensions for the model.

        :returns: True unless the model does not allow delay extensions
        """
        return cls._allow_delay_extensions.get(cls, True)

    @classmethod
    @overrides(AbstractPyNNModel.reset_all)
    def reset_all(cls) -> None:
        super().reset_all()
        AbstractPyNNNeuronModel._n_synapse_cores.clear()
        AbstractPyNNNeuronModel._allow_delay_extensions.clear()

    def __init__(self, model: AbstractNeuronImpl):
        """
        :param model: The model implementation
        """
        self.__model = model

    @property
    def _model(self) -> AbstractNeuronImpl:
        return self.__model

    @overrides(AbstractPyNNModel.create_vertex)
    def create_vertex(
            self, n_neurons: int, label: str, *,
            spikes_per_second: Optional[float] = None,
            ring_buffer_sigma: Optional[float] = None,
            max_expected_summed_weight: Optional[List[float]] = None,
            incoming_spike_buffer_size: Optional[int] = None,
            drop_late_spikes: Optional[bool] = None,
            splitter: Optional[SplitterPopulationVertex] = None,
            seed: Optional[int] = None,
            n_colour_bits: Optional[int] = None,
            neurons_per_core: Optional[Union[int, Tuple[int, ...]]] = None,
            n_synapse_cores: Optional[int] = None,
            allow_delay_extensions: Optional[bool] = None) -> PopulationVertex:
        """
        :param spikes_per_second:
        :param ring_buffer_sigma:
        :param incoming_spike_buffer_size:
        :param drop_late_spikes:
        :param splitter:
        :param seed:
        :param n_colour_bits:
        """
        if neurons_per_core is None:
            neurons_per_core = \
                self.get_model_max_atoms_per_dimension_per_core()
        if n_synapse_cores is None:
            n_synapse_cores = self.get_model_n_synapse_cores()
        if allow_delay_extensions is None:
            allow_delay_extensions = self.get_model_allow_delay_extensions()
        return PopulationVertex(
            n_neurons=n_neurons, label=label,
            max_atoms_per_core=neurons_per_core,
            n_synapse_cores=n_synapse_cores,
            allow_delay_extensions=allow_delay_extensions,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            max_expected_summed_weight=max_expected_summed_weight,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            neuron_impl=self.__model, pynn_model=self,
            drop_late_spikes=drop_late_spikes or False,
            splitter=splitter, seed=seed, n_colour_bits=n_colour_bits)

    @property
    @overrides(AbstractPyNNModel.name)
    def name(self) -> str:
        return self.__model.model_name
