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
from six import string_types, iteritems
from spinn_utilities.log import FormatAdapter
from collections import Iterable

from pacman.model.constraints import AbstractConstraint
from pacman.model.constraints.placer_constraints import ChipAndCoreConstraint
from pacman.model.constraints.partitioner_constraints import (
    MaxVertexAtomsConstraint)
from pacman.model.graphs.application.application_vertex import (
    ApplicationVertex)

from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun

from spynnaker.pyNN.models.abstract_models import (
    AbstractReadParametersBeforeSet, AbstractContainsUnits,
    AbstractPopulationInitializable, AbstractPopulationSettable)
from spynnaker.pyNN.utilities import constants
from .abstract_pynn_model import AbstractPyNNModel
from .neuron.pynn_partition_vertex import PyNNPartitionVertex
from spynnaker.pyNN.models.spike_source.rate_source_live_partition import RateSourceLivePartition

logger = FormatAdapter(logging.getLogger(__file__))


class PyNNPopulationCommon(object):
    __slots__ = [
        "_all_ids",
        "__change_requires_mapping",
        "__delay_vertex",
        "__first_id",
        "__has_read_neuron_parameters_this_run",
        "__last_id",
        "_positions",
        "__record_gsyn_file",
        "__record_spike_file",
        "__record_v_file",
        "_size",
        "__spinnaker_control",
        "__structure",
        "__vertex",
        "_vertex_changeable_after_run",
        "_vertex_contains_units",
        "_vertex_population_initializable",
        "_vertex_population_settable",
        "_vertex_read_parameters_before_set",
        "__label"]

    def __init__(
            self, spinnaker_control, size, label, constraints, model,
            structure, initial_values, additional_parameters=None,
            in_partitions=None, out_partitions=None, n_targets=None, wc_time=None):
        # pylint: disable=too-many-arguments
        size = self._roundsize(size, label)

        self.__spinnaker_control = spinnaker_control
        self.__delay_vertex = None
        self.__label = label

        # Use a provided model to create a vertex
        if isinstance(model, AbstractPyNNModel):
            if size is not None and size <= 0:
                raise ConfigurationException(
                    "A population cannot have a negative or zero size.")
            population_parameters = dict(model.default_population_parameters)
            if additional_parameters is not None:
                population_parameters.update(additional_parameters)
            if in_partitions is not None and out_partitions is not None:
                population_parameters["in_partitions"] = in_partitions
                population_parameters["out_partitions"] = out_partitions
            if n_targets is not None:
                population_parameters["n_targets"] = n_targets
            if wc_time is not None:
                population_parameters["wc_time"] = wc_time
            vertex = model.create_vertex(
                size, label, constraints, **population_parameters)

            if isinstance(vertex, Iterable):
                self.__vertex = vertex
            else:
                self.__vertex = list()
                self.__vertex.append(vertex)

            for v in self.__vertex:
                if isinstance(v, PyNNPartitionVertex) or isinstance(v, RateSourceLivePartition):
                    v.add_internal_edges_and_vertices(self.__spinnaker_control)
                else:
                    for app_vertex in v.out_vertices:
                        self.__spinnaker_control.add_application_vertex(app_vertex)

        # Use a provided application vertex directly
        elif isinstance(model, ApplicationVertex):
            if additional_parameters is not None:
                raise ConfigurationException(
                    "Cannot accept additional parameters {} when the cell is"
                    " a vertex".format(additional_parameters))
            self.__vertex = []
            self.__vertex.append(model)
            if size is None:
                size = self.__vertex[0].n_atoms
            elif size != self.__vertex[0].n_atoms:
                raise ConfigurationException(
                    "Vertex size does not match Population size")
            if label is not None:
                self.__vertex[0].set_label(label)
            if constraints is not None:
                self.__vertex[0].add_constraints(constraints)
            self.__spinnaker_control.add_application_vertex(self.__vertex[0])

        # Fail on anything else
        else:
            raise ConfigurationException(
                "Model must be either an AbstractPyNNModel or an"
                " ApplicationVertex")

        # Introspect properties of the vertex
        self._vertex_population_settable = \
            isinstance(self.__vertex[0], AbstractPopulationSettable)
        self._vertex_population_initializable = \
            isinstance(self.__vertex[0], AbstractPopulationInitializable)
        self._vertex_changeable_after_run = \
            isinstance(self.__vertex[0], AbstractChangableAfterRun)
        self._vertex_read_parameters_before_set = \
            isinstance(self.__vertex[0], AbstractReadParametersBeforeSet)
        self._vertex_contains_units = \
            isinstance(self.__vertex[0], AbstractContainsUnits)

        # Internal structure now supported 23 November 2014 ADR
        # structure should be a valid Space.py structure type.
        # generation of positions is deferred until needed.
        self.__structure = structure
        self._positions = None

        # add objects to the SpiNNaker control class
        self.__spinnaker_control.add_population(self)

        # initialise common stuff
        self._size = size
        self.__record_spike_file = None
        self.__record_v_file = None
        self.__record_gsyn_file = None

        # parameter
        self.__change_requires_mapping = True
        self.__has_read_neuron_parameters_this_run = False

        # things for pynn demands
        self._all_ids = numpy.arange(
            globals_variables.get_simulator().id_counter,
            globals_variables.get_simulator().id_counter + size)
        self.__first_id = self._all_ids[0]
        self.__last_id = self._all_ids[-1]

        # update the simulators id_counter for giving a unique ID for every
        # atom
        globals_variables.get_simulator().id_counter += size

        # set up initial values if given
        if initial_values is not None:
            for variable, value in iteritems(initial_values):
                self._initialize(variable, value)

    @property
    def first_id(self):
        return self.__first_id

    @property
    def last_id(self):
        return self.__last_id

    @property
    def _structure(self):
        return self.__structure

    @property
    def _vertex(self):
        return self.__vertex

    @property
    def requires_mapping(self):
        return self.__change_requires_mapping

    @requires_mapping.setter
    def requires_mapping(self, new_value):
        self.__change_requires_mapping = new_value

    def mark_no_changes(self):
        self.__change_requires_mapping = False
        self.__has_read_neuron_parameters_this_run = False

    def __add__(self, other):
        """ Merges populations
        """
        # TODO: Make this add the neurons from another population to this one
        raise NotImplementedError

    def all(self):
        """ Iterator over cell IDs on all nodes.
        """
        # TODO: Return the cells when we have such a thing
        raise NotImplementedError

    @property
    def conductance_based(self):
        """ True if the population uses conductance inputs
        """
        if hasattr(self.__vertex[0], "conductance_based"):
            return self.__vertex[0].conductance_based
        return False

    def __getitem__(self, index_or_slice):
        # Note: This is supported by sPyNNaker8
        # TODO: Used to get a single cell - not yet supported
        raise NotImplementedError

    def get(self, parameter_names, gather=False):
        """ Get the values of a parameter for every local cell in the\
            population.

        :param parameter_names: Name of parameter. This is either a single\
            string or a list of strings
        :return: A single list of values (or possibly a single value) if\
            paramter_names is a string, or a dict of these if parameter names\
            is a list.
        :rtype: str or list(str) or dict(str,str) or dict(str,list(str))
        """
        if not self._vertex_population_settable:
            raise KeyError("Population does not support setting")
        if isinstance(parameter_names, string_types):
            return self.__vertex[0].get_value(parameter_names)
        results = dict()
        for parameter_name in parameter_names:
            results[parameter_name] = self.__vertex[0].get_value(parameter_name)
        return results

    # NON-PYNN API CALL
    def get_by_selector(self, selector, parameter_names):
        """ Get the values of a parameter for the selected cell in the\
            population.

        :param parameter_names: Name of parameter. This is either a\
            single string or a list of strings
        :param selector: a description of the subrange to accept. \
            Or None for all. \
            See: _selector_to_ids in \
            SpiNNUtils.spinn_utilities.ranged.abstract_sized.py
        :return: A single list of values (or possibly a single value) if\
            paramter_names is a string or a dict of these if parameter names\
            is a list.
        :rtype: str or list(str) or dict(str,str) or dict(str,list(str))
        """
        if not self._vertex_population_settable:
            raise KeyError("Population does not support setting")
        if isinstance(parameter_names, string_types):
            return self.__vertex[0].get_value_by_selector(
                selector, parameter_names)
        results = dict()
        for parameter_name in parameter_names:
            results[parameter_name] = self.__vertex[0].get_value_by_selector(
                selector, parameter_name)
        return results

    def id_to_index(self, id):  # @ReservedAssignment
        """ Given the ID(s) of cell(s) in the Population, return its (their)\
            index (order in the Population).
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
        """
        # TODO: Need __getitem__
        raise NotImplementedError

    def _initialize(self, variable, value):
        """ Set the initial value of one of the state variables of the neurons\
            in this population.
        """
        if not self._vertex_population_initializable:
            raise KeyError(
                "Population does not support the initialisation of {}".format(
                    variable))
        if globals_variables.get_not_running_simulator().has_ran \
                and not self._vertex_changeable_after_run:
            raise Exception("Population does not support changes after run")
        self._read_parameters_before_set()
        self.__vertex[0].initialize(variable, value)

    def can_record(self, variable):
        """ Determine whether `variable` can be recorded from this population.

        Note: This is supported by sPyNNaker8
        """

        # TODO: Needs a more precise recording mechanism (coming soon)
        raise NotImplementedError

    def inject(self, current_source):
        """ Connect a current source to all cells in the Population.
        """

        # TODO:
        raise NotImplementedError

    def __iter__(self):
        """ Iterate over local cells

        Note: This is supported by sPyNNaker8
        """

        # TODO:
        raise NotImplementedError

    def __len__(self):
        """ Get the total number of cells in the population.
        """
        return self._size

    @property
    def label(self):
        """ The label of the population
        """
        return self.__label

    @label.setter
    def label(self, label):
        raise NotImplementedError(
            "As label is used as an ID it can not be changed")

    @property
    def local_size(self):
        """ The number of local cells
        """
        # Doesn't make much sense on SpiNNaker
        return self._size

    def _set_check(self, parameter, value):
        """ Checks for various set methods.
        """
        if not self._vertex_population_settable:
            raise KeyError("Population does not have property {}".format(
                parameter))

        if globals_variables.get_not_running_simulator().has_ran \
                and not self._vertex_changeable_after_run:
            raise Exception(
                " run has been called")

        if isinstance(parameter, string_types):
            if value is None:
                raise Exception("A value (not None) must be specified")
        elif type(parameter) is not dict:
            raise Exception(
                "Parameter must either be the name of a single parameter to"
                " set, or a dict of parameter: value items to set")

        self._read_parameters_before_set()

    def set(self, parameter, value=None):
        """ Set one or more parameters for every cell in the population.

        param can be a dict, in which case value should not be supplied, or a\
        string giving the parameter name, in which case value is the parameter\
        value. value can be a numeric value, or list of such\
        (e.g. for setting spike times)::

            p.set("tau_m", 20.0).
            p.set({'tau_m':20, 'v_rest':-65})

        :param parameter: the parameter to set
        :type parameter: str or dict
        :param value: the value of the parameter to set.
        """
        self._set_check(parameter, value)

        # set new parameters
        if isinstance(parameter, string_types):
            if value is None:
                raise Exception("A value (not None) must be specified")
            self.__vertex[0].set_value(parameter, value)
            return
        for (key, value) in parameter.iteritems():
            self.__vertex[0].set_value(key, value)

    # NON-PYNN API CALL
    def set_by_selector(self, selector, parameter, value=None):
        """ Set one or more parameters for selected cell in the population.

        param can be a dict, in which case value should not be supplied, or a\
        string giving the parameter name, in which case value is the parameter\
        value. value can be a numeric value, or list of such
        (e.g. for setting spike times)::

            p.set("tau_m", 20.0).
            p.set({'tau_m':20, 'v_rest':-65})

        :param selector: See RangedList.set_value_by_selector as this is just \
            a pass through method
        :param parameter: the parameter to set
        :param value: the value of the parameter to set.
        """
        self._set_check(parameter, value)

        # set new parameters
        if type(parameter) is str:
            self.__vertex[0].set_value_by_selector(selector, parameter, value)
        else:
            for (key, value) in parameter.iteritems():
                self.__vertex[0].set_value_by_selector(selector, key, value)

    def _read_parameters_before_set(self):
        """ Reads parameters from the machine before "set" completes

        :return: None
        """

        # If the tools have run before, and not reset, and the read
        # hasn't already been done, read back the data
        if globals_variables.get_simulator().has_ran \
                and self._vertex_read_parameters_before_set \
                and not self.__has_read_neuron_parameters_this_run \
                and not globals_variables.get_simulator().use_virtual_board:
            # locate machine vertices from the application vertices

            if isinstance(self.__vertex[0], PyNNPartitionVertex):
                self.__vertex[0].read_parameters_from_machine(globals_variables)
            else:
                machine_vertices = globals_variables.get_simulator().graph_mapper\
                    .get_machine_vertices(self.__vertex)

                # go through each machine vertex and read the neuron parameters
                # it contains
                for machine_vertex in machine_vertices:

                    # tell the core to rewrite neuron params back to the
                    # SDRAM space.
                    placement = globals_variables.get_simulator().placements.\
                        get_placement_of_vertex(machine_vertex)

                    self.__vertex.read_parameters_from_machine(
                        globals_variables.get_simulator().transceiver, placement,
                        globals_variables.get_simulator().graph_mapper.get_slice(
                            machine_vertex))

            self.__has_read_neuron_parameters_this_run = True

    def get_spike_counts(self, spikes, gather=True):
        """ Return the number of spikes for each neuron.
        """
        n_spikes = {}
        counts = numpy.bincount(spikes[:, 0].astype(dtype=numpy.int32),
                                minlength=self.__vertex[0].n_atoms)
        for i in range(self.__vertex[0].n_atoms):
            n_spikes[i] = counts[i]
        return n_spikes

    def get_synapse_id_by_target(self, target):
        return self._vertex[0].get_synapse_id_by_target(target)
    
    @property
    def positions(self):
        """ Return the position array for structured populations.
        """
        if self._positions is None:
            if self.__structure is None:
                raise ValueError("attempted to retrieve positions "
                                 "for an unstructured population")
            self._positions = self.__structure.generate_positions(
                self.__vertex[0].n_atoms)
        return self._positions

    @property
    def structure(self):
        """ Return the structure for the population.
        """
        return self.__structure

    # NON-PYNN API CALL
    def set_constraint(self, constraint):
        """ Apply a constraint to a population that restricts the processor\
            onto which its atoms will be placed.
        """
        globals_variables.get_simulator().verify_not_running()
        if not isinstance(constraint, AbstractConstraint):
            raise ConfigurationException(
                "the constraint entered is not a recognised constraint")

        self.__vertex[0].add_constraint(constraint)
        # state that something has changed in the population,
        self.__change_requires_mapping = True

    # NON-PYNN API CALL
    def add_placement_constraint(self, x, y, p=None):
        """ Add a placement constraint

        :param x: The x-coordinate of the placement constraint
        :type x: int
        :param y: The y-coordinate of the placement constraint
        :type y: int
        :param p: The processor ID of the placement constraint (optional)
        :type p: int
        """
        globals_variables.get_simulator().verify_not_running()
        self.__vertex[0].add_constraint(ChipAndCoreConstraint(x, y, p))

        # state that something has changed in the population,
        self.__change_requires_mapping = True

    # NON-PYNN API CALL
    def set_mapping_constraint(self, constraint_dict):
        """ Add a placement constraint - for backwards compatibility

        :param constraint_dict: A dictionary containing "x", "y" and\
            optionally "p" as keys, and ints as values
        :type constraint_dict: dict(str, int)
        """
        globals_variables.get_simulator().verify_not_running()
        self.add_placement_constraint(**constraint_dict)

        # state that something has changed in the population,
        self.__change_requires_mapping = True

    # NON-PYNN API CALL
    def set_max_atoms_per_core(self, max_atoms_per_core):
        """ Supports the setting of this population's max atoms per core

        :param max_atoms_per_core: the new value for the max atoms per core.
        """
        globals_variables.get_simulator().verify_not_running()
        self.__vertex[0].add_constraint(
            MaxVertexAtomsConstraint(max_atoms_per_core))
        # state that something has changed in the population
        self.__change_requires_mapping = True

    @property
    def size(self):
        """ The number of neurons in the population
        """
        atoms = 0
        for v in self.__vertex:
            atoms += v.n_atoms
        return atoms

    @property
    def _get_vertex(self):
        return self.__vertex[0]

    #@property
    #def get_syn_vertices(self):
    #    if len(self.__vertex) > 0:
    #        return self.__vertex[1:len(self.__vertex)]
    #    raise ConfigurationException(
    #        "There are not synapse vertices")

    @property
    def _internal_delay_vertex(self):
        return self.__delay_vertex

    @_internal_delay_vertex.setter
    def _internal_delay_vertex(self, delay_vertex):
        self.__delay_vertex = delay_vertex
        self.__change_requires_mapping = True

    def _get_variable_unit(self, parameter_name):
        """ Helper method for getting units from a parameter used by the vertex

        :param parameter_name: the parameter name to find the units for
        :return: the units in string form
        """
        if self._vertex_contains_units:
            return self.__vertex[0].get_units(parameter_name)
        raise ConfigurationException(
            "This population does not support describing its units")

    def _roundsize(self, size, label):
        if isinstance(size, int):
            return size
        # External device population can have a size of None so accept for now
        if size is None:
            return None
        # Allow a float which has a near int value
        temp = int(round(size))
        if abs(temp - size) < 0.001:
            logger.warning("Size of the population rounded "
                           "from {} to {}. Please use int values for size",
                           label, size, temp)
            return temp
        raise ConfigurationException(
            "Size of a population with label {} must be an int,"
            " received {}".format(label, size))
