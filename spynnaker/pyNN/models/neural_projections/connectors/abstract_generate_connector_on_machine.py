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
import numpy
from numpy import uint32
from numpy.typing import NDArray
from typing import TYPE_CHECKING
from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationEdge
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.common.param_generator_data import (
    param_generator_params, param_generator_params_size_in_bytes,
    param_generator_id, is_param_generatable)
from spynnaker.pyNN.types import (Delay_Types, Weight_Types)
from .abstract_generate_connector_on_host import (
    AbstractGenerateConnectorOnHost)
from pyNN.random import RandomDistribution
from spynnaker.pyNN.utilities.utility_calls import check_rng
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neural_projections import SynapseInformation


# Hashes of the connection generators supported by the synapse expander
class ConnectorIDs(Enum):
    ONE_TO_ONE_CONNECTOR = 0
    ALL_TO_ALL_CONNECTOR = 1
    FIXED_PROBABILITY_CONNECTOR = 2
    FIXED_TOTAL_NUMBER_CONNECTOR = 3
    FIXED_NUMBER_PRE_CONNECTOR = 4
    FIXED_NUMBER_POST_CONNECTOR = 5
    KERNEL_CONNECTOR = 6


class AbstractGenerateConnectorOnMachine(
        AbstractConnector, metaclass=AbstractBase):
    """
    Indicates that the connectivity can be generated on the machine.
    """

    __slots__ = ()

    @overrides(AbstractConnector.validate_connection)
    def validate_connection(
            self, application_edge: ApplicationEdge,
            synapse_info: SynapseInformation):
        # If we can't generate on machine, we must be able to generate on host
        if not self.generate_on_machine(
                synapse_info.weights, synapse_info.delays):
            if not isinstance(self, AbstractGenerateConnectorOnHost):
                raise SynapticConfigurationException(
                    "The parameters of this connection do not allow it to be"
                    " generated on the machine, but the connector cannot"
                    " be generated on host!")

    def generate_on_machine(
            self, weights: Weight_Types, delays: Delay_Types) -> bool:
        """
        Determine if this instance can generate on the machine.

        Default implementation returns True if the weights and delays can
        be generated on the machine

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.RandomDistribution
            or int or float or list(int) or list(float)
        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.RandomDistribution
            or int or float or list(int) or list(float)
        :rtype: bool
        """
        if (not is_param_generatable(weights) or
                not is_param_generatable(delays)):
            return False
        if isinstance(weights, RandomDistribution):
            check_rng(weights.rng, "RandomDistribution in weight")
        if isinstance(delays, RandomDistribution):
            check_rng(delays.rng, "RandomDistribution in delay")
        return True

    def gen_weights_id(self, weights: Weight_Types) -> int:
        """
        Get the id of the weight generator on the machine.

        :param weights:
        :type weights: ~pyNN.random.RandomDistribtuion or int or float
        :rtype: int
        """
        return param_generator_id(weights)

    def gen_weights_params(self, weights: Weight_Types) -> NDArray[uint32]:
        """
        Get the parameters of the weight generator on the machine.

        :param weights:
        :type weights: ~pyNN.random.RandomDistribution or int or float
        :rtype: ~numpy.ndarray(~numpy.uint32)
        """
        return param_generator_params(weights)

    def gen_weight_params_size_in_bytes(self, weights) -> int:
        """
        The size of the weight parameters in bytes.

        :param weights:
        :type weights: ~pyNN.random.RandomDistribution or int or float
        :rtype: int
        """
        return param_generator_params_size_in_bytes(weights)

    def gen_delays_id(self, delays: Delay_Types) -> int:
        """
        Get the id of the delay generator on the machine.

        :param delays:
        :type delays: ~pyNN.random.RandomDistribution or int or float
        :rtype: int
        """
        return param_generator_id(delays)

    def gen_delay_params(self, delays: Delay_Types) -> NDArray[uint32]:
        """
        Get the parameters of the delay generator on the machine.

        :param delays:
        :type delays: ~pyNN.random.RandomDistribution or int or float
        :rtype: ~numpy.ndarray(~numpy.uint32)
        """
        return param_generator_params(delays)

    def gen_delay_params_size_in_bytes(self, delays: Delay_Types) -> int:
        """
        The size of the delay parameters in bytes.

        :param delays:
        :type delays: ~pyNN.random.RandomDistribution  or int or float
        :rtype: int
        """
        return param_generator_params_size_in_bytes(delays)

    @property
    @abstractmethod
    def gen_connector_id(self) -> int:
        """
        The ID of the connection generator on the machine.

        :rtype: int
        """
        raise NotImplementedError

    def gen_connector_params(self) -> NDArray[uint32]:
        """
        Get the parameters of the on machine generation.

        :rtype: ~numpy.ndarray(uint32)
        """
        # pylint: disable=unused-argument
        return numpy.zeros(0, dtype="uint32")

    @property
    def gen_connector_params_size_in_bytes(self) -> int:
        """
        The size of the connector parameters, in bytes.

        :rtype: int
        """
        return 0
