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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


class AbstractNeuronImpl(object, metaclass=AbstractBase):
    """ An abstraction of a whole neuron model including all parts
    """

    __slots__ = ()

    @abstractproperty
    def model_name(self):
        """ The name of the model

        :rtype: str
        """

    @abstractproperty
    def binary_name(self):
        """ The name of the binary executable of this implementation

        :rtype str
        """

    @abstractproperty
    def structs(self):
        """ A list of structs used by the implementation

        :rtype: list(Struct)
        """

    @abstractmethod
    def get_n_cpu_cycles(self, n_neurons):
        """ Get the number of CPU cycles required to update the state

        :param int n_neurons: The number of neurons to get the cycles for
        :rtype: int
        """

    @abstractmethod
    def get_global_weight_scale(self):
        """ Get the weight scaling required by this model

        :rtype: int
        """

    @abstractmethod
    def get_n_synapse_types(self):
        """ Get the number of synapse types supported by the model

        :rtype: int
        """

    @abstractmethod
    def get_synapse_id_by_target(self, target):
        """ Get the ID of a synapse given the name

        :param str target: The name of the synapse
        :rtype: int
        """

    @abstractmethod
    def get_synapse_targets(self):
        """ Get the target names of the synapse type

        :rtype: list(str)
        """

    @abstractmethod
    def get_recordable_variables(self):
        """ Get the names of the variables that can be recorded in this model

        :rtype: list(str)
        """

    @abstractmethod
    def get_recordable_units(self, variable):
        """ Get the units of the given variable that can be recorded

        :param str variable: The name of the variable
        """

    @abstractmethod
    def get_recordable_data_types(self):
        """ Get the data type of the variables that can be recorded

        :return: dict of name of variable to DataType of variable
        """

    @abstractmethod
    def is_recordable(self, variable):
        """ Determine if the given variable can be recorded

        :param str variable: The name of the variable
        :rtype: bool
        """

    @abstractmethod
    def get_recordable_variable_index(self, variable):
        """ Get the index of the variable in the list of variables that can be\
            recorded

        :param str variable: The name of the variable
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

    @abstractmethod
    def get_units(self, variable):
        """ Get the units of the given variable

        :param str variable: The name of the variable
        """

    @abstractproperty
    def is_conductance_based(self):
        """ Determine if the model uses conductance

        :rtype: bool
        """

    def get_precomputed_values(self, parameters, state_variables):
        """ Get a dict of additional values calculated from the parameters
            and state variables, where the key is the name of the field in
            a struct.

            The values of the dict are each an AbstractList instance.  Each of
            the items in parameters and state_variables are also AbstractList
            instances; calculations can be performed by calling apply_operation
            on any of the items e.g.:
                parameters[PARAM].apply_operation(lambda x: numpy.exp(-x))
            Normal operations between parameters are also supported e.g.:
                parameters[PARAM_1] / parameters[PARAM_2]

            By default this returns an empty dict so must be overridden to
            provide additional values.

        :param RangeDictionary parameters: parameter values
        :param RangeDictionary state_variables: state variable values
        :rtype: dict(str, AbstractList)
        """
        return {}
