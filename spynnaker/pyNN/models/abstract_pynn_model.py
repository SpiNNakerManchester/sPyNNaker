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

from collections import defaultdict
import sys
from spinn_utilities.classproperty import classproperty
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spynnaker.pyNN.models.defaults import get_dict_from_init


class AbstractPyNNModel(object, metaclass=AbstractBase):
    """ A Model that can be passed in to a Population object in PyNN
    """

    __slots__ = []
    _max_atoms_per_core = defaultdict(lambda: sys.maxsize)

    @classmethod
    def set_model_max_atoms_per_core(cls, n_atoms=sys.maxsize):
        """ Set the maximum number of atoms per core for this model

        :param n_atoms: The new maximum, or None for the largest possible
        :type n_atoms: int or None
        """
        AbstractPyNNModel._max_atoms_per_core[cls] = n_atoms

    @classmethod
    def get_max_atoms_per_core(cls):
        """ Get the maximum number of atoms per core for this model

        :rtype: int
        """
        return AbstractPyNNModel._max_atoms_per_core[cls]

    @staticmethod
    def __get_init_params_and_svars(the_cls):
        init = getattr(the_cls, "__init__")
        while hasattr(init, "_method"):
            init = getattr(init, "_method")
        params = None
        if hasattr(init, "_parameters"):
            params = getattr(init, "_parameters")
        svars = None
        if hasattr(init, "_state_variables"):
            svars = getattr(init, "_state_variables")
        return init, params, svars

    @classproperty
    def default_parameters(cls):  # pylint: disable=no-self-argument
        """ Get the default values for the parameters of the model.

        :rtype: dict(str, Any)
        """
        init, params, svars = cls.__get_init_params_and_svars(cls)
        return get_dict_from_init(init, skip=svars, include=params)

    @classproperty
    def default_initial_values(cls):  # pylint: disable=no-self-argument
        """ Get the default initial values for the state variables of the model

        :rtype: dict(str, Any)
        """
        init, params, svars = cls.__get_init_params_and_svars(cls)
        if params is None and svars is None:
            return {}
        return get_dict_from_init(init, skip=params, include=svars)

    @classmethod
    def get_parameter_names(cls):
        """ Get the names of the parameters of the model

        :rtype: list(str)
        """
        return cls.default_parameters.keys()  # pylint: disable=no-member

    @classmethod
    def has_parameter(cls, name):
        """ Determine if the model has a parameter with the given name

        :param str name: The name of the parameter to check for
        :rtype: bool
        """
        return name in cls.default_parameters

    @abstractproperty
    def default_population_parameters(self):
        """ Get the default values for the parameters at the population level
            These are parameters that can be passed in to the Population\
            constructor in addition to the standard PyNN options

        :rtype: dict(str, Any)
        """

    @abstractmethod
    def create_vertex(self, n_neurons, label, constraints):
        """ Create a vertex for a population of the model

        :param int n_neurons: The number of neurons in the population
        :param str label: The label to give to the vertex
        :param constraints:
            A list of constraints to give to the vertex, or None
        :type constraints:
            list(~pacman.model.constraints.AbstractConstraint) or None
        :return: An application vertex for the population
        :rtype: ~pacman.model.graphs.application.ApplicationVertex
        """
