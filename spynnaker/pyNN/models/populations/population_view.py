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
import logging
import os
from typing import (
    Any, Callable, Dict, Iterable, Iterator, List, Optional,
    overload, Sequence, Tuple, TYPE_CHECKING, Union)

import numpy
from numpy import bool_, integer
from numpy.typing import NDArray

from pyNN import descriptions
from pyNN.random import NumpyRNG
from pyNN.space import BaseStructure
import neo  # type: ignore[import]

from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.abstract_sized import AbstractSized

from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from spynnaker.pyNN.types import Selector
from spynnaker.pyNN.utilities.utility_calls import get_neo_io

from .population_base import PopulationBase

if TYPE_CHECKING:
    from .population import Population
    from spynnaker.pyNN.models.current_sources import AbstractCurrentSource
    from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
    from spynnaker.pyNN.models.common.population_application_vertex import (
        PopulationApplicationVertex)
    from spynnaker.pyNN.models.common import ParameterHolder
    from spynnaker.pyNN.models.common.types import Names, Values
    from spynnaker.pyNN.models.recorder import Recorder
    from spynnaker.pyNN.types import IoDest

logger = FormatAdapter(logging.getLogger(__name__))


class PopulationView(PopulationBase):
    """
    A view of a subset of neurons within a
    :py:class:`~spynnaker.pyNN.models.populations.Population`.

    In most ways, Populations and PopulationViews have the same behaviour,
    i.e., they can be recorded, connected with Projections, etc.
    It should be noted that any changes to neurons in a PopulationView
    will be reflected in the parent Population and *vice versa.*

    It is possible to have views of views.

    .. note::
        Selector to Id is actually handled by :py:class:`~.AbstractSized`.
    """
    __slots__ = (
        "__annotations",
        "__indexes",
        "__label",
        "__mask",
        "__parent",
        "__population",
        "__vertex",
        "__recorder")

    __realslots__ = frozenset("_PopulationView" + item for item in __slots__)

    def __init__(
            self, parent: Union[Population, 'PopulationView'],
            selector: Selector, label: Optional[str] = None):
        """
        :param parent: the population or view to make the view from
        :param selector: a slice or numpy mask array.
            The mask array should either be a Boolean array (ideally) of the
            same size as the parent,
            or an integer array containing cell indices,
            i.e. if `p.size == 5` then:

            ::

                PopulationView(p, array([False, False, True, False, True]))
                PopulationView(p, array([2, 4]))
                PopulationView(p, slice(2, 5, 2))

            will all create the same view.
        :param label: A label for the view
        """
        self.__parent = parent
        sized = AbstractSized(parent.size)
        ids = sized.selector_to_ids(selector, warn=True)

        if isinstance(parent, PopulationView):
            self.__population = parent.grandparent
            self.__indexes: Sequence[int] = parent.index_in_grandparent(ids)
        else:
            self.__population = parent
            self.__indexes = ids
        self.__mask = selector
        if label is None:
            label = f"{parent.label}:{selector}"
        self.__label = label
        self.__annotations: Dict[str, Any] = dict()

        # Get these two objects to make access easier
        # pylint: disable=protected-access
        self.__vertex = self.__population._vertex
        # pylint: disable=protected-access
        self.__recorder = self.__population._recorder

    def __getattr__(self, name: str) -> ParameterHolder:
        return self.__vertex.get_parameter_values(name, self.__indexes)

    def __setattr__(self, name: str, value: Values) -> None:
        if name in self.__realslots__:
            object.__setattr__(self, name, value)
            return
        return self.__vertex.set_parameter_values(name, value, self.__indexes)

    @property
    def size(self) -> int:
        """
        The total number of neurons in the Population View.
        """
        return len(self.__indexes)

    @property
    def label(self) -> str:
        """
        A label for the Population View.
        """
        return self.__label

    @property
    def celltype(self) -> AbstractPyNNModel:
        """
        The type of neurons making up the underlying Population.
        """
        return self.__parent.celltype

    @property
    def initial_values(self) -> ParameterHolder:
        """
        A dict containing the initial values of the state variables.
        """
        return self.__vertex.get_initial_state_values(
            self.__vertex.get_state_variables(), self.__indexes)

    @property
    def current_values(self) -> ParameterHolder:
        """
        A dict containing the current values of the state variables.
        """
        warn_once(
            logger, "current_values is non-standard PyNN and therefore "
            "will not be portable to other simulators.")
        return self.__vertex.get_current_state_values(
            self.__vertex.get_state_variables(), self.__indexes)

    @property
    def parent(self) -> Union[Population, 'PopulationView']:
        """
        A reference to the parent Population (that this is a view of).
        """
        return self.__parent

    @property
    def mask(self) -> Selector:
        """
        The selector mask that was used to create this view.
        """
        return self.__mask

    @property
    @overrides(PopulationBase.all_cells)
    def all_cells(self) -> Sequence['IDMixin']:
        """
        An array containing the cell IDs of all neurons in the
        Population (all MPI nodes).
        """
        return [IDMixin(self.__population, idx) for idx in self.__indexes]

    @property
    def _indexes(self) -> Tuple[int, ...]:
        return tuple(self.__indexes)

    @overload
    def __getitem__(self, index: int) -> 'IDMixin':
        ...

    @overload
    def __getitem__(self, index: Union[
            None, slice, List[int], List[bool], NDArray[bool_],
            NDArray[integer]]) -> 'PopulationView':
        ...

    def __getitem__(self, index: Union[
            None, int, slice, List[int], List[bool], NDArray[bool_],
            NDArray[integer]]) -> 'PopulationView':
        """
        Return either a single cell (ID object) from the Population,
        if index is an integer, or a subset of the cells
        (PopulationView object), if index is a slice or array.

        .. note::
            ``__getitem__`` is called when using[] access, e.g. if
            ``p = Population(...)`` then
            ``p[2]`` is equivalent to ``p.__getitem__(2)``, and
            ``p[3:6]`` is equivalent to ``p.__getitem__(slice(3, 6))``
        """
        if isinstance(index, int):
            return IDMixin(self.__population, index)
        return PopulationView(self, index, label=self.label + "_" + str(index))

    def __iter__(self) -> Iterator['IDMixin']:
        """
        Iterator over cell IDs (on the local node).
        """
        for idx in self.__indexes:
            yield IDMixin(self.__population, idx)

    def __len__(self) -> int:
        """
        Return the total number of cells in the population (all nodes).
        """
        return len(self.__indexes)

    @property
    @overrides(PopulationBase.positions)
    def positions(self) -> NDArray[numpy.floating]:
        raise NotImplementedError("Not implemented for views")

    @property
    @overrides(PopulationBase.position_generator)
    def position_generator(self) -> Callable[[int], NDArray[numpy.floating]]:
        raise NotImplementedError("Not implemented for views")

    def all(self) -> Iterator[IDMixin]:
        """
        :returns: An iterator over cell IDs (on all MPI nodes).
        """
        for idx in self.__indexes:
            yield IDMixin(self.__population, idx)

    def can_record(self, variable: str) -> bool:
        """
        Determine whether variable can be recorded from this population.

        :returns: True if this variable can be recorded,
            False otherwise including if the variable is invalid.
        """
        return variable in self.__vertex.get_recordable_variables()

    @property
    def conductance_based(self) -> bool:
        """
        Whether the post-synaptic response is modelled as a
        change in conductance or a change in current.
        """
        return self.__vertex.conductance_based

    @overrides(PopulationBase.inject)
    def inject(self, current_source: AbstractCurrentSource) -> None:
        """
        Injects the specified current_source into this PopulationView.

        :param current_source:
            the current source to be injected
        """
        self.__vertex.inject(current_source, self.__indexes)

    def describe(self, template: str = 'populationview_default.txt',
                 engine: str = 'default') -> str:
        """
        Returns a human-readable description of the population view.

        The output may be customised by specifying a different template
        together with an associated template engine (see pyNN.descriptions).

        If template is ``None``, then a dictionary containing the template
        context will be returned.

        :param template: Template filename
        :param engine: Template substitution engine
        :returns: A human-readable description of the population view.
        """
        context = {"label": self.label,
                   "parent": self.parent.label,
                   "mask": self.mask,
                   "size": self.size}
        context.update(self.__annotations)
        return descriptions.render(engine, template, context)

    def find_units(self, variable: str) -> str:
        """
        Get the units of a variable

        .. warning::
            No PyNN description of this method.

        :param variable: The name of the variable
        :return: The units of the variable
        """
        return self.__vertex.get_units(variable)

    def get(self, parameter_names: Names,
            gather: bool = False, simplify: bool = True) -> ParameterHolder:
        """
        Get the values of the given parameters for all cells in the population.

        Values will be expressed in the standard PyNN units (i.e. millivolts,
        nanoamps, milliseconds, microsiemens, nanofarads, event per second).

        .. note::
            SpiNNaker always gathers.

        :param parameter_names:
        :param gather: Ignored. Purely for PyNN compatibility
        :param simplify: Ignored.  Purely for PyNN compatibility
        :returns: The values of the given parameters for all cell
        """
        if not gather:
            logger.warning("SpiNNaker only supports gather=True. We will run "
                           "as if gather was set to True.")
        if simplify is not True:
            logger.warning("The simplify value is ignored if not set to true")

        return self.__vertex.get_parameter_values(
            parameter_names, self.__indexes)

    @overrides(PopulationBase.get_data)
    def get_data(
            self, variables: Names = 'all',
            gather: bool = True, clear: bool = False, *,
            annotations: Optional[Dict[str, Any]] = None) -> neo.Block:
        """
        Return a Neo Block containing the data(spikes, state variables)
        recorded from the Population.

        :param variables: Either a single variable name or a list of variable
            names. Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :param gather: Ignored. Purely for PyNN compatibility

            .. note::
                SpiNNaker always gathers.

        :param clear:
            If True, recorded data will be deleted from the Population.
        :param annotations: annotations to put on the neo block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the variable or variables have not been previously set to
            record.
        """
        if not gather:
            logger.warning("SpiNNaker only supports gather=True. We will run "
                           "as if gather was set to True.")
        if annotations is not None:
            warn_once(
                logger, "Annotations parameter is not standard PyNN so may "
                "not be supported by all platforms.")

        return self.__recorder.extract_neo_block(
            variables, self.__indexes, clear, annotations)

    def spinnaker_get_data(
            self, variable: str, as_matrix: bool = False) -> NDArray:
        """
        SsPyNNaker specific method for getting data as a numpy array,
        instead of the Neo-based object

        :param variable: a single variable name
        :param as_matrix: If set True the data is returned as a 2d matrix
        :return: array of the data
        """
        return self.__population.spinnaker_get_data(
            variable, as_matrix, self.__indexes)

    @overrides(PopulationBase.get_spike_counts)
    def get_spike_counts(self, gather: bool = True) -> Dict[int, int]:
        self._check_params(gather)
        with NeoBufferDatabase() as db:
            return db.get_spike_counts(
                self.__recorder.recording_label, self.__indexes)

    @property
    def grandparent(self) -> Population:
        """
        The parent Population at the root of the tree (since the
        immediate parent may itself be a PopulationView).

        The name "grandparent" is of course a little misleading, as it could
        be just the parent, or the great, great, great, ..., grandparent.
        """
        return self.__population

    @overload
    def id_to_index(self, id: int) -> int:  # pylint: disable=redefined-builtin
        ...

    @overload
    def id_to_index(
            self, id: Iterable[int]  # pylint: disable=redefined-builtin
            ) -> List[int]:
        ...

    def id_to_index(
            self, id: Union[int, Iterable[int]]) -> \
            Union[int, List[int]]:  # pylint: disable=redefined-builtin
        """
        Given the ID(s) of cell(s) in the PopulationView, return its /
        their index / indices(order in the PopulationView).

        assert pv.id_to_index(pv[3]) == 3

        :param id:
        :returns: Index in this View
        """
        if isinstance(id, int):
            return self.__indexes.index(id)
        return [self.__indexes.index(idx) for idx in id]

    def index_in_grandparent(self, indices: Iterable[int]) -> List[int]:
        """
        Given an array of indices, return the indices in the parent
        population at the root of the tree.

        :param indices:
        :returns: Indices in the parent
        """
        return [self.__indexes[index] for index in indices]

    def initialize(self, **initial_values: Values) -> None:
        """
        Set initial values of state variables, e.g. the membrane potential.
        Values passed to ``initialize()`` may be:

        * single numeric values (all neurons set to the same value), or
        * :py:class:`~spynnaker.pyNN.RandomDistribution` objects, or
        * lists / arrays of numbers of the same size as the population
          mapping functions, where a mapping function accepts a single
          argument (the cell index) and returns a single number.

        Values should be expressed in the standard PyNN units (i.e.
        millivolts, nanoamps, milliseconds, microsiemens, nanofarads,
        events per second).

        Examples::

            p.initialize(v=-70.0)
            p.initialize(v=rand_distr, gsyn_exc=0.0)
            p.initialize(v=lambda i: -65 + i / 10.0)
        """
        for variable, value in initial_values.items():
            self.__vertex.set_initial_state_values(
                variable, value, self.__indexes)

    def set_state(self, **initial_values: Values) -> None:
        """
        Set current values of state variables, e.g. the membrane potential.
        Values passed to ``set_state()`` may be:

        * single numeric values (all neurons set to the same value), or
        * :py:class:`~spynnaker.pyNN.RandomDistribution` objects, or
        * lists / arrays of numbers of the same size as the population
          mapping functions, where a mapping function accepts a single
          argument (the cell index) and returns a single number.

        Values should be expressed in the standard PyNN units (i.e.
        millivolts, nanoamps, milliseconds, microsiemens, nanofarads,
        events per second).

        Examples::

            p.set_state(v=-70.0)
            p.set_state(v=rand_distr, gsyn_exc=0.0)
            p.set_state(v=lambda i: -65 + i / 10.0)
        """
        warn_once(
            logger, "set_state is non-standard PyNN and therefore "
            "will not be portable to other simulators.")
        for variable, value in initial_values.items():
            self.__vertex.set_current_state_values(
                variable, value, self.__indexes)

    @overrides(PopulationBase.record)
    def record(self, variables: Names, to_file: IoDest = None,
               sampling_interval: Optional[int] = None) -> None:
        self.__recorder.record(
            variables, to_file, sampling_interval, self.__indexes)

    @property
    @overrides(PopulationBase.structure)
    def structure(self) -> Optional[BaseStructure]:
        raise NotImplementedError("Not implemented for views")

    def sample(
            self, n: int, rng: Optional[NumpyRNG] = None) -> 'PopulationView':
        """
        Randomly sample `n` cells from the Population view, and return a
        new PopulationView object.

        :param n: The number of cells to select
        :param rng: Random number generator
        :returns: A PopulationView over n random cells.
        """
        if not rng:
            rng = NumpyRNG()
        indices = rng.permutation(
            numpy.arange(len(self), dtype=numpy.int32))[0:n]
        return PopulationView(
            self, indices,
            label=f"Random sample size {n} from {self.label}")

    def set(self, **parameters: Values) -> None:
        """
        Set one or more parameters for every cell in the population.
        Values passed to `set()` may be:

        * single values,
        * :py:class:`~spynnaker.pyNN.RandomDistribution` objects, or
        * lists / arrays of values of the same size as the population
          mapping functions, where a mapping function accepts a single
          argument (the cell index) and returns a single value.

        Here, a "single value" may be either a single number or a list /
        array of numbers (e.g. for spike times).

        Values should be expressed in the standard PyNN units (i.e.
        millivolts, nanoamps, milliseconds, microsiemens, nanofarads,
        event per second).

        Examples::

            p.set(tau_m=20.0, v_rest=-65).
            p.set(spike_times=[0.3, 0.7, 0.9, 1.4])
            p.set(cm=rand_distr, tau_m=lambda i: 10 + i / 10.0)
        """
        for (parameter, value) in parameters.items():
            self.__vertex.set_parameter_values(
                parameter, value, self.__indexes)

    @overrides(PopulationBase.write_data)
    def write_data(self, io: Union[str, neo.baseio.BaseIO],
                   variables: Names = 'all',
                   gather: bool = True, clear: bool = False,
                   annotations: Optional[Dict[str, Any]] = None) -> None:
        if not gather:
            logger.warning("SpiNNaker only supports gather=True. We will run "
                           "as if gather was set to True.")
        if isinstance(io, str):
            extension = os.path.splitext(io)[1][1:]
            if extension == "csv":
                self.__recorder.write_data(
                    io, variables, view_indexes=self.__indexes,
                    annotations=annotations)
                return
            io = get_neo_io(io)

        data = self.__recorder.extract_neo_block(
            variables, self.__indexes, clear, annotations)

        # write the neo block to the file
        io.write(data)

    @property
    @overrides(PopulationBase._vertex)
    def _vertex(self) -> PopulationApplicationVertex:
        return self.__vertex

    @property
    @overrides(PopulationBase._recorder)
    def _recorder(self) -> Recorder:
        return self.__recorder

    @property
    @overrides(PopulationBase._view_range)
    def _view_range(self) -> Tuple[int, int]:
        indices = self.__indexes
        return indices[0], indices[-1]

    @property
    def _is_contiguous(self) -> bool:
        cont = range(self.__indexes[0], self.__indexes[-1] + 1)
        # self.__indexes is likely a range too so test direct first
        if self.__indexes == cont:
            return True
        return tuple(self.__indexes) == tuple(cont)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PopulationView):
            return False
        return (self.__vertex == other._vertex and
                self._indexes == other._indexes)

    def __str__(self) -> str:
        return str(self.__vertex) + str(self.__indexes)

    def __repr__(self) -> str:
        return repr(self.__vertex) + str(self.__indexes)


