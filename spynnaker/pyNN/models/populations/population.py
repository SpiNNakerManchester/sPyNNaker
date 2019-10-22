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
from six import iteritems, string_types
from pyNN import descriptions
from pyNN.random import NumpyRNG
from spinn_utilities.logger_utils import warn_once
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.models.pynn_population_common import PyNNPopulationCommon
from spynnaker.pyNN.utilities.constants import SPIKES
from .idmixin import IDMixin
from .population_base import PopulationBase
from .population_view import PopulationView
from spynnaker.pyNN.models.recorder import Recorder

logger = logging.getLogger(__name__)


class Population(PyNNPopulationCommon, Recorder, PopulationBase):
    """ PyNN 0.8/0.9 population object
    """

    def __init__(
            self, size, cellclass, cellparams=None, structure=None,
            initial_values=None, label=None, constraints=None,
            additional_parameters=None):
        # pylint: disable=too-many-arguments

        # hard code initial values as required
        if initial_values is None:
            initial_values = {}

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

        self._celltype = model

        # build our initial objects
        super(Population, self).__init__(
            spinnaker_control=globals_variables.get_simulator(),
            size=size, label=label, constraints=constraints,
            model=model, structure=structure, initial_values=initial_values,
            additional_parameters=additional_parameters)
        Recorder.__init__(self, population=self)

        # annotations used by neo objects
        self._annotations = dict()

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
        """ Iterator over cell IDs on all MPI nodes."""
        for _id in range(self._size):
            yield IDMixin(self, _id)

    @property
    def annotations(self):
        """ The annotations given by the end user
        """
        return self._annotations

    @property
    def celltype(self):
        """ Implements the PyNN expected celltype property

        :return: The celltype this property has been set to
        """
        return self._celltype

    def can_record(self, variable):
        """ Determine whether `variable` can be recorded from this population.
        """
        return variable in self._get_all_possible_recordable_variables()

    def record(self, variables, to_file=None, sampling_interval=None,
               indexes=None):
        """ Record the specified variable or variables for all cells in the\
            Population or view.

        :param variables: either a single variable name or a list of variable\
            names. For a given celltype class, `celltype.recordable` contains\
            a list of variables that can be recorded for that celltype.
        :type variables: str or list(str)
        :param to_file: a file to automatically record to (optional).\
            `write_data()` will be automatically called when `end()` is called.
        :type to_file: a Neo IO instance
        :param sampling_interval: a value in milliseconds, and an integer\
            multiple of the simulation timestep.
        :type sampling_interval: int
        :param indexes: The indexes of neurons to record from.\
        This is none Standard PyNN and equivelent to creating a view with\
        these indexes and asking the View to record.
        """
        # pylint: disable=arguments-differ
        if indexes is not None:
            warn_once(
                logger, "record indexes parameter is non-standard PyNN, "
                "so may not be portable to other simulators. "
                "It is now deprecated and replaced with views")
        self._record_with_indexes(
            variables, to_file, sampling_interval, indexes)

    def _record_with_indexes(
            self, variables, to_file, sampling_interval, indexes):
        """ Same as record but without non-standard PyNN warning

        This method is non-standard PyNN and is intended only to be called by\
        record in a Population, View or Assembly
        """
        if variables is None:  # reset the list of things to record
            if sampling_interval is not None:
                raise ConfigurationException(
                    "Clash between parameters in record."
                    "variables=None turns off recording,"
                    "while sampling_interval!=None implies turn on recording")
            if indexes is not None:
                warn_once(
                    logger,
                    "View.record with variable None is non-standard PyNN. "
                    "Only the neurons in the view have their record turned "
                    "off. Other neurons already set to record will remain "
                    "set to record")

            # note that if record(None) is called, its a reset
            Recorder._turn_off_all_recording(self, indexes)
            # handle one element vs many elements
        elif isinstance(variables, string_types):
            # handle special case of 'all'
            if variables == "all":
                warn_once(
                    logger, 'record("all") is non-standard PyNN, and '
                    'therefore may not be portable to other simulators.')

                # get all possible recordings for this vertex
                variables = self._get_all_possible_recordable_variables()

                # iterate though them
                for variable in variables:
                    self._record(variable, sampling_interval, to_file, indexes)
            else:
                # record variable
                self._record(variables, sampling_interval, to_file, indexes)

        else:  # list of variables, so just iterate though them
            for variable in variables:
                self._record(variable, sampling_interval, to_file, indexes)

    def sample(self, n, rng=None):
        """ Randomly sample `n` cells from the Population, and return a\
            PopulationView object.
        """
        if not rng:
            rng = NumpyRNG()
        indices = rng.permutation(
            numpy.arange(len(self), dtype=numpy.int))[0:n]
        return PopulationView(
            self, indices,
            label="Random sample size {} from {}".format(n, self.label))

    def write_data(self, io, variables='all', gather=True, clear=False,
                   annotations=None):
        """ Write recorded data to file, using one of the file formats\
            supported by Neo.

        :param io: \
            a Neo IO instance, or a string for where to put a neo instance
        :type io: neo instance or str
        :param variables: \
            either a single variable name or a list of variable names.\
            Variables must have been previously recorded, otherwise an\
            Exception will be raised.
        :type variables: str or list(str)
        :param gather: pointless on sPyNNaker
        :param clear: \
            clears the storage data if set to true after reading it back
        :param annotations: annotations to put on the neo block
        """
        # pylint: disable=too-many-arguments
        if not gather:
            logger.warning(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")

        if isinstance(io, string_types):
            io = neo.get_io(io)

        data = self._extract_neo_block(variables, None, clear, annotations)
        # write the neo block to the file
        io.write(data)

    def describe(self, template='population_default.txt', engine='default'):
        """ Returns a human-readable description of the population.

        The output may be customized by specifying a different template\
        together with an associated template engine (see\
        :mod:`pyNN.descriptions`).

        If `template` is None, then a dictionary containing the template\
        context will be returned.
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
        for variable in self._write_to_files_indicators:
            if self._write_to_files_indicators[variable] is not None:
                self.write_data(
                    io=self._write_to_files_indicators[variable],
                    variables=[variable])

    def get_data(
            self, variables='all', gather=True, clear=False, annotations=None):
        """ Return a Neo `Block` containing the data\
            (spikes, state variables) recorded from the Assembly.

        :param variables: either a single variable name or a list of variable\
            names. Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :type variables: str or list
        :param gather: Whether to collect data from all MPI nodes or just the\
            current node.

            .. note::
                This is irrelevant on sPyNNaker, which always behaves as if
                this parameter is True.

        :type gather: bool
        :param clear: \
            Whether recorded data will be deleted from the `Assembly`.
        :type clear: bool
        :param annotations: annotations to put on the neo block
        :type annotations: dict
        :rtype: neo.Block
        """
        if not gather:
            logger.warning(
                logger, "sPyNNaker only supports gather=True. We will run "
                "as if gather was set to True.")
        if annotations is not None:
            warn_once(
                logger, "Annoations Parameter is not standard PyNN so may not "
                        "be supported by all platformd.")

        return self._extract_neo_block(variables, None, clear, annotations)

    def get_data_by_indexes(
            self, variables, indexes, clear=False, annotations=None):
        """ Return a Neo `Block` containing the data\
            (spikes, state variables) recorded from the Assembly.

        :param variables: either a single variable name or a list of variable\
            names. Variables must have been previously recorded, otherwise an
            Exception will be raised.
        :type variables: str or list
        :param indexes: List of neuron indexes to include in the data.
            Clearly only neurons recording will actually have any data
            If None will be taken as all recording as get_data
        :type indexes: list (int)
        :param clear: Whether recorded data will be deleted.
        :type clear: bool
        :param annotations: annotations to put on the neo block
        :type annotations: dict
        :rtype: neo.Block
        """
        return self._extract_neo_block(variables, indexes, clear, annotations)

    def spinnaker_get_data(self, variable):
        """ Public accessor for getting data as a numpy array, instead of\
            the neo based object

        :param variable: \
            either a single variable name or a list of variable names.\
            Variables must have been previously recorded, otherwise an\
            Exception will be raised.
        :return: numpy array of the data
        """
        warn_once(
            logger, "spinnaker_get_data is non-standard PyNN and therefore "
            "may not be portable to other simulators. Nor do we guarantee "
            "that this function will exist in future releases.")
        if isinstance(variable, list):
            if len(variable) == 1:
                variable = variable[0]
            else:
                msg = "Only one type of data at a time is supported"
                raise ConfigurationException(msg)
        if variable == SPIKES:
            return self._get_spikes()
        return self._get_recorded_pynn7(variable)

    def get_spike_counts(self,  # pylint: disable=arguments-differ
                         gather=True):
        """ Return the number of spikes for each neuron.
        """
        spikes = self._get_spikes()
        return PyNNPopulationCommon.get_spike_counts(self, spikes, gather)

    def find_units(self, variable):
        """ Get the units of a variable

        :param variable: The name of the variable
        :return: The units of the variable
        """
        return self._get_variable_unit(variable)

    def set(self, **parameters):
        for parameter, value in iteritems(parameters):
            try:
                super(Population, self).set(parameter, value)
            except InvalidParameterType:
                super(Population, self)._initialize(parameter, value)

    def tset(self, **kwargs):
        logger.warning(
            "This function is deprecated; call pop.set(...) instead")
        for parameter, value in iteritems(kwargs):
            try:
                super(Population, self).set(parameter, value)
            except InvalidParameterType:
                super(Population, self)._initialize(parameter, value)

    def initialize(self, **kwargs):
        for parameter, value in iteritems(kwargs):
            super(Population, self)._initialize(parameter, value)

    @property
    def initial_values(self):
        if not self._vertex_population_initializable:
            raise KeyError(
                "Population does not support the initialisation")
        return self._vertex.initial_values

    # NON-PYNN API CALL
    def get_initial_value(self, variable, selector=None):
        """ See AbstractPopulationInitializable.get_initial_value
        """
        if not self._vertex_population_initializable:
            raise KeyError(
                "Population does not support the initialisation of {}".format(
                    variable))
        return self._vertex.get_initial_value(variable, selector)

    # NON-PYNN API CALL
    def set_initial_value(self, variable, value, selector=None):
        """ See AbstractPopulationInitializable.set_initial_value
        """
        if not self._vertex_population_initializable:
            raise KeyError(
                "Population does not support the initialisation of {}".format(
                    variable))
        if globals_variables.get_not_running_simulator().has_ran \
                and not self._vertex_changeable_after_run:
            raise Exception("Population does not support changes after run")
        self._vertex.set_initial_value(variable, value, selector)

    # NON-PYNN API CALL
    def get_initial_values(self, selector=None):
        """ See AbstractPopulationInitializable.get_initial_values
        """
        if not self._vertex_population_initializable:
            raise KeyError("Population does not support the initialisation")
        return self._vertex.get_initial_values(selector)

    @property
    def positions(self):
        """ Return the position array for structured populations.
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
        self._change_requires_mapping = True

    @property
    def all_cells(self):
        cells = []
        for _id in range(self._size):
            cells.append(IDMixin(self, _id))
        return cells

    @property
    def position_generator(self):
        def gen(i):
            return self.positions[:, i]
        return gen

    @staticmethod
    def create(cellclass, cellparams=None, n=1):
        """ Pass through method to the constructor defined by PyNN.\
        Create n cells all of the same type.\
        Returns a Population object.

        :param cellclass: see Population.__init__
        :param cellparams: see Population.__init__
        :param n: see Population.__init__(size...)
        :return: A New Population
        """
        return Population(size=n, cellclass=cellclass, cellparams=cellparams)
