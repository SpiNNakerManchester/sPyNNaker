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
from __future__ import annotations
from collections import defaultdict
import sys
from typing import (
    Any, cast, Dict, Optional, Sequence, Tuple, TYPE_CHECKING, Union)
import numpy
from pyNN import descriptions
from spinn_utilities.classproperty import classproperty
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod)
from spynnaker.pyNN.models.defaults import AbstractProvidesDefaults
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.data import SpynnakerDataView
if TYPE_CHECKING:
    from spynnaker.pyNN.models.common.population_application_vertex import (
        PopulationApplicationVertex)


class AbstractPyNNModel(AbstractProvidesDefaults, metaclass=AbstractBase):
    """
    A Model that can be passed in to a Population object in PyNN.
    """

    __slots__ = ()

    # The maximum number of atoms per core for PyNN models
    _max_atoms_per_core: Dict[type, Optional[Tuple[int, ...]]] = defaultdict(
        lambda: None)

    @classmethod
    def verify_may_set(cls, param: str) -> None:
        """ If a Population has been created, this method will raise an
            exception; used to avoid setting global limits after a Population
            has been created.

        :param param:
            The parameter name that can be used to set the value being changed
            in the Population constructor instead.
        """
        SpynnakerDataView.check_user_can_act()
        if SpynnakerDataView.get_n_populations() == 0:
            return
        raise SpynnakerException(
            "Global set is not supported after a Population has been "
            "created. Either move it above the creation of all Populations "
            f"or provide {param} during the creation of each Population it "
            "applies to.")

    @classmethod
    def set_model_max_atoms_per_dimension_per_core(
            cls, n_atoms: Union[None, int, Tuple[int, ...]] = None) -> None:
        """
        Set the default maximum number of atoms per dimension per core for
        this model.  This can be overridden by the individual Population.
        The new value can be `None`, meaning that the maximum is the same as
        the number of atoms, an int, meaning all Populations of this model
        must have one dimension, or a tuple of *n* integers, meaning all
        Populations of this model must have *n* dimensions.
        If not all Populations of this model have the same number of
        dimensions, it is recommended to set this to `None` here and then
        set the maximum on each Population.

        :param n_atoms: The new maximum, or `None` for the largest possible
        """
        cls.verify_may_set(param="neurons_per_core")
        abs_max = cls.absolute_max_atoms_per_core
        if n_atoms is None:
            AbstractPyNNModel._max_atoms_per_core[cls] = None
        elif numpy.isscalar(n_atoms):
            if n_atoms > abs_max:
                raise SpynnakerException(
                    "The absolute maximum neurons per core for this"
                    f" model is {abs_max}")
            max_atoms_int: int = int(cast(int, n_atoms))
            AbstractPyNNModel._max_atoms_per_core[cls] = (max_atoms_int, )
        else:
            if numpy.prod(n_atoms) > abs_max:
                raise SpynnakerException(
                    "The absolute maximum sum of neurons per core for this"
                    f" model is {abs_max}")
            max_atoms_tuple: Tuple[int, ...] = cast(
                Tuple[int, ...],  n_atoms)
            AbstractPyNNModel._max_atoms_per_core[cls] = max_atoms_tuple

    @classmethod
    def get_model_max_atoms_per_dimension_per_core(cls) -> Tuple[int, ...]:
        """
        :returns:
            The maximum number of atoms per dimension per core for this model.
        """
        # If there is a stored value, use it
        max_stored = AbstractPyNNModel._max_atoms_per_core.get(cls)
        if max_stored is not None:
            return max_stored

        # Otherwise return the absolute maximum assuming 1D
        return (cls.absolute_max_atoms_per_core, )

    @classmethod
    def reset_all(cls) -> None:
        """
        Reset the maximum values for all classes.
        """
        AbstractPyNNModel._max_atoms_per_core.clear()

    @classproperty
    def absolute_max_atoms_per_core(  # pylint: disable=no-self-argument
            cls) -> int:
        """
        The absolute maximum number of atoms per core.

        This is an integer regardless of the number of dimensions
        in any vertex.

        :returns: The absolute maximum number of atoms per core.
        """
        return sys.maxsize

    @classmethod
    def get_parameter_names(cls) -> Sequence[str]:
        """
        :returns: The names of the parameters of the model.
        """
        return cls.default_parameters.keys()  # pylint: disable=no-member

    @classmethod
    def has_parameter(cls, name: str) -> bool:
        """
        :param name: The name of the parameter to check for
        :returns: True if the model has a parameter with the given name
        """
        return name in cls.default_parameters

    #: The default values for the parameters at the population level.
    #: These are parameters that can be passed in to the Population
    #: constructor in addition to the standard PyNN options.
    default_population_parameters: Dict[str, Any] = {}

    @classmethod
    def _get_default_population_parameters(cls) -> Dict[str, Any]:
        """
        Get the default population parameters.
        Slightly contorted to allow for overriding class variables.
        """
        return dict(cls.default_population_parameters)

    @abstractmethod
    def create_vertex(
            self, n_neurons: int, label: str) -> PopulationApplicationVertex:
        """
        Create a vertex for a population of the model.

        :param n_neurons: The number of neurons in the population
        :param label: The label to give to the vertex
        :return: An application vertex for the population
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        """
        The name of this model.
        """
        return self.__class__.__name__

    def describe(self, template: Optional[str] = 'modeltype_default.txt',
                 engine: str = 'default') -> str:
        """
        Returns a human-readable description of the population.

        The output may be customised by specifying a different template
        together with an associated template engine (see
        :mod:`pyNN.descriptions`).

        If ``template`` is ``None``, then a dictionary containing the template
        context will be returned.

        :param template: Template filename
        :param engine: Template substitution engine
        :returns: A human-readable description
        """
        context = {
            "name": self.name
        }
        return descriptions.render(engine, template, context)