class IDMixin(PopulationView):
    """
    Implementation of PyNN IDMixin.
    """
    __slots__ = ()

    def get_parameters(self) -> ParameterHolder:
        """
        :returns: A dict of all cell parameters.
        """
        return self._vertex.get_parameter_values(
            self._vertex.get_parameters(), self.id)

    # NON-PYNN API CALLS
    @property
    def id(self) -> int:
        """
        The lowest index in this view
        """
        return self._indexes[0]

    def __getattr__(self, name: str) -> ParameterHolder:
        if name == "_vertex":
            raise KeyError("Shouldn't come through here!")
        return self._vertex.get_parameter_values(name, self.id)

    def __setattr__(self, name: str, value: Values) -> None:
        if name in self.__realslots__:
            object.__setattr__(self, name, value)
            return
        return self._vertex.set_parameter_values(name, value, self.id)

    def get_initial_value(self, variable: str) -> ParameterHolder:
        """
        Get the initial value of a state variable of the cell.

        :param variable: The name of the variable
        :returns: The initial value for this variable
        """
        return self._vertex.get_initial_state_values(variable, self.id)

    @property
    def initial_values(self) -> ParameterHolder:
        return self._vertex.get_initial_state_values(
            self._vertex.get_state_variables(), self.id)

    def set_initial_value(self, variable: str, value: Values) -> None:
        """
        Set the initial value of a state variable of the cell.

        :param variable: The name of the variable
        :param value: The value of the variable
        """
        self._vertex.set_initial_state_values(variable, value, self.id)

    def set_parameters(self, **parameters: Values) -> None:
        """
        Set cell parameters, given as a sequence of parameter=value arguments.
        """
        for (name, value) in parameters.items():
            self._vertex.set_parameter_values(name, value, self.id)

    def as_view(self) -> PopulationView:
        """
        :returns: A PopulationView containing just this cell.
        """
        return self

    @property
    def local(self) -> bool:
        """
        Whether this cell is local to the current MPI node.
        """
        # There are no MPI nodes!
        return True

    @property
    @overrides(PopulationBase.positions)
    def positions(self) -> NDArray[numpy.floating]:
        raise NotImplementedError("Not implemented for IDMixin")

    @property
    @overrides(PopulationBase.position_generator)
    def position_generator(self) -> Callable[[int], NDArray[numpy.floating]]:
        raise NotImplementedError("Not implemented for IDMixin")

    @property
    @overrides(PopulationBase.structure)
    def structure(self) -> Optional[BaseStructure]:
        raise NotImplementedError("Not implemented for IDMixin")
