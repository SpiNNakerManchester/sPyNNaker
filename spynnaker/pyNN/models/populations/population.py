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

import logging
import numpy
import neo
import inspect
from pyNN import descriptions
from pyNN.random import NumpyRNG
from spinn_utilities.log import FormatAdapter
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.overrides import overrides
from pacman.model.constraints import AbstractConstraint
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint)
from pacman.model.graphs.application import ApplicationVertex
from spinn_front_end_common.utilities.globals_variables import (
    get_simulator, get_not_running_simulator)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.models.abstract_models import (
    AbstractContainsUnits, AbstractReadParametersBeforeSet,
    AbstractPopulationInitializable, AbstractPopulationSettable)
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.recorder import Recorder
from spynnaker.pyNN.utilities.constants import SPIKES
from .idmixin import IDMixin
from .population_base import PopulationBase
from .population_view import PopulationView

logger = FormatAdapter(logging.getLogger(__file__))

REMOVED_V6 = "The method {} is not standard PyNN so has been permanently " \
      "removed. Use {} instead. " \
      "(Even this warning will be removed in version 7)"


# Not in the class so pylint doesn't get confused about abstractness of methods
def _we_dont_do_this_now(*args):  # pylint: disable=unused-argument
    # pragma: no cover
    raise NotImplementedError("sPyNNaker does not currently do this")


