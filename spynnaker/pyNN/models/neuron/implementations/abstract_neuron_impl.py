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
from typing import Mapping, Optional, Sequence
from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.ranged import RangeDictionary
from spinn_front_end_common.interface.ds import DataType
from spynnaker.pyNN.utilities.struct import Struct


class AbstractNeuronImpl(object, metaclass=AbstractBase):
    """
    An abstraction of a whole neuron model including all parts.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        The name of the model.

        :rtype: str
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def binary_name(self) -> str:
        """
        The name of the binary executable of this implementation.

        :rtype: str
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def structs(self) -> Sequence[Struct]:
        """
        A list of structures used by the implementation.

        :rtype: list(Struct)
        """
        raise NotImplementedError

    @abstractmethod
    def get_global_weight_scale(self) -> float:
        """
        Get the weight scaling required by this model.

        :rtype: float
        """
        raise NotImplementedError

    @abstractmethod
    def get_n_synapse_types(self) -> int:
        """
        Get the number of synapse types supported by the model.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        """
        Get the ID of a synapse given the name.

        :param str target: The name of the synapse
        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def get_synapse_targets(self) -> Sequence[str]:
        """
        Get the target names of the synapse type.

        :rtype: list(str)
        """
        raise NotImplementedError

    @abstractmethod
    def get_recordable_variables(self) -> Sequence[str]:
        """
        Get the names of the variables that can be recorded in this model.

        :rtype: list(str)
        """
        raise NotImplementedError

    @abstractmethod
    def get_recordable_units(self, variable: str) -> str:
        """
        Get the units of the given variable that can be recorded.

        :param str variable: The name of the variable
        """
        raise NotImplementedError

    @abstractmethod
    def get_recordable_data_types(self) -> Mapping[str, DataType]:
        """
        Get the data type of the variables that can be recorded.

        :return: dictionary of name of variable to data type of variable
        :rtype: dict(str,~data_specification.enums.DataType)
        """
        raise NotImplementedError

    @abstractmethod
    def is_recordable(self, variable: str) -> bool:
        """
        Determine if the given variable can be recorded.

        :param str variable: The name of the variable
        :rtype: bool
        """
        raise NotImplementedError

    @abstractmethod
    def get_recordable_variable_index(self, variable: str) -> int:
        """
        Get the index of the variable in the list of variables that can be
        recorded.

        :param str variable: The name of the variable
        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def add_parameters(self, parameters: RangeDictionary):
        """
        Add the initial values of the parameters to the parameter holder.

        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            A holder of the parameters
        """
        raise NotImplementedError

    @abstractmethod
    def add_state_variables(self, state_variables: RangeDictionary):
        """
        Add the initial values of the state variables to the state
        variables holder.

        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            A holder of the state variables
        """
        raise NotImplementedError

    @abstractmethod
    def get_units(self, variable: str) -> str:
        """
        Get the units of the given variable.

        :param str variable: The name of the variable
        :rtype: str
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def is_conductance_based(self) -> bool:
        """
        Whether the model uses conductance.

        :rtype: bool
        """
        raise NotImplementedError
