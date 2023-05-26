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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractStandardNeuronComponent(object, metaclass=AbstractBase):
    """
    Represents a component of a standard neural model.
    """
    __slots__ = (
        "__structs",
        "__units")

    def __init__(self, structs, units):
        """
        :param list(Struct) structs: The structures of the component
        :param dict units: The units to use for each parameter
        """
        self.__structs = structs
        self.__units = units

    @property
    def structs(self):
        """
        The structures of the component.  If there are multiple structures,
        the order is how they will appear in memory; where there are
        structures that repeat per neuron the repeats will appear adjacent
        e.g. for non-repeating structure `g`, followed by repeating structures
        `s1` and `s2` with 3 neurons the layout will be:
        ``[g, s1, s1, s1, s2, s2, s2]``.

        :rtype: list(~spynnaker.pyNN.utilities.struct.Struct)
        """
        return self.__structs

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

    def has_variable(self, variable):
        """
        Determine if this component has a variable by the given name.

        :param str variable: The name of the variable
        :rtype: bool
        """
        return variable in self.__units

    def get_units(self, variable):
        """
        Get the units of the given variable.

        :param str variable: The name of the variable
        """
        return self.__units[variable]
