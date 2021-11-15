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
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.application import ApplicationVertex


@require_subclass(ApplicationVertex)
class AbstractPopulationInitializable(object, metaclass=AbstractBase):
    """ Indicates that this application vertex has properties that can be\
        initialised by a PyNN Population
    """

    __slots__ = ()

    @abstractmethod
    def initialize(self, variable, value, selector=None):
        """ Set the initial value of one of the state variables of the neurons\
            in this population.

        :param str variable: The name of the variable to set
        :param value: The value of the variable to set
        :type value: float or int or Any
        """

    @property
    def initial_values(self):
        """ A dict containing the initial values of the state variables.

        :rtype: dict(str,Any)
        """
        return self.get_initial_values(None)

    def get_initial_values(self, selector=None):
        """ A dict containing the initial values of the state variables.

        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :rtype: dict(str,Any)
        """
        results = dict()
        for variable_init in self.initialize_parameters:
            if variable_init.endswith("_init"):
                variable = variable_init[:-5]
            else:
                variable = variable_init
            results[variable] = self.get_initial_value(variable_init, selector)
        return results

    @abstractmethod
    def get_initial_value(self, variable, selector=None):
        """ Gets the value for any variable whose in initialize_parameters.keys

        Should return the current value not the default one.

        Must support the variable as listed in initialize_parameters.keys,
        ideally also with ``_init`` removed or added.

        :param str variable: variable name with or without ``_init``
        :param selector: a description of the subrange to accept, or None for
            all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :return: A list or an Object which act like a list
        :rtype: iterable
        """

    @abstractproperty
    def initialize_parameters(self):
        """ List the parameters that are initializable.

        If "foo" is initializable there should be a setter ``initialize_foo``
        and a getter property ``foo_init``

        :return: list of property names
        :rtype: iterable(str)
        """
        # Note: this will have been non_pynn_default_parameters
