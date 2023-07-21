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
from typing import Iterable, Optional
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)


class AbstractSynapseType(
        AbstractStandardNeuronComponent, metaclass=AbstractBase):
    """
    Represents the synapse types supported.
    """

    __slots__ = ()

    @abstractmethod
    def get_n_synapse_types(self) -> int:
        """
        Get the number of synapse types supported.

        :return: The number of synapse types supported
        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        """
        Get the ID of a synapse given the name.

        :return: The ID of the synapse
        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def get_synapse_targets(self) -> Iterable[str]:
        """
        Get the target names of the synapse type.

        :return: an array of strings (usually a list or tuple)
        :rtype: iterable(str)
        """
        raise NotImplementedError
