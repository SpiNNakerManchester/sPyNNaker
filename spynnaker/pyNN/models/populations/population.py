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
import inspect
import logging
import os
from typing import (
    Any, Callable, cast, Dict, final, Iterable, Iterator, List, Optional,
    overload, Sequence, Tuple, Type, TYPE_CHECKING, Union)

import numpy
from numpy import floating
from numpy.typing import NDArray
from typing_extensions import Never, TypeAlias

import neo
from neo.io.baseio import BaseIO  # type: ignore[import]
from pyNN.descriptions import TemplateEngine
from pyNN import descriptions
from pyNN.random import NumpyRNG
from pyNN.space import BaseStructure

from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.overrides import overrides

from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.abstract_models import SupportsStructure
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.models.recorder import Recorder
from spynnaker.pyNN.types import IoDest
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase
from spynnaker.pyNN.types import Selector
from spynnaker.pyNN.utilities.utility_calls import get_neo_io

from .population_base import PopulationBase
from .population_view import PopulationView, IDMixin

if TYPE_CHECKING:
    from pyNN.neuron.standardmodels.electrodes import NeuronCurrentSource
    from spynnaker.pyNN.models.common.types import Names, Values
    from spynnaker.pyNN.models.common.parameter_holder import ParameterHolder
    __Values: TypeAlias = Values  # Stupid PyDev!

logger = FormatAdapter(logging.getLogger(__file__))
_CellType: TypeAlias = Union[AbstractPyNNModel, PopulationApplicationVertex]
_CellTypeArg: TypeAlias = Union[Type[AbstractPyNNModel], _CellType]
_ParamDict: TypeAlias = Dict[str, Any]


