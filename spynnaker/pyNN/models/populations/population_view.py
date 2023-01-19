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
import neo
import numpy
from spinn_utilities.log import FormatAdapter
from pyNN import descriptions
from pyNN.random import NumpyRNG
from spinn_utilities.logger_utils import warn_once
from spinn_utilities.ranged.abstract_sized import AbstractSized
from .population_base import PopulationBase
from spinn_utilities.overrides import overrides

logger = FormatAdapter(logging.getLogger(__name__))


class PopulationView(PopulationBase):
    """ A view of a subset of neurons within a\
        :py:class:`~spynnaker.pyNN.models.populations.Population`.

    In most ways, Populations and PopulationViews have the same behaviour,
    i.e., they can be recorded, connected with Projections, etc.
    It should be noted that any changes to neurons in a PopulationView
    will be reflected in the parent Population and *vice versa.*

    It is possible to have views of views.

    .. note::
        Selector to Id is actually handled by :py:class:`~.AbstractSized`.
    """
    __slots__ = [
        "__annotations",
        "__indexes",
        "__label",
        "__mask",
        "__parent",
        "__population",
        "__vertex",
        "__recorder"]

    __realslots__ = tuple("_PopulationView" + item for item in __slots__)

    def __init__(self, parent, selector, label=None):
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
            self.__indexes = parent.index_in_grandparent(ids)
        else:
            self.__population = parent
            self.__indexes = ids
        self.__mask = selector
        self.__label = label
        self.__annotations = dict()

        # Get these two objects to make access easier
        # pylint: disable=protected-access
        self.__vertex = self.__population._vertex
        # pylint: disable=protected-access
        self.__recorder = self.__population._recorder

    def __getattr__(self, name):
        return self.__vertex.get_parameter_values(name, self.__indexes)

    def __setattr__(self, name, value):
        if name in self.__realslots__:
            object.__setattr__(self, name, value)
            return
        return self.__vertex.set_parameter_values(name, value, self.__indexes)

    @property
    def size(self):
        """ The total number of neurons in the Population View.

        :rtype: int
        """
        return len(self.__indexes)

    @property
    def label(self):
        """ A label for the Population View.

        :rtype: str
        """
        return self.__label

    @property
    def celltype(self):
        """ The type of neurons making up the underlying Population.

        :rtype: AbstractPyNNModel
        """
        return self.__parent.celltype

    @property
    def initial_values(self):
        """ A dict containing the initial values of the state variables.

        :rtype: InitialValuesHolder
        """
        return self.__vertex.get_initial_state_values(
            self.__vertex.get_state_variables(), self.__indexes)

    @property
    def current_values(self):
        """ A dict containing the initial values of the state variables.

        :rtype: InitialValuesHolder
        """
        warn_once(
            logger, "current_values is non-standard PyNN and therefore "
            "will not be portable to other simulators.")
        return self.__vertex.get_current_state_values(
            self.__vertex.get_state_variables(), self.__indexes)

    @property
    def parent(self):
        """ A reference to the parent Population (that this is a view of).

        :rtype: ~spynnaker.pyNN.models.populations.Population
        """
        return self.__parent

    @property
    def mask(self):
        """  The selector mask that was used to create this view.

        :rtype: None or slice or int or list(bool) or list(int) or
            ~numpy.ndarray(bool) or ~numpy.ndarray(int)
        """
        return self.__mask

    @property
    def all_cells(self):
        """ An array containing the cell IDs of all neurons in the\
            Population (all MPI nodes).

        :rtype: list(IDMixin)
        """
        return [IDMixin(self.__population, idx) for idx in self.__indexes]

    @property
    def _indexes(self):
        return tuple(self.__indexes)

    def __getitem__(self, index):
        """ Return either a single cell (ID object) from the Population,\
            if index is an integer, or a subset of the cells\
            (PopulationView object), if index is a slice or array.

        .. note::
            ``__getitem__`` is called when using[] access, e.g. if
            ``p = Population(...)`` then
            ``p[2]`` is equivalent to ``p.__getitem__(2)``, and
            ``p[3:6]`` is equivalent to ``p.__getitem__(slice(3, 6))``

        :rtype: ~.IDMixin or ~.PopulationView
        """
        if isinstance(index, int):
            return IDMixin(self.__population, index)
        return PopulationView(self, index, label=self.label + "_" + str(index))

    def __iter__(self):
        """ Iterator over cell IDs (on the local node).

        :rtype: iterable(~.IDMixin)
        """
        for idx in self.__indexes:
            yield IDMixin(self.__population, idx)

    def __len__(self):
        """ Return the total number of cells in the population (all nodes).

        :rtype: int
        """
        return len(self.__indexes)

    def all(self):
        """ Iterator over cell IDs (on all MPI nodes).

        :rtype: iterable(~.IDMixin)
        """
        for idx in self.__indexes:
            yield IDMixin(self.__population, idx)

    def can_record(self, variable):
        """ Determine whether variable can be recorded from this population.

        :rtype: bool
        """
        return self.__vertex.can_record(variable)

    @property
    def conductance_based(self):
        """ Indicates whether the post-synaptic response is modelled as a\
            change in conductance or a change in current.

        :rtype: bool
        """
        return self.__vertex.conductance_based

    def inject(self, current_source):
        """ Injects the specified current_source into this PopulationView.

        :param ~pyNN.standardmodels.electrodes.StandardCurrentSource\
            current_source: the CurrentSource to be injected
        """
        self.__vertex.inject(current_source, self.__indexes)

    def describe(self, template='populationview_default.txt',
                 engine='default'):
        """ Returns a human-readable description of the population view.

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

    def find_units(self, variable):
        """ Get the units of a variable

        .. warning::
            No PyNN description of this method.

        :param str variable: The name of the variable
        :return: The units of the variable
        :rtype: str
        """
        return self.__vertex.get_units(variable)

    def get(self, parameter_names, gather=False, simplify=True):
        """ Get the values of the given parameters for every local cell in\
            the population, or, if ``gather=True``,\
            for all cells in the population.

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
            self, variables='all', gather=True, clear=False, annotations=None):
        """ Return a Neo Block containing the data(spikes, state variables)\
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

    def spinnaker_get_spikes(self):
        """ Pulic accessor for getting spikes as a numpy array, instead of\
            the neo based object
        """
        spikes = self.__recorder.get_data("spikes")
        return spikes[numpy.isin(spikes[:, 0], self.__indexes)]

    def spinnaker_get_data(self, variable, as_matrix=False):
        """ Public accessor for getting data as a numpy array, instead of\
            the neo based object

        :param str variable: a single variable name
        :param bool as_matrix: If set True the data is returned as a 2d matrix
        :return: array of the data
        :rtype: ~numpy.ndarray
        """
        return self.__population.spinnaker_get_data(
            variable, as_matrix, self.__indexes)

    def get_spike_counts(self, gather=True):
        """ Returns a dict containing the number of spikes for each neuron.

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
        if not gather:
            logger.warning(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        logger.info("get_spike_counts is inefficient as it just counts the "
                    "results of get_datas('spikes')")
        spikes = self.__recorder.get_data("spikes")
        counts = numpy.bincount(spikes[:, 0].astype(dtype=numpy.int32),
                                minlength=self.__vertex.n_atoms)
        return {i: counts[i] for i in self.__indexes}

    @property
    def grandparent(self):
        """ Returns the parent Population at the root of the tree (since the\
            immediate parent may itself be a PopulationView).

        The name "grandparent" is of course a little misleading, as it could
        be just the parent, or the great, great, great, ..., grandparent.

        :rtype: ~spynnaker.pyNN.models.populations.Population
        """
        return self.__population

    def id_to_index(self, id):  # pylint: disable=redefined-builtin
        """ Given the ID(s) of cell(s) in the PopulationView, return its /\
            their index / indices(order in the PopulationView).

        assert pv.id_to_index(pv[3]) == 3

        :param id:
        :type id: int or list(int)
        :rtype: int or list(int)
        """
        if isinstance(id, int):
            return self.__indexes.index(id)
        return [self.__indexes.index(idx) for idx in id]

    def index_in_grandparent(self, indices):
        """ Given an array of indices, return the indices in the parent\
            population at the root of the tree.

        :param list(int) indices:
        :rtype: list(int)
        """
        return [self.__indexes[index] for index in indices]

    def initialize(self, **initial_values):
        """ Set initial values of state variables, e.g. the membrane\
            potential.  Values passed to ``initialize()`` may be:

        * single numeric values (all neurons set to the same value), or
        * :py:class:`~pyNN.random.RandomDistribution` objects, or
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

    def set_state(self, **initial_values):
        """ Set current values of state variables, e.g. the membrane\
            potential.  Values passed to ``initialize()`` may be:

        * single numeric values (all neurons set to the same value), or
        * :py:class:`~pyNN.random.RandomDistribution` objects, or
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

    def record(self, variables,  to_file=None, sampling_interval=None):
        """ Record the specified variable or variables for all cells in the\
            Population or view.

        :param variables: either a single variable name, or a list of variable
            names, or ``all`` to record everything. For a given celltype
            class, celltype.recordable contains a
            list of variables that can be recorded for that celltype.
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

    def sample(self, n, rng=None):
        """ Randomly sample `n` cells from the Population view, and return a\
            new PopulationView object.

        :param int n: The number of cells to select
        :param ~pyNN.random.NumpyRNG rng: Random number generator
        :rtype: ~spynnaker.pyNN.models.populations.PopulationView
        """
        if not rng:
            rng = NumpyRNG()
        indices = rng.permutation(
            numpy.arange(len(self), dtype=numpy.int))[0:n]
        return PopulationView(
            self, indices,
            label="Random sample size {} from {}".format(n, self.label))

    def set(self, **parameters):
        """ Set one or more parameters for every cell in the population.\
            Values passed to `set()` may be:

        * single values,
        * :py:class:`~pyNN.random.RandomDistribution` objects, or
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

    def write_data(self, io, variables='all', gather=True, clear=False,
                   annotations=None):
        """ Write recorded data to file, using one of the file formats\
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
        data = self.__recorder.extract_neo_block(
            variables, self.__indexes, clear, annotations)

        if isinstance(io, str):
            io = neo.get_io(io)

        # write the neo block to the file
        io.write(data)

    @property
    @overrides(PopulationBase._vertex)
    def _vertex(self):
        return self.__vertex

    @property
    @overrides(PopulationBase._recorder)
    def _recorder(self):
        return self.__recorder

    def __eq__(self, other):
        if not isinstance(other, PopulationView):
            return False
        return (self.__vertex == other._vertex and
                self._indexes == other._indexes)

    def __ne__(self, other):
        if not isinstance(other, PopulationView):
            return True
        return not self.__eq__(other)

    def __str__(self):
        return str(self.__vertex) + str(self.__indexes)

    def __repr__(self):
        return repr(self.__vertex) + str(self.__indexes)


class IDMixin(PopulationView):

    __slots__ = []

    def get_parameters(self):
        """ Return a dict of all cell parameters.

        :rtype: dict(str, ...)
        """
        return self._vertex.get_parameter_values(
            self._vertex.get_parameters(), self.id)

    # NON-PYNN API CALLS
    @property
    def id(self):
        """
        :rtype: int
        """
        return self._indexes[0]

    def __getattr__(self, name):
        if name == "_vertex":
            raise KeyError("Shouldn't come through here!")
        return self._vertex.get_parameter_values(name, self.id)

    def __setattr__(self, name, value):
        if name in self.__realslots__:
            object.__setattr__(self, name, value)
            return
        return self._vertex.set_parameter_values(name, value, self.id)

    def get_initial_value(self, variable):
        """ Get the initial value of a state variable of the cell.

        :param str variable: The name of the variable
        :rtype: float
        """
        return self._vertex.get_initial_state_values(variable, self.id)

    @property
    def initial_values(self):
        return self._vertex.get_initial_state_values(
            self._vertex.get_state_variables(), self.id)

    def set_initial_value(self, variable, value):
        """ Set the initial value of a state variable of the cell.
        :param str variable: The name of the variable
        :param float value: The value of the variable
        """
        self._vertex.set_initial_state_values(variable, value, self.id)

    def set_parameters(self, **parameters):
        """ Set cell parameters, given as a sequence of parameter=value\
            arguments.
        """
        for (name, value) in parameters.items():
            self._vertex.set_parameter_values(name, value, self.id)

    def as_view(self):
        """ Return a PopulationView containing just this cell.

        :rtype: ~spynnaker.pyNN.models.populations.PopulationView
        """
        return self

    @property
    def local(self):
        """ Whether this cell is local to the current MPI node.

        :rtype: bool
        """
        # There are no MPI nodes!
        return True