class Population(PopulationBase):
    """ PyNN 0.9 population object.
    """

    __slots__ = [
        "_all_ids",
        "_annotations",
        "_celltype",
        "__change_requires_mapping",
        "__delay_vertex",
        "__first_id",
        "__has_read_neuron_parameters_this_run",
        "__last_id",
        "_positions",
        "_recorder",
        "_size",
        "__structure",
        "__vertex",
        "__vertex_changeable_after_run",
        "__vertex_contains_units",
        "__vertex_population_initializable",
        "__vertex_population_settable"]

    def __init__(
            self, size, cellclass, cellparams=None, structure=None,
            initial_values=None, label=None, constraints=None,
            additional_parameters=None):
        """
        :param int size: The number of neurons in the population
        :param cellclass: The implementation of the individual neurons.
        :type cellclass: type or AbstractPyNNModel
        :param cellparams: Parameters to pass to ``cellclass`` if it
            is a class to instantiate. Must be ``None`` if ``cellclass`` is an
            instantiated object.
        :type cellparams: dict(str,object) or None
        :param ~pyNN.space.BaseStructure structure:
        :param dict(str,float) initial_values:
            Initial values of state variables
        :param str label: A label for the population
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Any constraints on how the population is deployed to SpiNNaker.
        :param additional_parameters:
            Additional parameters to pass to the vertex creation function.
        :type additional_parameters: dict(str, ...)
        """
        # pylint: disable=too-many-arguments

        # build our initial objects
        model = self.__create_model(cellclass, cellparams)
        size = self.__roundsize(size, label)
        self.__create_vertex(
            model, size, label, constraints, additional_parameters)
        self._recorder = Recorder(population=self, vertex=self.__vertex)

        self.__delay_vertex = None

        # Internal structure now supported 23 November 2014 ADR
        # structure should be a valid Space.py structure type.
        # generation of positions is deferred until needed.
        self.__structure = structure
        self._positions = None

        # add objects to the SpiNNaker control class
        sim = get_simulator()
        sim.add_population(self)
        sim.add_application_vertex(self.__vertex)

        # initialise common stuff
        if size is None:
            size = self.__vertex.n_atoms
        self._size = size
        self._annotations = dict()

        # parameter
        self.__change_requires_mapping = True
        self.__has_read_neuron_parameters_this_run = False

        # things for pynn demands
        self._all_ids = numpy.arange(sim.id_counter, sim.id_counter + size)
        self.__first_id = self._all_ids[0]
        self.__last_id = self._all_ids[-1]

        # update the simulators id_counter for giving a unique ID for every
        # atom
        sim.id_counter += size

        # set up initial values if given
        if initial_values:
            for variable, value in initial_values.items():
                self._initialize(variable, value)

    def __iter__(self):
        """ Iterate over local cells
        """
        for _id in range(self._size):
            yield IDMixin(self, _id)

    def __getitem__(self, index_or_slice):
        if isinstance(index_or_slice, int):
            return IDMixin(self, index_or_slice)
        else:
            return PopulationView(
                self, index_or_slice, label="view over {}".format(self.label))

    def all(self):
        """ Iterator over cell IDs on all MPI nodes.

        :rtype: iterable(IDMixin)
        """
        for _id in range(self._size):
            yield IDMixin(self, _id)

    @property
    def annotations(self):
        """ The annotations given by the end user

        :rtype: dict(str, ...)
        """
        return self._annotations

    @property
    def celltype(self):
        """ Implements the PyNN expected celltype property

        :return: The celltype this property has been set to
        :rtype: AbstractPyNNModel
        """
        return self._celltype

    def can_record(self, variable):
        """ Determine whether `variable` can be recorded from this population.

        :param str variable: The variable to answer the question about
        :rtype: bool
        """
        return variable in \
            self._recorder.get_all_possible_recordable_variables()

    @overrides(PopulationBase.record, extend_doc=False)
    def record(self, variables, to_file=None, sampling_interval=None):
        """ Record the specified variable or variables for all cells in the\
            Population or view.

        :param variables: either a single variable name or a list of variable
            names. For a given celltype class, ``celltype.recordable`` contains
            a list of variables that can be recorded for that celltype.
        :type variables: str or list(str)
        :param to_file: a file to automatically record to (optional).
            :py:meth:`write_data` will be automatically called when
            `sim.end()` is called.
        :type to_file: ~neo.io or ~neo.rawio or str
        :param int sampling_interval: a value in milliseconds, and an integer
            multiple of the simulation timestep.
        """
        self._recorder.record(
            variables, to_file, sampling_interval, indexes=None)

    def _record(
            self, variables, to_file, sampling_interval, indexes):
        """ Record the specified variable or variables for all cells in the\
            Population or view.

        :param variables: either a single variable name or a list of variable
            names. For a given celltype class, ``celltype.recordable`` contains
            a list of variables that can be recorded for that celltype.
            Can also be ``None`` to reset the list of variables.
        :type variables: str or list(str) or None
        :param to_file: a file to automatically record to (optional).
            :py:meth:`write_data` will be automatically called when
            `sim.end()` is called.
        :type to_file: ~neo.io or ~neo.rawio or str
        :param int sampling_interval: a value in milliseconds, and an integer
            multiple of the simulation timestep.
        :param indexes: The indexes of neurons to record from.
            This is non-standard PyNN and equivalent to creating a view with
            these indexes and asking the View to record.
        :type indexes: None or list(int)
        """
        self._recorder.record(
            variables, to_file, sampling_interval, indexes=indexes)

    def sample(self, n, rng=None):
        """ Randomly sample `n` cells from the Population, and return a\
            PopulationView object.

        :param int n: The number of cells to put in the view.
        :param rng: The random number generator to use
        :type rng: ~pyNN.random.NumpyRNG
        :rtype: ~spynnaker.pyNN.models.populations.PopulationView
        """
        if not rng:
            rng = NumpyRNG()
        indices = rng.permutation(
            numpy.arange(len(self), dtype=numpy.int))[0:n]
        return PopulationView(
            self, indices,
            label="Random sample size {} from {}".format(n, self.label))

    @overrides(PopulationBase.write_data, extend_doc=False)
    def write_data(self, io, variables='all', gather=True, clear=False,
                   annotations=None):
        """ Write recorded data to file, using one of the file formats\
            supported by Neo.

        :param io:
            a Neo IO instance, or a string for where to put a neo instance
        :type io: neo.io.baseio.BaseIO or str
        :param variables:
            either a single variable name or a list of variable names.
            Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :type variables: str or list(str)
        :param bool gather: Whether to bring all relevant data together.

            .. note::
                SpiNNaker always gathers.

        :param bool clear:
            clears the storage data if set to true after reading it back
        :param annotations: annotations to put on the neo block
        :type annotations: dict(str, ...)
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the variable or variables have not been previously set to
            record.
        """
        # pylint: disable=too-many-arguments
        if not gather:
            logger.warning(
                "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")

        if isinstance(io, str):
            io = neo.get_io(io)

        data = self._recorder.extract_neo_block(
            variables, None, clear, annotations)
        # write the neo block to the file
        io.write(data)

    def describe(self, template='population_default.txt', engine='default'):
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
        vertex_context = self._vertex.describe()

        context = {
            "label": self.label,
            "celltype": vertex_context,
            "structure": None,
            "size": self.size,
            "size_local": self.size,
            "first_id": self.first_id,
            "last_id": self.last_id,
        }
        context.update(self._annotations)
        if self.size > 0:
            context.update({
                "local_first_id": self.first_id,
                "cell_parameters": {}})
        if self._structure:
            context["structure"] = self._structure.describe(template=None)
        return descriptions.render(engine, template, context)

    def _end(self):
        """ Do final steps at the end of the simulation
        """
        for variable in self._recorder.write_to_files_indicators:
            if self._recorder.write_to_files_indicators[variable]:
                self.write_data(
                    io=self._recorder.write_to_files_indicators[variable],
                    variables=[variable])

    @overrides(PopulationBase.get_data, extend_doc=False)
    def get_data(
            self, variables='all', gather=True, clear=False, annotations=None):
        """ Return a Neo Block containing the data\
            (spikes, state variables) recorded from the Assembly.

        :param variables: either a single variable name or a list of variable
            names. Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :type variables: str or list(str)
        :param bool gather: Whether to collect data from all MPI nodes or
            just the current node.

            .. note::
                This is irrelevant on sPyNNaker, which always behaves as if
                this parameter is True.

        :param bool clear:
            Whether recorded data will be deleted from the ``Assembly``.
        :param annotations: annotations to put on the neo block
        :type annotations: dict(str, ...)
        :rtype: ~neo.core.Block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the variable or variables have not been previously set to
            record.
        """
        if not gather:
            logger.warning(
                "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        if annotations is not None:
            warn_once(
                logger, "annotations parameter is not standard PyNN so may "
                        "not be supported by all platforms.")

        return self._recorder.extract_neo_block(
            variables, None, clear, annotations)

    def get_data_by_indexes(
            self, variables, indexes, clear=False, annotations=None):
        """ Return a Neo `Block` containing the data\
            (spikes, state variables) recorded from the Assembly.

        :param variables: either a single variable name or a list of variable
            names. Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :type variables: str or list(str)
        :param list(int) indexes: List of neuron indexes to include in the
            data. Clearly only neurons recording will actually have any data.
            If None will be taken as all recording as in :meth:`get_data`
        :param bool clear: Whether recorded data will be deleted.
        :param annotations: annotations to put on the neo block
        :type annotations: dict(str, ...)
        :rtype: ~neo.core.Block
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            If the variable or variables have not been previously set to
            record.
        """
        return self._recorder.extract_neo_block(
            variables, indexes, clear, annotations)

    def spinnaker_get_data(self, variable, as_matrix=False, view_indexes=None):
        """ Public accessor for getting data as a numpy array, instead of\
            the neo based object

        :param str variable: a single variable name.
        :type variable: str or list(str)
        :param bool as_matrix: If set True the data is returned as a 2d matrix
        :param view_indexes: The indexes for which data should be returned.
            If ``None``, all data (view_index = data_indexes)
        :return: array of the data
        :rtype: ~numpy.ndarray
        """
        warn_once(
            logger, "spinnaker_get_data is non-standard PyNN and therefore "
            "will not be portable to other simulators.")
        if isinstance(variable, list):
            if len(variable) != 1:
                raise ConfigurationException(
                    "Only one type of data at a time is supported")
            variable = variable[0]
        if variable == SPIKES:
            if as_matrix:
                logger.warning(f"Ignoring as matrix for {SPIKES}")
            spikes = self._recorder.get_spikes()
            if view_indexes is None:
                return spikes
            return spikes[numpy.isin(spikes[:, 0], view_indexes)]
        return self._recorder.get_recorded_pynn7(
            variable, as_matrix, view_indexes)

    @overrides(PopulationBase.get_spike_counts, extend_doc=False)
    def get_spike_counts(self, gather=True):
        """ Return the number of spikes for each neuron.

        :rtype: ~numpy.ndarray
        """
        spikes = self._recorder.get_spikes()
        return self._get_spike_counts(spikes, gather)

    def _get_spike_counts(self, spikes, gather=True):
        """ Return the number of spikes for each neuron.

        Defined by
        http://neuralensemble.org/docs/PyNN/reference/populations.html

        :param ~numpy.ndarray spikes:
        :param gather: pointless on sPyNNaker
        :rtype: dict(int,int)
        """
        if not gather:
            warn_once(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        n_spikes = {}
        counts = numpy.bincount(spikes[:, 0].astype(dtype=numpy.int32),
                                minlength=self.__vertex.n_atoms)
        for i in range(self.__vertex.n_atoms):
            n_spikes[i] = counts[i]
        return n_spikes

    def find_units(self, variable):
        """ Get the units of a variable

        :param str variable: The name of the variable
        :return: The units of the variable
        :rtype: str
        """
        return self._get_variable_unit(variable)

    def set(self, **parameters):
        """ Set parameters of this population.

        :param parameters: The parameters to set.
        """
        for parameter, value in parameters.items():
            try:
                self._set(parameter, value)
            except InvalidParameterType:
                self._initialize(parameter, value)

    @overrides(PopulationBase.tset)
    def tset(self, **kwargs):
        logger.warning(
            "This function is deprecated; call pop.set(...) instead")
        for parameter, value in kwargs.items():
            try:
                self._set(parameter, value)
            except InvalidParameterType:
                self._initialize(parameter, value)

    def initialize(self, **kwargs):
        """ Set initial values of state variables, e.g. the membrane\
            potential.  Values passed to ``initialize()`` may be:

        * single numeric values (all neurons set to the same value), or
        * :py:class:`~pyNN.random.RandomDistribution` objects, or
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
        for parameter, value in kwargs.items():
            self._initialize(parameter, value)

    @property
    def initial_values(self):
        """
        :rtype: dict
        """
        if not self.__vertex_population_initializable:
            raise KeyError(
                "Population does not support the initialisation")
        return self._vertex.initial_values

    def get_initial_value(self, variable, selector=None):
        """
        .. deprecated:: 6.0
            Use :py:meth:`initial_values` instead.
        """
        raise NotImplementedError(REMOVED_V6.format(
            "get_initial_value", "initial_values"))

    def _get_initial_value(self, variable, selector):
        """ See :py:meth:`~.AbstractPopulationInitializable.get_initial_value`

        :param str variable: variable name with or without ``_init`` suffix
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :return: A list, or an object which acts like a list
        :rtype: iterable
        """
        if not self.__vertex_population_initializable:
            raise KeyError(
                "Population does not support the initialisation of {}".format(
                    variable))
        return self._vertex.get_initial_value(variable, selector)

    def set_initial_value(self, variable, value, selector=None):
        """
        .. deprecated:: 6.0
            Use :py:meth:`initialize` instead.
        """
        raise NotImplementedError(REMOVED_V6.format(
            "set_initial_value", "initialize"))

    def _get_initial_values(self, selector=None):
        """ See :py:meth:`~.AbstractPopulationInitializable.get_initial_values`

        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :return: dictionary from variable name to initial value(s)
        :rtype: dict(str,int or float or list(int) or list(float))
        """
        if not self.__vertex_population_initializable:
            raise KeyError("Population does not support the initialisation")
        return self._vertex.get_initial_values(selector)

    @property
    def positions(self):
        """ Return the position array for structured populations.

        :return: a 2D array, one row per cell.
            Each row is three long, for X,Y,Z
        :rtype: ~numpy.ndarray
        """
        if self._positions is None:
            if self._structure is None:
                raise ValueError("attempted to retrieve positions "
                                 "for an unstructured population")
            self._positions = self._structure.generate_positions(
                self._vertex.n_atoms)
        return self._positions.T  # change of order in pyNN 0.8

    @positions.setter
    def positions(self, positions):
        """ Sets all the positions in the population.
        """
        self._positions = positions

        # state that something has changed in the population,
        self.__change_requires_mapping = True

    @property
    def all_cells(self):
        """
        :rtype: list(~spynnaker.pyNN.models.populations.IDMixin)
        """
        cells = []
        for _id in range(self._size):
            cells.append(IDMixin(self, _id))
        return cells

    @property
    def position_generator(self):
        """
        :rtype: callable((int), ~numpy.ndarray)
        """
        def gen(i):
            return self.positions[:, i]
        return gen

    @property
    def first_id(self):
        """ The ID of the first member of the population.

        :rtype: int
        """
        return self.__first_id

    @property
    def last_id(self):
        """ The ID of the last member of the population.

        :rtype: int
        """
        return self.__last_id

    @property
    def _structure(self):
        """
        :rtype: ~pyNN.space.BaseStructure or None
        """
        return self.__structure

    @property
    def _vertex(self):
        """
        :rtype: ~pacman.model.graphs.application.ApplicationVertex
        """
        return self.__vertex

    @property
    def requires_mapping(self):
        """ Whether this population requires mapping.

        :rtype: bool
        """
        return self.__change_requires_mapping

    @requires_mapping.setter
    def requires_mapping(self, new_value):
        self.__change_requires_mapping = new_value

    def mark_no_changes(self):
        """ Mark this population as not having changes to be mapped.
        """
        self.__change_requires_mapping = False
        self.__has_read_neuron_parameters_this_run = False

    @property
    def conductance_based(self):
        """ True if the population uses conductance inputs

        :rtype: bool
        """
        if hasattr(self.__vertex, "conductance_based"):
            return self.__vertex.conductance_based
        return False

    def get(self, parameter_names, gather=True, simplify=True):
        """ Get the values of a parameter for every local cell in the\
            population.

        :param parameter_names: Name of parameter. This is either a single
            string or a list of strings
        :type parameter_names: str or iterable(str)
        :param bool gather: pointless on sPyNNaker
        :param bool simplify: ignored
        :return: A single list of values (or possibly a single value) if
            paramter_names is a string, or a dict of these if parameter names
            is a list.
        :rtype: str or list(str) or dict(str,str) or dict(str,list(str))
        """
        if not gather:
            warn_once(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        if simplify is not True:
            warn_once(
                logger, "The simplify value is ignored if not set to true")
        if not self.__vertex_population_settable:
            raise KeyError("Population does not support setting")
        if isinstance(parameter_names, str):
            return self.__vertex.get_value(parameter_names)
        results = dict()
        for parameter_name in parameter_names:
            results[parameter_name] = self.__vertex.get_value(parameter_name)
        return results

    # NON-PYNN API CALL
    def _get_by_selector(self, selector, parameter_names):
        """ Get the values of a parameter for the selected cell in the\
            population.

        :param selector: a description of the subrange to accept.
            Or None for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: slice or int or iterable(bool) or iterable(int)
        :param parameter_names: Name of parameter. This is either a
            single string or a list of strings
        :type parameter_names: str or iterable(str)
        :return: A single list of values (or possibly a single value) if
            paramter_names is a string or a dict of these if parameter names
            is a list.
        :rtype: str or list(str) or dict(str,str) or dict(str,list(str))
        """
        if not self.__vertex_population_settable:
            raise KeyError("Population does not support setting")
        if isinstance(parameter_names, str):
            return self.__vertex.get_value_by_selector(
                selector, parameter_names)
        results = dict()
        for parameter_name in parameter_names:
            results[parameter_name] = self.__vertex.get_value_by_selector(
                selector, parameter_name)
        return results

    def id_to_index(self, id):  # @ReservedAssignment
        """ Given the ID(s) of cell(s) in the Population, return its (their)\
            index (order in the Population).

        Defined by
        http://neuralensemble.org/docs/PyNN/reference/populations.html

        :param id:
        :type id: int or iterable(int)
        :rtype: int or iterable(int)
        """
        # pylint: disable=redefined-builtin
        if not numpy.iterable(id):
            if not self.__first_id <= id <= self.__last_id:
                raise ValueError(
                    "id should be in the range [{},{}], actually {}".format(
                        self.__first_id, self.__last_id, id))
            return int(id - self.__first_id)  # assume IDs are consecutive
        return id - self.__first_id

    def index_to_id(self, index):
        """ Given the index (order in the Population) of cell(s) in the\
            Population, return their ID(s)

        :param index:
        :type index: int or iterable(int)
        :rtype: int or iterable(int)
        """
        if not numpy.iterable(index):
            if index > self.__last_id - self.__first_id:
                raise ValueError(
                    "indexes should be in the range [{},{}], actually {}"
                    "".format(0, self.__last_id - self.__first_id, index))
            return int(index + self.__first_id)
        # this assumes IDs are consecutive
        return index + self.__first_id

    def id_to_local_index(self, cell_id):
        """ Given the ID(s) of cell(s) in the Population, return its (their)\
            index (order in the Population), counting only cells on the local\
            MPI node.

        Defined by
        http://neuralensemble.org/docs/PyNN/reference/populations.html

        :param cell_id:
        :type cell_id: int or iterable(int)
        :rtype: int or iterable(int)
        """
        # TODO: Need __getitem__
        _we_dont_do_this_now(cell_id)

    def _initialize(self, variable, value, selector=None):
        """ Set the initial value of one of the state variables of the neurons\
            in this population.

        :param str variable:
        :param value:
        :type value: float or int or list(float) or list(int)
        :param selector: a description of the subrange to accept.
            Or None for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: slice or int or iterable(bool) or iterable(int)
        """
        if not self.__vertex_population_initializable:
            raise KeyError(
                "Population does not support the initialisation of {}".format(
                    variable))
        if get_not_running_simulator().has_ran \
                and not self.__vertex_changeable_after_run:
            raise Exception("Population does not support changes after run")
        self._read_parameters_before_set()
        self.__vertex.initialize(variable, value, selector)

    def inject(self, current_source):
        """ Connect a current source to all cells in the Population.

        Defined by
        http://neuralensemble.org/docs/PyNN/reference/populations.html
        """
        # Pass this into the vertex
        self.__vertex.inject(current_source, [n for n in range(self._size)])
        current_source.set_population(self)
        # Must remap if called between runs (with reset)
        self.__change_requires_mapping = True

    def __len__(self):
        """ Get the total number of cells in the population.
        """
        return self._size

    @property
    def label(self):
        """ The label of the population

        :rtype: str
        """
        return self._vertex.label

    @label.setter
    def label(self, label):
        raise NotImplementedError(
            "As label is used as an ID it can not be changed")

    @property
    def local_size(self):
        """ The number of local cells

        Defined by
        http://neuralensemble.org/docs/PyNN/reference/populations.html
        """
        # Doesn't make much sense on SpiNNaker
        return self._size

    def _set_check(self, parameter, value):
        """ Checks for various set methods.
        """
        if not self.__vertex_population_settable:
            raise KeyError("Population does not have property {}".format(
                parameter))

        sim = get_not_running_simulator()
        if sim.has_ran and not self.__vertex_changeable_after_run:
            raise Exception(
                "Run has been called but vertex is not changable.")

        if isinstance(parameter, str):
            if value is None:
                raise Exception("A value (not None) must be specified")
        elif type(parameter) is not dict:
            raise Exception(
                "Parameter must either be the name of a single parameter to"
                " set, or a dict of parameter: value items to set")

        if not sim.has_reset_last:
            self._read_parameters_before_set()

    def _set(self, parameter, value=None):
        """ Set one or more parameters for every cell in the population.

        ``parameter`` can be a dict, in which case ``value`` should not be
        supplied, or a string giving the parameter name, in which case
        ``value`` is the parameter value. ``value`` can be a numeric value, or
        list of such (e.g. for setting spike times)::

            p._set("tau_m", 20.0).
            p._set({'tau_m':20, 'v_rest':-65})

        :param parameter:
            the parameter to set or dictionary of parameters to set
        :type parameter:
            str or dict(str, int or float or list(int) or list(float))
        :param value: the value of the parameter to set.
        :type value: int or float or list(int) or list(float)
        """
        self._set_check(parameter, value)

        # set new parameters
        if isinstance(parameter, str):
            if value is None:
                raise Exception("A value (not None) must be specified")
            self.__vertex.set_value(parameter, value)
            return
        for (key, value) in parameter.iteritems():
            self.__vertex.set_value(key, value)

    # NON-PYNN API CALL
    def set_by_selector(self, selector, parameter, value=None):
        """ Set one or more parameters for selected cell in the population.

        param can be a dict, in which case value should not be supplied, or a
        string giving the parameter name, in which case value is the parameter
        value. value can be a numeric value, or list of such
        (e.g. for setting spike times)::

            p.set_by_selector(1, "tau_m", 20.0).
            p.set_by_selector(1, {'tau_m':20, 'v_rest':-65})

        :param selector:
            See :py:meth:`RangedList.set_value_by_selector` as this is just a
            pass through method
        :param parameter:
            the parameter to set or dictionary of parameters to set
        :type parameter:
            str or dict(str, int or float or list(int) or list(float))
        :param value: the value of the parameter to set.
        :type value: int or float or list(int) or list(float)
        """
        self._set_check(parameter, value)

        # set new parameters
        if type(parameter) is str:
            self.__vertex.set_value_by_selector(selector, parameter, value)
        else:
            for (key, value) in parameter.iteritems():
                self.__vertex.set_value_by_selector(selector, key, value)

    def _read_parameters_before_set(self):
        """ Reads parameters from the machine before :py:meth:`set` completes
        """

        # If the tools have run before, and not reset, and the read
        # hasn't already been done, read back the data
        sim = get_simulator()
        if (sim.has_ran
                and not self.__has_read_neuron_parameters_this_run
                and not sim.use_virtual_board):
            # go through each machine vertex and read the neuron parameters
            # it contains
            for vertex in self.__vertex.machine_vertices:
                if isinstance(vertex, AbstractReadParametersBeforeSet):
                    # tell the core to rewrite neuron params back to the
                    # SDRAM space.
                    placement = sim.placements.get_placement_of_vertex(vertex)
                    vertex.read_parameters_from_machine(
                        sim.transceiver, placement, vertex.vertex_slice)

            self.__has_read_neuron_parameters_this_run = True

    @property
    def structure(self):
        """ Return the structure for the population.

        :rtype: ~pyNN.space.BaseStructure or None
        """
        return self.__structure

    # NON-PYNN API CALL
    def set_constraint(self, constraint):
        """ Apply a constraint to a population that restricts the processor\
            onto which its atoms will be placed.

        :param ~pacman.model.constraints.AbstractConstraint constraint:
        """
        get_simulator().verify_not_running()
        if not isinstance(constraint, AbstractConstraint):
            raise ConfigurationException(
                "the constraint entered is not a recognised constraint")

        self.__vertex.add_constraint(constraint)
        # state that something has changed in the population,
        self.__change_requires_mapping = True

    # NON-PYNN API CALL
    def add_placement_constraint(self, x, y, p=None):
        """ Add a placement constraint

        :param int x: The x-coordinate of the placement constraint
        :param int y: The y-coordinate of the placement constraint
        :param int p: The processor ID of the placement constraint (optional)
        """
        get_simulator().verify_not_running()
        self.__vertex.add_constraint(ChipAndCoreConstraint(x, y, p))

        # state that something has changed in the population,
        self.__change_requires_mapping = True

    # NON-PYNN API CALL
    def set_mapping_constraint(self, constraint_dict):
        """ Add a placement constraint - for backwards compatibility

        :param dict(str,int) constraint_dict:
            A dictionary containing "x", "y" and optionally "p" as keys, and
            ints as values
        """
        get_simulator().verify_not_running()
        self.add_placement_constraint(**constraint_dict)

        # state that something has changed in the population,
        self.__change_requires_mapping = True

    # NON-PYNN API CALL
    def set_max_atoms_per_core(self, max_atoms_per_core):
        """ Supports the setting of this population's max atoms per core

        :param int max_atoms_per_core:
            the new value for the max atoms per core.
        """
        get_simulator().verify_not_running()
        self.__vertex.add_constraint(
            MaxVertexAtomsConstraint(max_atoms_per_core))
        # state that something has changed in the population
        self.__change_requires_mapping = True

    @property
    def size(self):
        """ The number of neurons in the population

        :rtype: int
        """
        return self.__vertex.n_atoms

    @property
    def _internal_delay_vertex(self):
        """
        :rtype: DelayExtensionVertex
        """
        return self.__delay_vertex

    @_internal_delay_vertex.setter
    def _internal_delay_vertex(self, delay_vertex):
        self.__delay_vertex = delay_vertex
        self.__change_requires_mapping = True

    def _get_variable_unit(self, parameter_name):
        """ Helper method for getting units from a parameter used by the vertex

        :param str parameter_name: the parameter name to find the units for
        :return: the units in string form
        :rtype: str
        """
        if self.__vertex_contains_units:
            return self.__vertex.get_units(parameter_name)
        raise ConfigurationException(
            "This population does not support describing its units")

    def _cache_data(self):
        """ Store data for later extraction
        """
        self._recorder.cache_data()

    @staticmethod
    def __create_model(cellclass, cellparams):
        """
        :param cellclass: The implementation of the individual neurons.
        :type cellclass: type or AbstractPyNNModel or ApplicationVertex
        :param cellparams: Parameters to pass to ``cellclass`` if it
            is a class to instantiate. Must be ``None`` if ``cellclass`` is an
            instantiated object.
        :type cellparams: dict(str,object) or None
        :rtype: ApplicationVertex or AbstractPyNNModel
        """
        model = cellclass
        if inspect.isclass(cellclass):
            if cellparams is None:
                model = cellclass()
            else:
                model = cellclass(**cellparams)
        elif cellparams:
            raise ConfigurationException(
                "cellclass is an instance which includes params so "
                "cellparams must be None")
        return model

    def __create_vertex(
            self, model, size, label, constraints, additional_parameters):
        """
        :param model: The implementation of the individual neurons.
        :type model: ApplicationVertex or AbstractPyNNModel
        :param int size:
        :param label:
        :type label: str or None
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Any constraints on how the population is deployed to SpiNNaker.
        :param additional_parameters:
            Additional parameters to pass to the vertex creation function.
        :type additional_parameters: dict(str, ...)
        """
        # pylint: disable=too-many-arguments
        self._celltype = model
        # Use a provided model to create a vertex
        if isinstance(model, AbstractPyNNModel):
            if size is not None and size <= 0:
                raise ConfigurationException(
                    "A population cannot have a negative or zero size.")
            population_parameters = dict(model.default_population_parameters)
            if additional_parameters is not None:
                # check that the additions are suitable. report wrong ones
                # and ignore
                population_parameters = self.__process_additional_params(
                    additional_parameters, population_parameters)
            self.__vertex = model.create_vertex(
                size, label, constraints, **population_parameters)

        # Use a provided application vertex directly
        elif isinstance(model, ApplicationVertex):
            if additional_parameters is not None:
                raise ConfigurationException(
                    "Cannot accept additional parameters {} when the cell is"
                    " a vertex".format(additional_parameters))
            self.__vertex = model
            if size is None:
                size = self.__vertex.n_atoms
            elif size != self.__vertex.n_atoms:
                raise ConfigurationException(
                    "Vertex size does not match Population size")
            if label is not None:
                self.__vertex.set_label(label)
            if constraints is not None:
                self.__vertex.add_constraints(constraints)

        # Fail on anything else
        else:
            raise ConfigurationException(
                "Model must be either an AbstractPyNNModel or an"
                " ApplicationVertex")

        # Introspect properties of the vertex
        self.__vertex_population_settable = \
            isinstance(self.__vertex, AbstractPopulationSettable)
        self.__vertex_population_initializable = \
            isinstance(self.__vertex, AbstractPopulationInitializable)
        self.__vertex_changeable_after_run = \
            isinstance(self.__vertex, AbstractChangableAfterRun)
        self.__vertex_contains_units = \
            isinstance(self.__vertex, AbstractContainsUnits)

    @staticmethod
    def create(cellclass, cellparams=None, n=1):
        """ Pass through method to the constructor defined by PyNN.\
        Create ``n`` cells all of the same type.

        :param cellclass: see :py:meth:`~.Population.__init__`
        :type cellclass: type or AbstractPyNNModel
        :param cellparams: see :py:meth:`~.Population.__init__`
        :type cellparams: dict(str, object) or None
        :param int n: see :py:meth:`~.Population.__init__` (``size`` parameter)
        :return: A New Population
        :rtype: ~spynnaker.pyNN.models.populations.Population
        """
        return Population(size=n, cellclass=cellclass, cellparams=cellparams)

    @staticmethod
    def __process_additional_params(
            additional_parameters, population_parameters):
        """ essential method for allowing things like splitter objects at\
            pop level

        :param additional_parameters: the additional params handed down from
            user
        :param population_parameters: the additional params the vertex can
            support.
        :return: the list of params that are accepted.
        """
        for key in additional_parameters.keys():
            if key in population_parameters:
                population_parameters[key] = additional_parameters[key]
            else:
                logger.warning(
                    "additional_parameter {} will be ignored".format(key))
        return population_parameters

    @staticmethod
    def __roundsize(size, label):
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
            "Size of a population with label {} must be an int,"
            " received {}".format(label, size))