class Population(PopulationBase):
    """
    PyNN population object.
    """
    # pylint: disable=redefined-builtin
    __slots__ = (
        "__annotations",
        "__celltype",
        "__first_id",
        "__last_id",
        "__positions",
        "__recorder",
        "__size",
        "__structure",
        "__vertex")

    def __init__(
            self, size: Union[int, float, None], cellclass: _CellTypeArg,
            cellparams: Optional[_ParamDict] = None,
            structure: Optional[BaseStructure] = None,
            initial_values: Optional[Dict[str, float]] = None,
            label: Optional[str] = None,
            additional_parameters: Optional[_ParamDict] = None,
            **additional_kwargs: _ParamDict):
        """
        :param size: The number of neurons in the population
        :param cellclass: The implementation of the individual neurons.
        :param cellparams: Parameters to pass to ``cellclass`` if it
            is a class to instantiate. Must be ``None`` if ``cellclass`` is an
            instantiated object.
        :param structure:
        :param initial_values: Initial values of state variables
        :param label: A label for the population
        :param additional_parameters:
            Additional parameters to pass to the vertex creation function.
        :param additional_kwargs:
            A nicer way of allowing additional things
        """
        # Deal with the kwargs!
        additional: _ParamDict = dict()
        if additional_parameters is not None:
            additional.update(additional_parameters)
        if additional_kwargs:
            additional.update(additional_kwargs)

        # build our initial objects
        self.__celltype: AbstractPyNNModel
        self.__vertex: PopulationApplicationVertex
        model = self.__create_model(cellclass, cellparams)
        realsize = self.__roundsize(size, label)
        self.__create_vertex(model, realsize, label, additional)
        self.__recorder = Recorder(population=self, vertex=self.__vertex)

        # structure should be a valid Space.py structure type.
        # generation of positions is deferred until needed.
        self.__structure = structure
        self.__positions: Optional[numpy.ndarray] = None
        if isinstance(self.__vertex, SupportsStructure):
            self.__vertex.set_structure(structure)

        # add objects to the SpiNNaker control class
        SpynnakerDataView.add_vertex(self.__vertex)

        # initialise common stuff
        if realsize is None:
            realsize = self.__vertex.n_atoms
        self.__size = realsize
        self.__annotations: Dict[str, Any] = dict()

        # things for pynn demands
        self.__first_id, self.__last_id = SpynnakerDataView.add_population(
            self)

        # set up initial values if given
        if initial_values:
            for variable, value in initial_values.items():
                self.__vertex.set_initial_state_values(variable, value)

    def __iter__(self) -> Iterator[PopulationView]:
        """
        Iterate over local cells.
        """
        for _id in range(self.__size):
            yield IDMixin(self, _id)

    def __getitem__(self, index_or_slice: Selector) -> PopulationView:
        if isinstance(index_or_slice, int):
            return IDMixin(self, index_or_slice)
        else:
            return PopulationView(self, index_or_slice)

    def all(self) -> Iterator[PopulationView]:
        """
        :returns: Iterator over cell IDs on all MPI nodes.
        """
        for _id in range(self.__size):
            yield IDMixin(self, _id)

    @property
    def annotations(self) -> Dict[str, Any]:
        """
        The annotations given by the end user.
        """
        return self.__annotations

    @property
    def celltype(self) -> AbstractPyNNModel:
        """
        The Model uses for this population.
        """
        return self.__celltype

    def can_record(self, variable: str) -> bool:
        """
        Determine whether `variable` can be recorded from this population.

        :param variable: The variable to answer the question about
        :returns: True if the variable can be recorded, False otherwise.
        """
        return variable in self.__vertex.get_recordable_variables()

    @overrides(PopulationBase.record)
    def record(self, variables: Names, to_file: IoDest = None,
               sampling_interval: Optional[int] = None) -> None:
        self.__recorder.record(
            variables, to_file, sampling_interval, indexes=None)

    def sample(self, n: int, rng: Optional[NumpyRNG] = None) -> PopulationView:
        """
        Randomly sample `n` cells from the Population, and return a
        PopulationView object.

        :param n: The number of cells to put in the view.
        :param rng: The random number generator to use
        :returns: A PopulationView over n random cells.
        """
        if not rng:
            rng = NumpyRNG()
        indices = rng.permutation(
            numpy.arange(len(self), dtype=numpy.int32))[0:n]
        return PopulationView(
            self, indices,
            label=f"Random sample size {n} from {self.label}")

    @overrides(PopulationBase.write_data)
    def write_data(self, io: Union[str, BaseIO], variables: Names = 'all',
                   gather: bool = True, clear: bool = False,
                   annotations: Optional[Dict[str, Any]] = None) -> None:
        self._check_params(gather, annotations)

        if isinstance(io, str):
            extension = os.path.splitext(io)[1][1:]
            if extension == "csv":
                self.__recorder.write_data(
                    io, variables, annotations=annotations)
                return
            io = get_neo_io(io)

        data = self.__recorder.extract_neo_block(
            variables, None, clear, annotations)
        # write the neo block to the file
        io.write(data)

    def describe(self, template: str = 'population_default.txt',
                 engine:  Optional[Union[str, TemplateEngine]] = 'default'
                 ) -> Union[str, Dict[str, Any]]:
        """
        Returns a human-readable description of the population.

        The output may be customised by specifying a different template
        together with an associated template engine (see
        :mod:`pyNN.descriptions`).

        If ``template`` is ``None``, then a dictionary containing the template
        context will be returned.

        :param template: Template filename
        :param engine: Template substitution engine
        :returns: Human-readable description as a string or dict
        """
        context: Dict[str, Any] = {
            "label": self.label,
            "celltype": self.celltype.describe(template=None),
            "structure": None,
            "size": self.size,
            "size_local": self.size,
            "first_id": self.first_id,
            "last_id": self.last_id,
        }
        context.update(self.annotations)
        if self.size > 0:
            parameters = self.__vertex.get_parameters()
            cell_parameters: Union[str, ParameterHolder]
            if parameters:
                cell_parameters = self.__vertex.get_parameter_values(
                    parameters, 0)
            else:
                cell_parameters = "No cell parameters"
            context.update({
                "local_first_id": 0,
                "cell_parameters": cell_parameters
            })
        if self.structure:
            context["structure"] = self.structure.describe(template=None)
        return descriptions.render(engine, template, context)

    def _end(self) -> None:
        """
        Do final steps at the end of the simulation.
        """
        for variable in self.__recorder.write_to_files_indicators:
            if self.__recorder.write_to_files_indicators[variable]:
                self.write_data(
                    io=self.__recorder.write_to_files_indicators[variable],
                    variables=[variable])

    @overrides(PopulationBase.get_data)
    def get_data(
            self, variables: Names = 'all',
            gather: bool = True, clear: bool = False, *,
            annotations: Optional[Dict[str, Any]] = None) -> neo.Block:
        self._check_params(gather, annotations)
        return self.__recorder.extract_neo_block(
            variables, None, clear, annotations)

    def spinnaker_get_data(
            self, variable: str, as_matrix: bool = False,
            view_indexes: Optional[Sequence[int]] = None) -> NDArray[floating]:
        """
        SsPyNNaker specific method for getting data as a numpy array,
        instead of the Neo-based object

        :param variable: a single variable name.
        :param as_matrix: If set True the data is returned as a 2d matrix
        :param view_indexes: The indexes for which data should be returned.
            If ``None``, all data (view_index = data_indexes)
        :return: array of the data
        """
        warn_once(
            logger, "spinnaker_get_data is non-standard PyNN and therefore "
            "will not be portable to other simulators.")
        with NeoBufferDatabase() as db:
            return db.spinnaker_get_data(self.__recorder.recording_label,
                                         variable, as_matrix, view_indexes)

    @overrides(PopulationBase.get_spike_counts)
    def get_spike_counts(self, gather: bool = True) -> Dict[int, int]:
        self._check_params(gather)
        with NeoBufferDatabase() as db:
            return db.get_spike_counts(self.__recorder.recording_label)

    def find_units(self, variable: str) -> str:
        """
        Get the units of a variable.

        :param variable: The name of the variable
        :return: The units of the variable
        """
        return self.__vertex.get_units(variable)

    def set(self, **parameters: Values) -> None:
        """
        Set one or more parameters for every cell in the population.
        For example::

            p.set(tau_m=20.0).

        :param parameters:
            The parameters to set and the values to set them to.
            The type of each parameter depends on the parameter; it's often a
            float, but not always.
        :raises SimulatorRunningException: If `sim.run` is currently running
        :raises SimulatorNotSetupException: If called before `sim.setup`
        :raises SimulatorShutdownException: If called after `sim.end`
        """
        SpynnakerDataView.check_user_can_act()
        for parameter, value in parameters.items():
            self.__vertex.set_parameter_values(parameter, value)

    def initialize(self, **kwargs: Values) -> None:
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
        event per second).

        Examples::

            p.initialize(v=-70.0)
            p.initialize(v=rand_distr, gsyn_exc=0.0)
            p.initialize(v=lambda i: -65 + i / 10.0)
        """
        SpynnakerDataView.check_user_can_act()
        if SpynnakerDataView.is_ran_last():
            warn_once(
                logger, "Calling initialize without reset will have no effect."
                " If you want to set the current value of a state variable"
                " consider calling the non-PyNN function set_state instead.")
        for variable, value in kwargs.items():
            self.__vertex.set_initial_state_values(variable, value)

    @property
    def initial_values(self) -> ParameterHolder:
        """
        The initial values of the state variables.

        .. note::
            These values will be the same as the values set with the last call
            to initialize rather than the actual initial values if this call
            has been made.
        """
        SpynnakerDataView.check_user_can_act()
        return self.__vertex.get_initial_state_values(
            self.__vertex.get_state_variables())

    def set_state(self, **kwargs: Values) -> None:
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
        event per second).

        Examples::

            p.set_state(v=-70.0)
            p.set_state(v=rand_distr, gsyn_exc=0.0)
            p.set_state(v=lambda i: -65 + i / 10.0)
        """
        SpynnakerDataView.check_user_can_act()
        warn_once(
            logger, "set_state is non-standard PyNN and therefore "
            "will not be portable to other simulators.")
        for variable, value in kwargs.items():
            self.__vertex.set_current_state_values(variable, value)

    @property
    def current_values(self) -> ParameterHolder:
        """
        Get the current values of the state variables.
        """
        SpynnakerDataView.check_user_can_act()
        warn_once(
            logger, "current_values is non-standard PyNN and therefore "
            "will not be portable to other simulators.")
        return self.__vertex.get_current_state_values(
            self.__vertex.get_state_variables())

    @property
    @overrides(PopulationBase.positions)
    def positions(self) -> NDArray[floating]:
        if self.__positions is None:
            if self.__structure is None:
                raise ValueError("attempted to retrieve positions "
                                 "for an unstructured population")
            self.__positions = self.__structure.generate_positions(
                self.__vertex.n_atoms)
        return self.__positions.T

    @positions.setter
    def positions(self, positions: NDArray[numpy.floating]) -> None:
        """
        Sets all the positions in the population.
        """
        self.__positions = positions

    @property
    @overrides(PopulationBase.all_cells)
    def all_cells(self) -> List[IDMixin]:
        return [IDMixin(self, _id) for _id in range(self.__size)]

    @property
    @overrides(PopulationBase.position_generator)
    def position_generator(self) -> Callable[[int], NDArray[numpy.floating]]:
        return lambda i: self.positions[:, i]

    @property
    def first_id(self) -> int:
        """
        The ID of the first member of the population.
        """
        return self.__first_id

    @property
    def last_id(self) -> int:
        """
        The ID of the last member of the population.
        """
        return self.__last_id

    @property
    @overrides(PopulationBase._vertex)
    def _vertex(self) -> PopulationApplicationVertex:
        return self.__vertex

    @property
    def _recorder(self) -> Recorder:
        return self.__recorder

    @property
    @overrides(PopulationBase._view_range)
    def _view_range(self) -> Tuple[int, int]:
        return 0, self.size - 1

    @property
    def conductance_based(self) -> bool:
        """
        Whether the population uses conductance inputs
        """
        return self.__vertex.conductance_based

    def get(self, parameter_names: Names,
            gather: bool = True, simplify: bool = True) -> ParameterHolder:
        """
        Get the values of a parameter for every local cell in the population.

        :param parameter_names: Name of parameter. This is either a single
            string or a list of strings
        :param gather: Ignored. Purely for PyNN compatibility
        :param simplify: Ignored. Purely for PyNN compatibility
        :return: A single list of values (or possibly a single value) if
            paramter_names is a string, or a dict of these if parameter names
            is a list.
        """
        self._check_params(gather)
        if simplify is not True:
            warn_once(
                logger, "The simplify value is ignored if not set to true")

        return self.__vertex.get_parameter_values(parameter_names)

    @overload
    def id_to_index(self, id: int) -> int:  # @ReservedAssignment
        ...

    @overload
    def id_to_index(
            self, id: Iterable[int]) -> List[int]:  # @ReservedAssignment
        ...

    def id_to_index(self, id: Union[int, Iterable[int]]
                    ) -> Union[int, List[int]]:  # @ReservedAssignment
        """
        Given the ID(s) of cell(s) in the Population, return its (their)
        index (order in the Population).

        Defined by
        https://neuralensemble.org/docs/PyNN/reference/populations.html

        :param id:
        :returns: Index of cell(s) in the Population
        """
        # pylint: disable=redefined-builtin
        if not numpy.iterable(id):
            id = cast(int, id)
            if not self.__first_id <= id <= self.__last_id:
                raise ValueError(
                    f"id should be in the range [{self.__first_id},"
                    f"{self.__last_id}], actually {id}")
            return int(id - self.__first_id)  # assume IDs are consecutive
        return [_id - self.__first_id for _id in id]

    @overload
    def index_to_id(self, index: int) -> int:
        ...

    @overload
    def index_to_id(self, index: Iterable[int]) -> List[int]:
        ...

    def index_to_id(self, index: Union[int, Iterable[int]]
                    ) -> Union[int, List[int]]:
        """
        Given the index (order in the Population) of cell(s) in the
        Population, return their ID(s)

        :param index:
        :returns: The ID(s) of the cell(s) in the Population
        """
        if not numpy.iterable(index):
            index = cast(int, index)
            if index > self.__last_id - self.__first_id:
                raise ValueError(
                    "indexes should be in the range [0,"
                    f"{self.__last_id - self.__first_id}], actually {index}")
            return int(index + self.__first_id)
        # this assumes IDs are consecutive
        return [_index + self.__first_id for _index in index]

    def id_to_local_index(self, cell_id: Union[int, Iterable[int]]) -> Never:
        """
        Given the ID(s) of cell(s) in the Population, return its (their)
        index (order in the Population), counting only cells on the local
        MPI node.

        Defined by
        https://neuralensemble.org/docs/PyNN/reference/populations.html

        :param cell_id:
        """
        raise NotImplementedError(
            "sPyNNaker does not currently do id_to_local_index")

    @overrides(PopulationBase.inject)
    def inject(self, current_source: NeuronCurrentSource) -> None:
        """
        Connect a current source to all cells in the Population.

        Defined by
        https://neuralensemble.org/docs/PyNN/reference/populations.html
        """
        # Pass this into the vertex
        self.__vertex.inject(current_source, [n for n in range(self.__size)])

    def __len__(self) -> int:
        """
        Get the total number of cells in the population.
        """
        return self.__size

    @property
    def label(self) -> str:
        """
        The label of the population.
        """
        return self.__vertex.label or ""  # Should never be empty

    @label.setter
    def label(self, label: str) -> Never:
        raise NotImplementedError(
            "As label is used as an ID it can not be changed")

    @property
    @overrides(PopulationBase.structure)
    def structure(self) -> Optional[BaseStructure]:
        """
        The structure for the population.
        """
        return self.__structure

    # NON-PYNN API CALL
    def add_placement_constraint(
            self, x: int, y: int, p: Optional[int] = None) -> None:
        """
        Add a placement constraint.

        :param x: The x-coordinate of the placement constraint
        :param y: The y-coordinate of the placement constraint
        :param p: The processor ID of the placement constraint (optional)
        :raises SimulatorRunningException: If `sim.run` is currently running
        :raises SimulatorNotSetupException: If called before `sim.setup`
        :raises SimulatorShutdownException: If called after `sim.end`
        """
        self.__vertex.set_fixed_location(x, y, p)

    # NON-PYNN API CALL
    def set_max_atoms_per_core(
            self, max_atoms_per_core: Union[int, Tuple[int, ...]]) -> None:
        """
        Supports the setting of this population's max atoms per
        dimension per core.

        :param max_atoms_per_core:
            the new value for the max atoms per dimension per core.
        :raises SimulatorRunningException: If `sim.run` is currently running
        :raises SimulatorNotSetupException: If called before `sim.setup`
        :raises SimulatorShutdownException: If called after `sim.end`
        """
        SpynnakerDataView.check_user_can_act()
        ct = self.celltype
        if isinstance(ct, AbstractPyNNModel):
            cap = ct.absolute_max_atoms_per_core
            if numpy.prod(max_atoms_per_core) > cap:
                raise SpynnakerException(
                    f"Set the max_atoms_per_core to {max_atoms_per_core} "
                    f"blocked as the current limit for the model is {cap}")
        self.__vertex.set_max_atoms_per_dimension_per_core(max_atoms_per_core)

    @property
    def size(self) -> int:
        """
        The number of neurons in the population.
        """
        return self.__vertex.n_atoms

    @staticmethod
    def __create_model(
            cell_class: _CellTypeArg,
            cell_params: Optional[_ParamDict]) -> _CellType:
        """
        :param cell_class: The implementation of the individual neurons.
        :param cell_params: Parameters to pass to ``cell_class`` if it
            is a class to instantiate. Must be ``None`` if ``cell_class`` is an
            instantiated object.
        """
        if inspect.isclass(cell_class):
            if cell_params is None:
                model = cell_class()
            else:
                model = cell_class(**cell_params)
            assert isinstance(model, (
                AbstractPyNNModel, PopulationApplicationVertex))
        elif cell_params:
            raise ConfigurationException(
                "cell_class is an instance which includes params so "
                "cell_params must be None")
        else:
            model = cell_class
        return model

    def __create_vertex_from_model(
            self, model: AbstractPyNNModel, size: Optional[int],
            label: Optional[str], additional_parameters: _ParamDict) -> None:
        """
        Worker for :meth:`__create_vertex` to handle the case where we really
        have a model.
        """
        self.__celltype = model
        # pylint: disable=protected-access
        if size is not None and size <= 0:
            raise ConfigurationException(
                "A population cannot have a negative or zero size.")
        parameters = model._get_default_population_parameters()
        if additional_parameters:
            # check that the additions are suitable. report wrong ones
            # and ignore
            parameters = self.__process_additional_params(
                additional_parameters, parameters)
        self.__vertex = model.create_vertex(
            size or 1, label or f"{model.name} vertex", **parameters)

    def __init_with_supplied_vertex(
            self, model: PopulationApplicationVertex, size: Optional[int],
            label: Optional[str], additional_parameters: _ParamDict) -> None:
        """
        Worker for :meth:`__create_vertex` to handle the case where we have a
        user-supplied vertex.
        """
        if additional_parameters:
            raise ConfigurationException(
                "Cannot accept additional parameters "
                f"{additional_parameters} when the cell is a vertex")
        # Use a synthetic model
        self.__celltype = _VertexHolder(model)
        self.__vertex = model
        if size is not None and size != self.__vertex.n_atoms:
            raise ConfigurationException(
                "Vertex size does not match Population size")
        if label is not None:
            self.__vertex.set_label(label)

    def __create_vertex(
            self, model: _CellType, size: Optional[int], label: Optional[str],
            additional_parameters: _ParamDict) -> None:
        """
        :param model: The implementation of the individual neurons.
        :param size:
        :param label:
        :param additional_parameters:
            Additional parameters to pass to the vertex creation function.
        """
        # Use a provided model to create a vertex
        if isinstance(model, AbstractPyNNModel):
            self.__create_vertex_from_model(
                model, size, label, additional_parameters)

        # Use a provided application vertex directly
        elif isinstance(model, PopulationApplicationVertex):
            self.__init_with_supplied_vertex(
                model, size, label, additional_parameters)

        # Fail on anything else
        else:
            raise ConfigurationException(
                "Model must be either an AbstractPyNNModel or a"
                " PopulationApplicationVertex")

    @staticmethod
    def create(
            cellclass: _CellTypeArg, cellparams: Optional[_ParamDict] = None,
            n: int = 1) -> 'Population':
        """
        Pass through method to the constructor defined by PyNN.
        Create ``n`` cells all of the same type.

        :param cellclass: see :py:meth:`~.Population.__init__`
        :param cellparams: see :py:meth:`~.Population.__init__`
        :param n: see :py:meth:`~.Population.__init__` (``size`` parameter)
        :return: A New Population
        """
        return Population(size=n, cellclass=cellclass, cellparams=cellparams)

    @staticmethod
    def __process_additional_params(
            additional_parameters: _ParamDict,
            population_parameters: _ParamDict) -> _ParamDict:
        """
        Essential method for allowing things like splitter objects at
        population level.

        :param additional_parameters:
            the additional parameters handed down from user
        :param population_parameters:
            the additional parameters the vertex can support.
        :return: the list of parameters that are accepted.
        """
        for key in additional_parameters.keys():
            if key in population_parameters:
                population_parameters[key] = additional_parameters[key]
            else:
                logger.warning("additional_parameter {} will be ignored", key)
        return population_parameters

    @staticmethod
    def __roundsize(
            size: Union[int, float, None],
            label: Optional[str]) -> Optional[int]:
        # External device population can have a size of None so accept for now
        if size is None or isinstance(size, int):
            return size
        # Allow a float which has a near int value
        temp = int(round(size))
        if abs(temp - size) < 0.001:
            logger.warning("Size of the population {} rounded "
                           "from {} to {}. Please use int values for size",
                           label, size, temp)
            return temp
        raise ConfigurationException(
            f"Size of a population with label {label} must be an int,"
            f" received {size}")


@final
class _VertexHolder(AbstractPyNNModel):
    """
    A simplistic model that just holds its supplied vertex.
    It has nothing to configure.
    """
    __slots__ = ("__vertex", )
    default_population_parameters = {}

    def __init__(self, vertex: PopulationApplicationVertex):
        """
        :param vertex: Vertex to hold and return
        """
        self.__vertex = vertex

    @property
    def vertex(self) -> PopulationApplicationVertex:
        """
        The vertex passed into the init.
        """
        return self.__vertex

    @overrides(AbstractPyNNModel.create_vertex)
    def create_vertex(
            self, n_neurons: int, label: str) -> PopulationApplicationVertex:
        # The parameters are ignored; the vertex already exists
        return self.__vertex
