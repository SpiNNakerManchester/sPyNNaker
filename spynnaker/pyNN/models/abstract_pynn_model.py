try:
    from collections.abc import defaultdict
except ImportError:
    from collections import defaultdict
import sys
from six import add_metaclass
from spinn_utilities.classproperty import classproperty
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spynnaker.pyNN.models.defaults import get_dict_from_init


@add_metaclass(AbstractBase)
class AbstractPyNNModel(object):
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
    def _get_init_params_and_svars(cls):
        init = getattr(cls, "__init__")
        params = None
        if hasattr(init, "_parameters"):
            params = getattr(init, "_parameters")
        svars = None
        if hasattr(init, "_state_variables"):
            svars = getattr(init, "_state_variables")
        return init, params, svars

    @classproperty
    def default_parameters(cls):
        """ Get the default values for the parameters of the model.

        :rtype: dict(str, object)
        """
        init, params, svars = cls._get_init_params_and_svars(cls)
        return get_dict_from_init(init, skip=svars, include=params)

    @classproperty
    def default_initial_values(cls):
        """ Get the default initial values for the state variables of the model

        :rtype: dict(str, object)
        """
        init, params, svars = cls._get_init_params_and_svars(cls)
        if params is None and svars is None:
            return {}
        return get_dict_from_init(init, skip=params, include=svars)

    @classmethod
    def get_parameter_names(cls):
        """ Get the names of the parameters of the model

        :rtype: list(str)
        """
        return cls.default_parameters.keys()

    @classmethod
    def has_parameter(cls, name):
        """ Determine if the model has a parameter with the given name

        :param name: The name of the parameter to check for
        :type name: str
        :rtype: bool
        """
        return name in cls.default_parameters

    @abstractproperty
    @staticmethod
    def default_population_parameters():
        """ Get the default values for the parameters at the population-level;\
            these are parameters that can be passed in to the Population\
            constructor in addition to the standard PyNN options

        :rtype: dict(str, object)
        """

    @abstractmethod
    def create_vertex(self, n_neurons, label, constraints):
        """ Create a vertex for a population of the model

        :param n_neurons: The number of neurons in the population
        :type n_neurons: int
        :param label: The label to give to the vertex
        :type label: str
        :param constraints:\
            A list of constraints to give to the vertex, or None
        :type constraints: list or None
        :return: An application vertex for the population
        :rtype: :py:class:`pacman.model.graphs.application.ApplicationVertex`
        """
