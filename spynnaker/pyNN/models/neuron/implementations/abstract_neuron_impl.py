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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


class AbstractNeuronImpl(object, metaclass=AbstractBase):
    """
    An abstraction of a whole neuron model including all parts.
    """

    __slots__ = ()

    @abstractproperty
    def model_name(self):
        """
        The name of the model.

        :rtype: str
        """

    @abstractproperty
    def binary_name(self):
        """
        The name of the binary executable of this implementation.

        :rtype: str
        """

    @abstractproperty
    def structs(self):
        """
        A list of structures used by the implementation.

        :rtype: list(Struct)
        """

    @abstractmethod
    def get_global_weight_scale(self):
        """
        Get the weight scaling required by this model.

        :rtype: int
        """

    @abstractmethod
    def get_n_synapse_types(self):
        """
        Get the number of synapse types supported by the model.

        :rtype: int
        """

    @abstractmethod
    def get_synapse_id_by_target(self, target):
        """
        Get the ID of a synapse given the name.

        :param str target: The name of the synapse
        :rtype: int
        """

    @abstractmethod
    def get_synapse_targets(self):
        """
        Get the target names of the synapse type.

        :rtype: list(str)
        """

    @abstractmethod
    def get_recordable_variables(self):
        """
        Get the names of the variables that can be recorded in this model.

        :rtype: list(str)
        """

    @abstractmethod
    def get_recordable_units(self, variable):
        """
        Get the units of the given variable that can be recorded.

        :param str variable: The name of the variable
        """

    @abstractmethod
    def get_recordable_data_types(self):
        """
        Get the data type of the variables that can be recorded.

        :return: dictionary of name of variable to data type of variable
        :rtype: dict(str,~data_specification.enums.DataType)
        """

    @abstractmethod
    def is_recordable(self, variable):
        """
        Determine if the given variable can be recorded.

        :param str variable: The name of the variable
        :rtype: bool
        """

    @abstractmethod
    def get_recordable_variable_index(self, variable):
        """
        Get the index of the variable in the list of variables that can be
        recorded.

        :param str variable: The name of the variable
        :rtype: int
        """

    @abstractmethod
    def add_parameters(self, parameters):
        """
        Add the initial values of the parameters to the parameter holder.

        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            A holder of the parameters
        """

    @abstractmethod
    def add_state_variables(self, state_variables):
        """
        Add the initial values of the state variables to the state
        variables holder.

        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            A holder of the state variables
        """

    @abstractmethod
    def get_units(self, variable):
        """
        Get the units of the given variable.

        :param str variable: The name of the variable
        :rtype: str
        """

    @abstractproperty
    def is_conductance_based(self):
        """
        Whether the model uses conductance.

        :rtype: bool
        """
