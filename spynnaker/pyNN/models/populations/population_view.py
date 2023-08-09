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
import numpy
from numpy import bool_, integer
from numpy.typing import NDArray
import os
from typing import (
    Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union,
    overload, TYPE_CHECKING)
from typing_extensions import TypeAlias
from spinn_utilities.log import FormatAdapter
from pyNN import descriptions
from pyNN.random import NumpyRNG
import neo  # type: ignore[import]
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.ranged.abstract_sized import AbstractSized
from .population_base import PopulationBase
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from spynnaker.pyNN.utilities.utility_calls import get_neo_io
if TYPE_CHECKING:
    from .population import Population
    from spynnaker.pyNN.models.current_sources import AbstractCurrentSource
    from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
    from spynnaker.pyNN.models.common.population_application_vertex import (
        PopulationApplicationVertex)
    from spynnaker.pyNN.models.common import ParameterHolder
    from spynnaker.pyNN.models.common.types import Names, Values
    from spynnaker.pyNN.models.recorder import Recorder
    #: :meta private:
    Selector: TypeAlias = Union[
        None, int, slice, List[int], List[bool], NDArray[bool_],
        NDArray[integer]]

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
        :type parent: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
        :param PopulationApplicationVertex vertex: The actual underlying vertex
        :param Recorder recorder: The recorder of the Population
        :param selector: a slice or numpy mask array.
            The mask array should either be a boolean array (ideally) of the
            same size as the parent,
            or an integer array containing cell indices,
            i.e. if `p.size == 5` then:

            ::

                PopulationView(p, array([False, False, True, False, True]))
                PopulationView(p, array([2, 4]))
                PopulationView(p, slice(2, 5, 2))

            will all create the same view.
        :type selector: None or slice or int or list(bool) or list(int) or
            ~numpy.ndarray(bool) or ~numpy.ndarray(int)
        :param str label: A label for the view
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
        self.__label = label
        self.__annotations: Dict[str, Any] = dict()

        # Get these two objects to make access easier
        # pylint: disable=protected-access
        self.__vertex = self.__population._vertex
        # pylint: disable=protected-access
        self.__recorder = self.__population._recorder

    def __getattr__(self, name: str) -> ParameterHolder:
        return self.__vertex.get_parameter_values(name, self.__indexes)

    def __setattr__(self, name: str, value):
        if name in self.__realslots__:
            object.__setattr__(self, name, value)
            return
        return self.__vertex.set_parameter_values(name, value, self.__indexes)

    @property
    def size(self) -> int:
        """
        The total number of neurons in the Population View.

        :rtype: int
        """
        return len(self.__indexes)

    @property
    def label(self) -> Optional[str]:
        """
        A label for the Population View.

        :rtype: str
        """
        return self.__label

    @property
    def celltype(self) -> AbstractPyNNModel:
        """
        The type of neurons making up the underlying Population.

        :rtype: AbstractPyNNModel
        """
        return self.__parent.celltype

    @property
    def initial_values(self) -> ParameterHolder:
        """
        A dict containing the initial values of the state variables.

        :rtype: InitialValuesHolder
        """
        return self.__vertex.get_initial_state_values(
            self.__vertex.get_state_variables(), self.__indexes)

    @property
    def current_values(self) -> ParameterHolder:
        """
        A dict containing the current values of the state variables.

        :rtype: InitialValuesHolder
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

        :rtype: ~spynnaker.pyNN.models.populations.Population
        """
        return self.__parent

    @property
    def mask(self) -> Selector:
        """
        The selector mask that was used to create this view.

        :rtype: None or slice or int or list(bool) or list(int) or
            ~numpy.ndarray(bool) or ~numpy.ndarray(int)
        """
        return self.__mask

    @property
    def all_cells(self) -> Sequence['IDMixin']:
        """
        An array containing the cell IDs of all neurons in the
        Population (all MPI nodes).

        :rtype: list(IDMixin)
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

    def __getitem__(self, index):
        """
        Return either a single cell (ID object) from the Population,
        if index is an integer, or a subset of the cells
        (PopulationView object), if index is a slice or array.

        .. note::
            ``__getitem__`` is called when using[] access, e.g. if
            ``p = Population(...)`` then
            ``p[2]`` is equivalent to ``p.__getitem__(2)``, and
            ``p[3:6]`` is equivalent to ``p.__getitem__(slice(3, 6))``

        :rtype: IDMixin or ~.PopulationView
        """
        if isinstance(index, int):
            return IDMixin(self.__population, index)
        return PopulationView(self, index, label=self.label + "_" + str(index))

    def __iter__(self) -> Iterator['IDMixin']:
        """
        Iterator over cell IDs (on the local node).

        :rtype: iterable(IDMixin)
        """
        for idx in self.__indexes:
            yield IDMixin(self.__population, idx)

    def __len__(self) -> int:
        """
        Return the total number of cells in the population (all nodes).

        :rtype: int
        """
        return len(self.__indexes)

    def all(self) -> Iterable['IDMixin']:
        """
        Iterator over cell IDs (on all MPI nodes).

        :rtype: iterable(IDMixin)
        """
        for idx in self.__indexes:
            yield IDMixin(self.__population, idx)

    def can_record(self, variable: str) -> bool:
        """
        Determine whether variable can be recorded from this population.

        :rtype: bool
        """
        return variable in self.__vertex.get_recordable_variables()

    @property
    def conductance_based(self) -> bool:
        """
        Whether the post-synaptic response is modelled as a
        change in conductance or a change in current.

        :rtype: bool
        """
        return self.__vertex.conductance_based

    def inject(self, current_source: AbstractCurrentSource):
        """
        Injects the specified current_source into this PopulationView.

        :param AbstractCurrentSource current_source:
            the current source to be injected
        """
        self.__vertex.inject(current_source, self.__indexes)

    def describe(self, template='populationview_default.txt',
                 engine='default'):
        """
        Returns a human-readable description of the population view.

        The output may be customized by specifying a different template
        together with an associated template engine (see pyNN.descriptions).

        If template is ``None``, then a dictionary containing the template
        context will be returned.

        :param str template: Template filename
        :param engine: Template substitution engine
        :type engine: str or ~pyNN.descriptions.TemplateEngine or None
        :rtype: str or dict
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

        :param str variable: The name of the variable
        :return: The units of the variable
        :rtype: str
        """
        return self.__vertex.get_units(variable)

    def get(self, parameter_names: Names,
            gather=False, simplify=True) -> ParameterHolder:
        """
        Get the values of the given parameters for every local cell in the
        population, or, if ``gather=True``, for all cells in the population.

        Values will be expressed in the standard PyNN units (i.e. millivolts,
        nanoamps, milliseconds, microsiemens, nanofarads, event per second).

        .. note::
            SpiNNaker always gathers.

        :param parameter_names:
        :type parameter_names: str or list(str)
        :param bool gather:
        :param bool simplify:
        :rtype: ParameterHolder
        """
        if not gather:
            logger.warning("SpiNNaker only supports gather=True. We will run "
                           "as if gather was set to True.")
        if simplify is not True:
            logger.warning("The simplify value is ignored if not set to true")

        return self.__vertex.get_parameter_values(
            parameter_names, self.__indexes)

    def get_data(
            self, variables: Names = 'all',
            gather=True, clear: bool = False, *,
            annotations: Optional[Dict[str, Any]] = None) -> neo.Block:
        """
        Return a Neo Block containing the data(spikes, state variables)
        recorded from the Population.

        :param variables: Either a single variable name or a list of variable
            names. Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :type variables: str or list(str)
        :param bool gather: For parallel simulators, if gather is True, all
            data will be gathered to all nodes and the Neo Block will contain
            data from all nodes.
            Otherwise, the Neo Block will contain only data from the cells
            simulated on the local node.

            .. note::
                SpiNNaker always gathers.

        :param bool clear:
            If True, recorded data will be deleted from the Population.
        :param annotations: annotations to put on the neo block
        :type annotations: dict(str, ...)
        :rtype: ~neo.core.Block
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
        Public accessor for getting data as a numpy array, instead of
        the Neo-based object

        :param str variable: a single variable name
        :param bool as_matrix: If set True the data is returned as a 2d matrix
        :return: array of the data
        :rtype: ~numpy.ndarray
        """
        return self.__population.spinnaker_get_data(
            variable, as_matrix, self.__indexes)

    def get_spike_counts(self, gather=True) -> Dict[int, int]:
        """
        Returns a dict containing the number of spikes for each neuron.

        The dict keys are neuron IDs, not indices.

        .. note::
            Implementation of this method is different to Population as the
            Populations uses PyNN 7 version of the ``get_spikes`` method which
            does not support indexes.

        :param bool gather:
            .. note::
                SpiNNaker always gathers.

        :rtype: dict(int,int)
        """
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

        :rtype: ~spynnaker.pyNN.models.populations.Population
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

    def id_to_index(self, id):  # pylint: disable=redefined-builtin
        """
        Given the ID(s) of cell(s) in the PopulationView, return its /
        their index / indices(order in the PopulationView).

        assert pv.id_to_index(pv[3]) == 3

        :param id:
        :type id: int or list(int)
        :rtype: int or list(int)
        """
        if isinstance(id, int):
            return self.__indexes.index(id)
        return [self.__indexes.index(idx) for idx in id]

    def index_in_grandparent(self, indices: Iterable[int]) -> List[int]:
        """
        Given an array of indices, return the indices in the parent
        population at the root of the tree.

        :param list(int) indices:
        :rtype: list(int)
        """
        return [self.__indexes[index] for index in indices]

    def initialize(self, **initial_values: Values):
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

    def set_state(self, **initial_values: Values):
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

    def record(self, variables: Names,
               to_file: Union[None, str, neo.baseio.BaseIO] = None,
               sampling_interval: Optional[int] = None):
        # Type is technically wrong, but neo internals are awful
        """
        Record the specified variable or variables for all cells in the
        Population or view.

        :param variables: either a single variable name, or a list of variable
            names, or ``all`` to record everything. For a given `celltype`
            class, `celltype.recordable` contains a
            list of variables that can be recorded for that `celltype`.
        :type variables: str or list(str)
        :param to_file:
            If specified, should be a Neo IO instance and
            :py:meth:`write_data`
            will be automatically called when `sim.end()` is called.
        :type to_file: ~neo.io or ~neo.rawio or str
        :param int sampling_interval:
            should be a value in milliseconds, and an integer multiple of the
            simulation timestep.
        """
        self.__recorder.record(
            variables, to_file, sampling_interval, self.__indexes)

    def sample(
            self, n: int, rng: Optional[NumpyRNG] = None) -> 'PopulationView':
        """
        Randomly sample `n` cells from the Population view, and return a
        new PopulationView object.

        :param int n: The number of cells to select
        :param ~pyNN.random.NumpyRNG rng: Random number generator
        :rtype: ~spynnaker.pyNN.models.populations.PopulationView
        """
        if not rng:
            rng = NumpyRNG()
        indices = rng.permutation(
            numpy.arange(len(self), dtype=numpy.int32))[0:n]
        return PopulationView(
            self, indices,
            label=f"Random sample size {n} from {self.label}")

    def set(self, **parameters: Values):
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

    def write_data(self, io: Union[str, neo.baseio.BaseIO],
                   variables: Names = 'all',
                   gather=True, clear: bool = False,
                   annotations: Optional[Dict[str, Any]] = None):
        """
        Write recorded data to file, using one of the file formats
        supported by Neo.

        :param io: a Neo IO instance or the name of a file to write
        :type io: neo.io.BaseIO or str
        :param variables: either a single variable name or a list of variable
            names. These must have been previously recorded, otherwise an
            Exception will be raised.
        :type variables: str or list(str)
        :param bool gather: For parallel simulators, if this is True, all
            data will be gathered to the master node and a single output file
            created there. Otherwise, a file will be written on each node,
            containing only data from the cells simulated on that node.

            .. note::
                SpiNNaker always gathers.

        :param bool clear:
            If this is True, recorded data will be deleted from the Population.
        :param annotations: should be a dict containing simple data types such
            as numbers and strings. The contents will be written into the
            output data file as metadata.
        :type annotations: dict(str, ...)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the variable or variables have not been previously set to
            record.
        """
        if not gather:
            logger.warning("SpiNNaker only supports gather=True. We will run "
                           "as if gather was set to True.")
        if isinstance(io, str):
            extension = os.path.splitext(io)[1][1:]
            if extension == "csv":
                self.__recorder.csv_neo_block(
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

    def __eq__(self, other) -> bool:
        if not isinstance(other, PopulationView):
            return False
        return (self.__vertex == other._vertex and
                self._indexes == other._indexes)

    def __str__(self) -> str:
        return str(self.__vertex) + str(self.__indexes)

    def __repr__(self):
        return repr(self.__vertex) + str(self.__indexes)


class IDMixin(PopulationView):
    __slots__ = ()

    def get_parameters(self) -> ParameterHolder:
        """
        Return a dict of all cell parameters.

        :rtype: dict(str, ...)
        """
        return self._vertex.get_parameter_values(
            self._vertex.get_parameters(), self.id)

    # NON-PYNN API CALLS
    @property
    def id(self) -> int:
        """
        :rtype: int
        """
        return self._indexes[0]

    def __getattr__(self, name: str) -> ParameterHolder:
        if name == "_vertex":
            raise KeyError("Shouldn't come through here!")
        return self._vertex.get_parameter_values(name, self.id)

    def __setattr__(self, name: str, value):
        if name in self.__realslots__:
            object.__setattr__(self, name, value)
            return
        return self._vertex.set_parameter_values(name, value, self.id)

    def get_initial_value(self, variable: str):
        """
        Get the initial value of a state variable of the cell.

        :param str variable: The name of the variable
        :rtype: float
        """
        return self._vertex.get_initial_state_values(variable, self.id)

    @property
    def initial_values(self) -> ParameterHolder:
        return self._vertex.get_initial_state_values(
            self._vertex.get_state_variables(), self.id)

    def set_initial_value(self, variable: str, value: Values):
        """
        Set the initial value of a state variable of the cell.

        :param str variable: The name of the variable
        :param float value: The value of the variable
        """
        self._vertex.set_initial_state_values(variable, value, self.id)

    def set_parameters(self, **parameters: Values):
        """
        Set cell parameters, given as a sequence of parameter=value arguments.
        """
        for (name, value) in parameters.items():
            self._vertex.set_parameter_values(name, value, self.id)

    def as_view(self) -> PopulationView:
        """
        Return a PopulationView containing just this cell.

        :rtype: ~spynnaker.pyNN.models.populations.PopulationView
        """
        return self

    @property
    def local(self) -> bool:
        """
        Whether this cell is local to the current MPI node.

        :rtype: bool
        """
        # There are no MPI nodes!
        return True
