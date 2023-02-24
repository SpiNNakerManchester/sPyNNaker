# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict
import sys
import numpy
from pyNN import descriptions
from spinn_utilities.classproperty import classproperty
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spynnaker.pyNN.models.defaults import get_dict_from_init
from spynnaker.pyNN.exceptions import SpynnakerException


class AbstractPyNNModel(object, metaclass=AbstractBase):
    """ A Model that can be passed in to a Population object in PyNN
    """

    __slots__ = []
    _max_atoms_per_core = defaultdict(lambda: None)

    @classmethod
    def set_model_max_atoms_per_dimension_per_core(cls, n_atoms=None):
        """ Set the default maximum number of atoms per dimension per core for
            this model.  This can be overridden by the individual Population.
            The new value can be None, meaning that the maximum is the same as
            the number of atoms, an int, meaning all Populations of this model
            must have one dimension, or a tuple of n integers, meaning all
            Populations of this model must have n dimensions.
            If not all Populations of this model have the same number of
            dimensions, it is recommended to set this to None here and then
            set the maximum on each Population.

        :param n_atoms: The new maximum, or None for the largest possible
        :type n_atoms: int or tuple or None
        """
        abs_max = cls.absolute_max_atoms_per_core
        if n_atoms is not None and numpy.prod(n_atoms) > abs_max:
            raise SpynnakerException(
                "The absolute maximum neurons per core for this model is"
                f" {abs_max}")
        AbstractPyNNModel._max_atoms_per_core[cls] = n_atoms

    @classmethod
    def get_model_max_atoms_per_dimension_per_core(cls):
        """ Get the maximum number of atoms per dimension per core for this
            model

        :rtype: int or tuple or None
        """
        # If there is a stored value, use it
        max_stored = AbstractPyNNModel._max_atoms_per_core.get(cls)
        if max_stored is not None:
            return max_stored

        # Otherwise return the absolute maximum
        return cls.absolute_max_atoms_per_core

    @classproperty
    def absolute_max_atoms_per_core(cls):  # pylint: disable=no-self-argument
        """ The absolute maximum number of atoms per core.
            This is an integer regardless of the number of dimensions
            in any vertex.

        :rtype: int
        """
        return sys.maxsize

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
    def create_vertex(self, n_neurons, label):
        """ Create a vertex for a population of the model

        :param int n_neurons: The number of neurons in the population
        :param str label: The label to give to the vertex
        :return: An application vertex for the population
        :rtype: ~spynnaker.pyNN.models.common.PopulationApplicationVertex
        """

    @property
    def name(self):
        """
        The name of this model

        :rtype: str
        """
        return self.__class__.__name__

    def describe(self, template='modeltype_default.txt', engine='default'):
        """ Returns a human-readable description of the population.

        The output may be customized by specifying a different template
        together with an associated template engine (see
        :mod:`pyNN.descriptions`).

        If ``template`` is ``None``, then a dictionary containing the template
        context will be returned.

        :param str template: Template filename
        :param engine: Template substitution engine
        :type engine: str or ~pyNN.descriptions.TemplateEngine or None
        :rtype: str or dict
        """
        context = {
            "name": self.name
        }
        return descriptions.render(engine, template, context)
