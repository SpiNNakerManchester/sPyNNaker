# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractStandardNeuronComponent(object, metaclass=AbstractBase):
    """ Represents a component of a standard neural model.
    """

    __slots__ = ["__structs", "__units"]

    def __init__(self, structs, units):
        """
        :param list(Struct) structs: The structs of the component
        :param dict units: The units to use for each parameter
        """
        self.__structs = structs
        self.__units = units

    @property
    def structs(self):
        """ The structures of the component.  If there are multiple structs,
            the order is how they will appear in memory; where there are
            structs that repeat per neuron the repeats will appear adjacent
            e.g. for non-repeating struct g, followed by repeating structs s1
            and s2 with 3 neurons the layout will be:
            [g, s1, s1, s1, s2, s2, s2].

        :rtype: list(~spynnaker.pyNN.utilities.struct.Struct)
        """
        return self.__structs

    @abstractmethod
    def get_n_cpu_cycles(self, n_neurons):
        """ Get the number of CPU cycles required to update the state

        :param int n_neurons: The number of neurons to get the cycles for
        :rtype: int
        """

    @abstractmethod
    def add_parameters(self, parameters):
        """ Add the initial values of the parameters to the parameter holder

        :param ~spinn_utilities.ranged.RangeDictionary parameters:
            A holder of the parameters
        """

    @abstractmethod
    def add_state_variables(self, state_variables):
        """ Add the initial values of the state variables to the state\
            variables holder

        :param ~spinn_utilities.ranged.RangeDictionary state_variables:
            A holder of the state variables
        """

    def has_variable(self, variable):
        """ Determine if this component has a variable by the given name

        :param str variable: The name of the variable
        :rtype: bool
        """
        return variable in self.__units

    def get_units(self, variable):
        """ Get the units of the given variable

        :param str variable: The name of the variable
        """
        return self.__units[variable]