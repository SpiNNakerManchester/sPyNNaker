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
from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import numpy
from numpy import uint32
from numpy.typing import NDArray

from pyNN.random import RandomDistribution

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.overrides import overrides

from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.common.param_generator_data import (
    param_generator_params, param_generator_params_size_in_bytes,
    param_generator_id, is_param_generatable)
from spynnaker.pyNN.types import (DELAYS, WEIGHTS)
from spynnaker.pyNN.utilities.utility_calls import check_rng

from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import (
        ProjectionApplicationEdge, SynapseInformation)


class ConnectorIDs(Enum):
    """
    Hashes of the connection generators supported by the synapse expander
    """
    ONE_TO_ONE_CONNECTOR = 0
    ALL_TO_ALL_CONNECTOR = 1
    FIXED_PROBABILITY_CONNECTOR = 2
    FIXED_TOTAL_NUMBER_CONNECTOR = 3
    FIXED_NUMBER_PRE_CONNECTOR = 4
    FIXED_NUMBER_POST_CONNECTOR = 5
    KERNEL_CONNECTOR = 6
    ALL_BUT_ME_CONNECTOR = 7
    ONE_TO_ONE_OFFSET_CONNECTOR = 8


class AbstractGenerateConnectorOnMachine(
        AbstractConnector, metaclass=AbstractBase):
    """
    Indicates that the connectivity can be generated on the machine.
    """

    __slots__ = ()

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ProjectionApplicationEdge,
            synapse_info: SynapseInformation) -> None:
        # If we can't generate on machine, we must be able to generate on host
        if not self.generate_on_machine(synapse_info):
            if not isinstance(self, AbstractGenerateConnectorOnHost):
                raise SynapticConfigurationException(
                    "The parameters of this connection do not allow it to be"
                    " generated on the machine, but the connector cannot"
                    " be generated on host!")

    def generate_on_machine(self, synapse_info: SynapseInformation) -> bool:
        """
        Determine if this instance can generate on the machine.

        Default implementation returns True if the weights and delays can
        be generated on the machine

        :param synapse_info: The synapse information
        """
        if (not is_param_generatable(synapse_info.weights) or
                not is_param_generatable(synapse_info.delays)):
            return False
        if isinstance(synapse_info.weights, RandomDistribution):
            check_rng(synapse_info.weights.rng, "RandomDistribution in weight")
        if isinstance(synapse_info.delays, RandomDistribution):
            check_rng(synapse_info.delays.rng, "RandomDistribution in delay")
        return True

    def gen_weights_id(self, weights: WEIGHTS) -> int:
        """
        Get the id of the weight generator on the machine.

        :param weights:
        """
        return param_generator_id(weights)

    def gen_weights_params(self, weights: WEIGHTS) -> NDArray[uint32]:
        """
        Get the parameters of the weight generator on the machine.

        :param weights:
        """
        return param_generator_params(weights)

    def gen_weight_params_size_in_bytes(self, weights:  WEIGHTS) -> int:
        """
        The size of the weight parameters in bytes.

        :param weights:
        """
        return param_generator_params_size_in_bytes(weights)

    def gen_delays_id(self, delays: DELAYS) -> int:
        """
        Get the id of the delay generator on the machine.

        :param delays:
        """
        return param_generator_id(delays)

    def gen_delay_params(self, delays: DELAYS) -> NDArray[uint32]:
        """
        Get the parameters of the delay generator on the machine.

        :param delays:
        """
        return param_generator_params(delays)

    def gen_delay_params_size_in_bytes(self, delays: DELAYS) -> int:
        """
        The size of the delay parameters in bytes.

        :param delays:
        """
        return param_generator_params_size_in_bytes(delays)

    @property
    @abstractmethod
    def gen_connector_id(self) -> int:
        """
        The ID of the connection generator on the machine.
        """
        raise NotImplementedError

    def gen_connector_params(
            self, synapse_info: SynapseInformation) -> NDArray[uint32]:
        """
        Get the parameters of the on machine generation.

        :param synapse_info: The synaptic information
        """
        _ = synapse_info
        return numpy.zeros(0, dtype="uint32")

    @property
    def gen_connector_params_size_in_bytes(self) -> int:
        """
        The size of the connector parameters, in bytes.
        """
        return 0
