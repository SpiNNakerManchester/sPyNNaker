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
import logging
from typing import Any, cast, Optional, Sequence, Tuple, Set, TYPE_CHECKING

import numpy

from pyNN.random import RandomDistribution

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.log import FormatAdapter

from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import MachineVertex

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.types import (
    Delays, WeightsDelysIn, Weights)
from spynnaker.pyNN.utilities.constants import POP_TABLE_MAX_ROW_LENGTH
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    NUMPY_CONNECTORS_DTYPE as CONNECTOR_DTYPE)
from spynnaker.pyNN.types import is_scalar

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections.connectors import (
        AbstractConnector)
    from spynnaker.pyNN.models.neural_projections import SynapseInformation
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge)

logger = FormatAdapter(logging.getLogger(__name__))


class AbstractSynapseDynamics(object, metaclass=AbstractBase):
    """
    How do the dynamics of a synapse interact with the rest of the model.
    """

    __slots__ = ("__delay", "__weight")

    def __init__(self, delay: WeightsDelysIn,
                 weight: WeightsDelysIn):
        """
        :param delay: The delay or a way of generating the delays
        :param weight: The weights or way to generate the weights
        """
        self.__check_in_type(delay, "delay")
        self.__delay = self._round_delay(delay)
        self.__check_out_delay(self.__delay, "delay")
        self.__check_in_type(weight, "weight")
        self.__weight = self._convert_weight(weight)
        self.__check_out_weight(self.__weight, "weight")

    def __check_in_type(self, value: WeightsDelysIn, name: str) -> None:
        if value is None:
            return
        if isinstance(value, (int, float, str, RandomDistribution)):
            return
        try:
            for x in value:
                if not isinstance(x, (int, numpy.integer, float)):
                    raise TypeError(
                        f"Unexpected collection of type  {type(x)} for {name}"
                        f"Expected types in collection are int and float")
            return
        except TypeError:
            # OK not a collection
            pass
        raise TypeError(
            f"Unexpected type for {name}: {type(value)}. "
            "Expected types are int, float, str, RandomDistribution "
            "and collections of type int or float")

    def __check_out_weight(self, weight: Weights, name: str) -> None:
        if weight is None:
            return
        if isinstance(weight, (int, float, str, RandomDistribution)):
            return
        if isinstance(weight, numpy.ndarray):
            for x in weight:
                if not isinstance(x, (numpy.float64)):
                    raise TypeError(
                        f"Unexpected numpy ndarray of type {type(x)}"
                        f" for {name}")
            return
        raise TypeError(
            f"Unexpected type for output data: {type(weight)} for {name} "
            "Expected types are float, str, RandomDistribution "
            "and list of type float")

    def __check_out_delay(self, delay: Delays, name: str) -> None:
        if isinstance(delay, (float, (str, RandomDistribution))):
            return
        if isinstance(delay, numpy.ndarray):
            for x in delay:
                if not isinstance(x, (numpy.float64)):
                    raise TypeError(
                        f"Unexpected numpy ndarray of type {type(x)}"
                        f" for {name}")
            return
        raise TypeError(
            f"Unexpected type for output data: {type(delay)} for {name} "
            "Expected types are float, str, RandomDistribution "
            "and list of type float")

    #: Type model of the basic configuration data of a connector
    NUMPY_CONNECTORS_DTYPE = CONNECTOR_DTYPE

    @abstractmethod
    def merge(self, synapse_dynamics: AbstractSynapseDynamics
              ) -> AbstractSynapseDynamics:
        """
        Merge with the given synapse_dynamics and return the result, or
        error if merge is not possible.

        :param synapse_dynamics:
        :returns: A merge of this and the given synapse_dynamics
        """
        raise NotImplementedError

    @abstractmethod
    def get_vertex_executable_suffix(self) -> str:
        """
        :returns: The executable suffix for a vertex for this dynamics.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def changes_during_run(self) -> bool:
        """
        Whether the synapses change during a run.
        """
        raise NotImplementedError

    @property
    def weight(self) -> Weights:
        """
        The weight of connections.
        """
        return self.__weight

    def _round_delay(self, delay: WeightsDelysIn) -> Delays:
        """
        Round the delays to multiples of full timesteps.

        (otherwise SDRAM estimation calculations can go wrong)

        :param delay:
        :return: Rounded delay
        """
        if isinstance(delay, (RandomDistribution, str)):
            return delay
        if delay is None:
            delay = SpynnakerDataView.get_min_delay()
        # Note the cast is just to say trust use the delay will work
        # If not numpy will raise an exception
        new_delay = (
                numpy.rint(numpy.array(cast(float, delay)) *
                           SpynnakerDataView.get_simulation_time_step_per_ms())
                * SpynnakerDataView.get_simulation_time_step_ms())
        if not numpy.allclose(cast(float, delay), new_delay):
            logger.warning("Rounding up delay in f{} from {} to {}",
                           self, delay, new_delay)
        if isinstance(new_delay, numpy.float64):
            return float(new_delay)
        if isinstance(new_delay, numpy.ndarray):
            return new_delay
        raise TypeError(f"{type(delay)=}")

    def _convert_weight(self, weight: WeightsDelysIn) -> Weights:
        """
        Convert the weights if numerical to (list of) float .

        :param weight:
        :return: weight as float (if numerical)
        """
        if weight is None:
            return weight
        if isinstance(weight, (RandomDistribution, str)):
            return weight
        if isinstance(weight, int):
            return weight
        if is_scalar(weight):
            return float(weight)
        new_weight = numpy.array(weight, dtype=float)
        return new_weight

    @property
    def delay(self) -> Delays:
        """
        The delay of connections.
        """
        return self.__delay

    @property
    @abstractmethod
    def is_combined_core_capable(self) -> bool:
        """
        Whether the synapse dynamics can run on a core combined with
        the neuron, or if a separate core is needed.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def is_split_core_capable(self) -> bool:
        """
        Whether the synapse dynamics can run on a core split from
        the neuron, or if only a combined core is possible.
        """
        raise NotImplementedError

    def get_synapse_parameter_names(self) -> Set[str]:
        """
        :return: the names of the parameters that can be extracted from
         synapses read from the machine.
        """
        return {"source", "target", "weight", "delay"}

    def get_value(self, key: str) -> Any:
        """
        Get a property.

        :param key: the name of the property
        :returns: Value for this key
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise InvalidParameterType(
            f"Type {type(self)} does not have parameter {key}")

    def set_value(self, key: str, value: Any) -> None:
        """
        Set a property.

        :param key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        """
        if hasattr(self, key):
            setattr(self, key, value)
            SpynnakerDataView.set_requires_mapping()
        else:
            raise InvalidParameterType(
                f"Type {type(self)} does not have parameter {key}")

    def get_delay_maximum(
            self, connector: AbstractConnector,
            synapse_info: SynapseInformation) -> float:
        """
        :returns: The maximum delay for the synapses.
        """
        return connector.get_delay_maximum(synapse_info)

    def get_delay_minimum(
            self, connector: AbstractConnector,
            synapse_info: SynapseInformation) -> Optional[float]:
        """
        Get the minimum delay for the synapses.

        This will support the filtering of the undelayed edge
        from the graph, but requires fixes in the synaptic manager to
        happen first before this can be utilised fully.

        :param connector: connector
        :param synapse_info: synapse info
        :returns: The minimum delay
        """
        return connector.get_delay_minimum(synapse_info)

    def get_delay_variance(
            self, connector: AbstractConnector, delays: Delays,
            synapse_info: SynapseInformation) -> float:
        """
        :param connector:
        :param delays:
        :param synapse_info:
        :returns: The variance in delay for the synapses.
        """
        return connector.get_delay_variance(delays, synapse_info)

    def get_weight_mean(
            self, connector: AbstractConnector,
            synapse_info: SynapseInformation) -> float:
        """
        :param connector:
        :param synapse_info:
        :returns: The mean weight for the synapses.
        """
        return connector.get_weight_mean(synapse_info.weights, synapse_info)

    def get_weight_maximum(
            self, connector: AbstractConnector,
            synapse_info: SynapseInformation) -> float:
        """
        :param connector:
        :param synapse_info:
        :returns: The maximum weight for the synapses.
        """
        return connector.get_weight_maximum(synapse_info)

    def get_weight_variance(
           self, connector: AbstractConnector, weights: Weights,
            synapse_info: SynapseInformation) -> float:
        """
        :param connector:
        :param weights:
        :param synapse_info:
        :returns: The variance in weight for the synapses.
        """
        return connector.get_weight_variance(weights, synapse_info)

    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        """
        :param target: The name of the synapse
        :returns: The index of the synapse type based on the name,
            or `None` if the name is not found.
        """
        _ = target
        return None

    def get_connected_vertices(
            self, s_info: SynapseInformation,
            source_vertex: ApplicationVertex,
            target_vertex: ApplicationVertex) -> Sequence[
                Tuple[MachineVertex, Sequence[AbstractVertex]]]:
        """
        Get the machine vertices that are connected to each other with
        this connector.

        :param s_info: The synapse information of the connection
        :param source_vertex: The source of the spikes
        :param target_vertex: The target of the spikes
        :return: A list of tuples of (target machine vertex, list of sources)
        """
        # By default, just ask the connector
        return s_info.connector.get_connected_vertices(
            s_info, source_vertex, target_vertex)

    @property
    def absolute_max_atoms_per_core(self) -> int:
        """
        The absolute maximum number of atoms per core supported by this
        synapse dynamics object.
        """
        # By default, we can only support the maximum row length per core
        return POP_TABLE_MAX_ROW_LENGTH

    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> None:
        """
        Checks that the edge supports the connector.  Returns nothing; it
        is assumed that an Exception will be raised if anything is wrong.

        By default this checks only that the views are not used
        on multi-dimensional vertices.

        :param application_edge: The edge of the connection
        :param synapse_info: The synaptic information
        """
        # By default, just ask the connector
        synapse_info.connector.validate_connection(
            application_edge, synapse_info)

    @property
    @abstractmethod
    def synapses_per_second(self) -> int:
        """
        Approximate number of synapses that can be processed per second;
        ideally as close to the truth as possible, but underestimate would
        be OK.  Overestimation would potentially mean having to handle more
        spikes than is possible, so overruns would occur.
        """
        raise NotImplementedError
