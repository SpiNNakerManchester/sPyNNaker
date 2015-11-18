from pacman.model.constraints.abstract_constraints.abstract_constraint\
    import AbstractConstraint
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint

from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN import exceptions as local_exceptions
from spynnaker.pyNN.models.abstract_models.abstract_population_settable \
    import AbstractPopulationSettable
from spynnaker.pyNN.models.abstract_models.abstract_population_initializable\
    import AbstractPopulationInitializable
from spynnaker.pyNN.models.abstract_models.abstract_mappable \
    import AbstractMappable
from spynnaker.pyNN.models.neuron.input_types.input_type_conductance \
    import InputTypeConductance
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_gsyn_recordable \
    import AbstractGSynRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable \
    import AbstractVRecordable

from spinn_front_end_common.utilities import exceptions

from pyNN.space import Space

import numpy
import logging
import copy

logger = logging.getLogger(__name__)


class Population(object):
    """ A collection neuron of the same types. It encapsulates a type of\
        vertex used with Spiking Neural Networks, comprising n cells (atoms)\
        of the same model type.

    :param int size:
        size (number of cells) of the Population.
    :param cellclass:
        specifies the neural model to use for the Population
    :param dict cellparams:
        a dictionary containing model specific parameters and values
    :param structure:
        a spatial structure
    :param string label:
        a label identifying the Population
    :returns a list of vertexes and edges
    """

    _non_labelled_vertex_count = 0

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 structure=None):
        if size is not None and size <= 0:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative or zero size.")

        # Create a partitionable_graph vertex for the population and add it
        # to PACMAN
        cell_label = label
        if label is None:
            cell_label = "Population {}".format(
                Population._non_labelled_vertex_count)
            Population._non_labelled_vertex_count += 1

        # copy the parameters so that the end users are not exposed to the
        # additions placed by spinnaker.
        cellparams = copy.deepcopy(cellparams)

        # set spinnaker targeted parameters
        cellparams['label'] = cell_label
        cellparams['n_neurons'] = size
        cellparams['machine_time_step'] = spinnaker.machine_time_step
        cellparams['timescale_factor'] = spinnaker.timescale_factor

        # create population vertex.
        self._vertex = cellclass(**cellparams)
        self._spinnaker = spinnaker
        self._delay_vertex = None

        # Internal structure now supported 23 November 2014 ADR
        # structure should be a valid Space.py structure type.
        # generation of positions is deferred until needed.
        if structure:
            self._structure = structure
            self._positions = None
        else:
            self._structure = None

        self._spinnaker._add_population(self)
        self._spinnaker.add_vertex(self._vertex)

        # initialise common stuff
        self._size = size
        self._record_spike_file = None
        self._record_v_file = None
        self._record_gsyn_file = None

        # parameter
        self._change_requires_mapping = True

    @property
    def requires_mapping(self):
        if isinstance(self._vertex, AbstractMappable):
            return self._vertex.requires_mapping
        return self._change_requires_mapping

    def mark_no_changes(self):
        self._change_requires_mapping = False
        if isinstance(self._vertex, AbstractMappable):
            self._vertex.mark_no_changes()

    def __add__(self, other):
        """ Merges populations
        """
        # TODO: Make this add the neurons from another population to this one
        raise NotImplementedError

    def all(self):
        """ Iterator over cell ids on all nodes.
        """
        # TODO: Return the cells when we have such a thing
        raise NotImplementedError

    @property
    def conductance_based(self):
        """ True if the population uses conductance inputs
        """
        return isinstance(self._vertex.input_type, InputTypeConductance)

    @property
    def default_parameters(self):
        """ The default parameters of the vertex from this population
        :return:
        """
        return self._vertex.default_parameters

    def describe(self, template='population_default.txt', engine='default'):
        """
        Returns a human-readable description of the population.

        The output may be customised by specifying a different template
        together with an associated template engine (see ``pyNN.descriptions``)

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        # TODO:
        raise NotImplementedError

    def __getitem__(self, index_or_slice):
        # TODO: Used to get a single cell - not yet supported
        raise NotImplementedError

    def get(self, parameter_name, gather=False):
        """ Get the values of a parameter for every local cell in the\
            population.
        """
        if isinstance(self._vertex, AbstractPopulationSettable):
            return self._vertex.get_value(parameter_name)
        raise KeyError("Population does not have a property {}".format(
            parameter_name))

    def _get_cell_position(self, cell_id):
        """ Get the position of a cell.
        """
        # TODO: This isn't part of the API - is it ever used?
        if self._structure is None:
            raise ValueError("Attempted to get the position of a cell "
                             "in an un-structured population")
        elif self._positions is None:
            self._structure.generate_positions(self._vertex.n_atoms)
        return self._positions[cell_id]

    def _get_cell_initial_value(self, cell_id, variable):
        """ Get a given cells initial value
        """
        # TODO: Remove?  This isn't in the API...
        raise NotImplementedError

    # noinspection PyPep8Naming
    def getSpikes(self, compatible_output=False, gather=True):
        """
        Return a 2-column numpy array containing cell ids and spike times for\
        recorded cells.
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will "
                        " execute as if gather was true anyhow")

        if isinstance(self._vertex, AbstractSpikeRecordable):
            if not self._vertex.is_recording_spikes():
                raise exceptions.ConfigurationException(
                    "This population has not been set to record spikes. "
                    "Therefore spikes cannot be retrieved. Please set this "
                    "vertex to record spikes before running this command.")
        else:
            raise exceptions.ConfigurationException(
                "This poplation has not got the capability to record spikes. "
                "Therefore spikes cannot be retrieved or asked to be recorded."
                " Please readjust your PyNN script and try again.")

        if not self._spinnaker.has_ran:
            raise local_exceptions.SpynnakerException(
                "The simulation has not yet run, therefore spikes cannot"
                " be retrieved. Please execute the simulation before"
                " running this command")

        spikes = self._vertex.get_spikes(
            self._spinnaker.transceiver,
            self._spinnaker.no_machine_time_steps,
            self._spinnaker.placements, self._spinnaker.graph_mapper)

        return spikes

    def get_spike_counts(self, gather=True):
        """ Return the number of spikes for each neuron.
        """
        spikes = self.getSpikes(True, gather)
        n_spikes = {}
        counts = numpy.bincount(spikes[:, 0].astype(dtype="uint32"),
                                minlength=self._vertex.n_atoms)
        for i in range(self._vertex.n_atoms):
            n_spikes[i] = counts[i]
        return n_spikes

    # noinspection PyUnusedLocal
    def get_gsyn(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time and synaptic
        conductances for recorded cells.
        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        """

        if isinstance(self._vertex, AbstractGSynRecordable):
            if not self._vertex.is_recording_gsyn():
                raise exceptions.ConfigurationException(
                    "This population has not been set to record gsyn. "
                    "Therefore gsyn cannot be retrieved. Please set this "
                    "vertex to record gsyn before running this command.")
        else:
            raise exceptions.ConfigurationException(
                "This poplation has not got the capability to record gsyn. "
                "Therefore gsyn cannot be retrieved or asked to be recorded. "
                "Please readjust your PyNN script and try again.")

        if not self._spinnaker.has_ran:
            raise local_exceptions.SpynnakerException(
                "The simulation has not yet run, therefore gsyn cannot"
                " be retrieved. Please execute the simulation before"
                " running this command")

        # check that the vertex has read up to the position it needs to
        return self._vertex.get_gsyn(
            self._spinnaker.transceiver,
            self._spinnaker.no_machine_time_steps,
            self._spinnaker.placements, self._spinnaker.graph_mapper)

    # noinspection PyUnusedLocal
    def get_v(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and Vm for
        recorded cells.

        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        """
        if isinstance(self._vertex, AbstractVRecordable):
            if not self._vertex.is_recording_v():
                raise exceptions.ConfigurationException(
                    "This population has not been set to record v. "
                    "Therefore v cannot be retrieved. Please set this "
                    "vertex to record v before running this command.")
        else:
            raise exceptions.ConfigurationException(
                "This poplation has not got the capability to record v. "
                "Therefore v cannot be retrieved or asked to be recorded. "
                "Please readjust your PyNN script and try again.")

        if not self._spinnaker.has_ran:
            raise local_exceptions.SpynnakerException(
                "The simulation has not yet run, therefore v cannot"
                " be retrieved. Please execute the simulation before"
                " running this command")

        # check that the vertex has read up to the position it needs to
        return self._vertex.get_v(
            self._spinnaker.transceiver,
            self._spinnaker.no_machine_time_steps,
            self._spinnaker.placements, self._spinnaker.graph_mapper)

    def id_to_index(self, cell_id):
        """
        Given the ID(s) of cell(s) in the Population, return its (their) index
        (order in the Population).
        """

        # TODO: Need __getitem__
        raise NotImplementedError

    def id_to_local_index(self, cell_id):
        """
        Given the ID(s) of cell(s) in the Population, return its (their) index
        (order in the Population), counting only cells on the local MPI node.
        """
        # TODO: Need __getitem__
        raise NotImplementedError

    def initialize(self, variable, value):
        """
        Set the initial value of one of the state variables of the neurons in
        this population.

        """
        if not isinstance(self._vertex, AbstractPopulationInitializable):
            raise KeyError(
                "Population does not support the initialization of {}".format(
                    variable))
        self._vertex.initialize(variable, utility_calls.convert_param_to_numpy(
            value, self._vertex.n_atoms))
        self._change_requires_mapping = True

    @staticmethod
    def is_local(cell_id):
        """
        Determine whether the cell with the given ID exists on the local
        MPI node.
        :param cell_id:
        """

        # Doesn't really mean anything on SpiNNaker
        return True

    def can_record(self, variable):
        """ Determine whether `variable` can be recorded from this population.
        """

        # TODO: Needs a more precise recording mechanism (coming soon)
        raise NotImplementedError

    def inject(self, current_source):
        """
        Connect a current source to all cells in the Population.
        """

        # TODO:
        raise NotImplementedError

    def __iter__(self):
        """
        suppose to iterate over local cells
        """

        # TODO:
        raise NotImplementedError

    def __len__(self):
        """
        Returns the total number of cells in the population.
        """
        return self._size

    @property
    def label(self):
        """
        label of the population
        :return:
        """
        return self._vertex.label

    @property
    def local_size(self):
        """
        returns the number of local cells
        """

        # Doesn't make much sense on SpiNNaker
        return self._size

    # noinspection PyPep8Naming
    def meanSpikeCount(self, gather=True):
        """
        Returns the mean number of spikes per neuron.
        :param gather: gather has no meaning in spinnaker, always set to true
        :return: an array whcih contains the avg spike rate per neuron
        """
        return self.mean_spike_count(gather)

    def mean_spike_count(self, gather=True):
        """
        Returns the mean number of spikes per neuron.
        """
        spike_counts = self.get_spike_counts(gather)
        total_spikes = sum(spike_counts.values())
        return total_spikes / self._size

    def nearest(self, position):
        """ Return the neuron closest to the specified position.
        """
        if self._structure is None:
            raise ValueError("attempted to retrieve positions "
                             "for an un-structured population")
        elif self._positions is None:
            self._structure.generate_positions(self._vertex.n_atoms)
        position_diff = numpy.empty(self._positions.shape)
        position_diff.fill(position)
        distances = Space.distances(self._positions, position_diff)
        return distances.argmin()

    @property
    def position_generator(self):
        """ Returns a position generator.
        """
        if self._structure is None:
            raise ValueError("attempted to retrieve positions "
                             "for an un-structured population")
        else:
            return self._structure.generate_positions

    # noinspection PyPep8Naming
    def randomInit(self, distribution):
        """
        Set initial membrane potentials for all the cells in the population to
        random values.

        :param `pyNN.random.RandomDistribution` distribution:
            the distribution used to draw random values.

        """
        self.initialize('v', distribution)
        self._change_requires_mapping = True

    def record(self, to_file=None):
        """ Record spikes from all cells in the Population.

        :param to_file: file to write the spike data to
        """

        if not isinstance(self._vertex, AbstractSpikeRecordable):
            raise Exception(
                "This population does not support the recording of spikes!")

        # Tell the vertex to record spikes
        self._vertex.set_recording_spikes()

        # set the file to store the spikes in once retrieved
        self._record_spike_file = to_file

        # state that something has changed in the population,
        self._change_requires_mapping = True

    def record_gsyn(self, to_file=None):
        """ Record the synaptic conductance for all cells in the Population.

        :param to_file: the file to write the recorded gsyn to.
        """
        if not isinstance(self._vertex, AbstractGSynRecordable):
            raise Exception(
                "This population does not support the recording of gsyn")
        if not isinstance(self._vertex.input_type, InputTypeConductance):
            logger.warn(
                "You are trying to record the conductance from a model which "
                "does not use conductance input.  You will receive "
                "current measurements instead.")
        self._vertex.set_recording_gsyn()
        self._record_gsyn_file = to_file

        # state that something has changed in the population,
        self._change_requires_mapping = True

    def record_v(self, to_file=None):
        """ Record the membrane potential for all cells in the Population.

        :param to_file: the file to write the recorded v to.
        """
        if not isinstance(self._vertex, AbstractVRecordable):
            raise Exception(
                "This population does not support the recording of v")

        self._vertex.set_recording_v()
        self._record_v_file = to_file

        # state that something has changed in the population,
        self._change_requires_mapping = True

    @property
    def positions(self):
        """ Return the position array for structured populations.
        """
        if self._structure is None:
            raise ValueError("attempted to retrieve positions "
                             "for an unstructured population")
        elif self._positions is None:
            self._positions = self._structure.generate_positions(
                self._vertex.n_atoms)
        return self._positions

    # noinspection PyPep8Naming
    def printSpikes(self, filename, gather=True):
        """ Write spike time information from the population to a given file.
        :param filename: the absolute file path for where the spikes are to\
                    be printed in
        :param gather: Supported from the PyNN language, but ignored here
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        spikes = self.getSpikes(compatible_output=True)
        if spikes is not None:
            first_id = 0
            num_neurons = self._vertex.n_atoms
            dimensions = self._vertex.n_atoms
            last_id = self._vertex.n_atoms - 1
            utility_calls.check_directory_exists_and_create_if_not(filename)
            spike_file = open(filename, "w")
            spike_file.write("# first_id = {}\n".format(first_id))
            spike_file.write("# n = {}\n".format(num_neurons))
            spike_file.write("# dimensions = [{}]\n".format(dimensions))
            spike_file.write("# last_id = {}\n".format(last_id))
            for (neuronId, time) in spikes:
                spike_file.write("{}\t{}\n".format(time, neuronId))
            spike_file.close()

    def print_gsyn(self, filename, gather=True):
        """ Write conductance information from the population to a given file.
        :param filename: the absolute file path for where the gsyn are to be\
                    printed in
        :param gather: Supported from the PyNN language, but ignored here
        """
        time_step = (self._spinnaker.machine_time_step * 1.0) / 1000.0
        gsyn = self.get_gsyn(gather, compatible_output=True)
        first_id = 0
        num_neurons = self._vertex.n_atoms
        dimensions = self._vertex.n_atoms
        utility_calls.check_directory_exists_and_create_if_not(filename)
        file_handle = open(filename, "w")
        file_handle.write("# first_id = {}\n".format(first_id))
        file_handle.write("# n = {}\n".format(num_neurons))
        file_handle.write("# dt = {}\n".format(time_step))
        file_handle.write("# dimensions = [{}]\n".format(dimensions))
        file_handle.write("# last_id = {{}}\n".format(num_neurons - 1))
        file_handle = open(filename, "w")
        for (neuronId, time, value_e, value_i) in gsyn:
            file_handle.write("{}\t{}\t{}\t{}\n".format(
                time, neuronId, value_e, value_i))
        file_handle.close()

    def print_v(self, filename, gather=True):
        """ Write membrane potential information from the population to a\
            given file.
        :param filename: the absolute file path for where the voltage are to\
                     be printed in
        :param gather: Supported from the PyNN language, but ignored here
        """
        time_step = (self._spinnaker.machine_time_step * 1.0) / 1000.0
        v = self.get_v(gather, compatible_output=True)
        utility_calls.check_directory_exists_and_create_if_not(filename)
        file_handle = open(filename, "w")
        first_id = 0
        num_neurons = self._vertex.n_atoms
        dimensions = self._vertex.n_atoms
        file_handle.write("# first_id = {}\n".format(first_id))
        file_handle.write("# n = {}\n".format(num_neurons))
        file_handle.write("# dt = {}\n".format(time_step))
        file_handle.write("# dimensions = [{}]\n".format(dimensions))
        file_handle.write("# last_id = {}\n".format(num_neurons - 1))
        for (neuronId, time, value) in v:
            file_handle.write("{}\t{}\t{}\n".format(time, neuronId, value))
        file_handle.close()

    def rset(self, parametername, rand_distr):
        """
        'Random' set. Set the value of parametername to a value taken from
        rand_distr, which should be a RandomDistribution object.
        :param parametername: the parameter to set
        :param rand_distr: the random distribution object to set the parameter\
                     to
        """
        self.set(parametername, rand_distr)

        # state that something has changed in the population,
        self._change_requires_mapping = True

    def sample(self, n, rng=None):
        """ Return a random selection of neurons from a population in the form\
            of a population view
        :param n: the number of neurons to sample
        :param rng: the random number generator to use.
        """

        # TODO: Need PopulationView support
        raise NotImplementedError

    def save_positions(self, file):
        """ Save positions to file.
        :param file: the file to write the positions to.
        """
        if self._structure is None:
            raise ValueError("attempted to retrieve positions "
                             "for an un-structured population")
        elif self._positions is None:
            self._structure.generate_positions(self._vertex.n_atoms)
        file_handle = open(file, "w")
        file_handle.write(self._positions)
        file_handle.close()

    def _set_cell_initial_value(self, cell_id, variable, value):
        """ Set a given cells initial value
        """
        # TODO: Remove? Not part of API...
        raise NotImplementedError

    def _set_cell_position(self, cell_id, pos):
        """ Sets a cell to a given position
        """
        # TODO: Remove?  This is never called
        if self._structure is None:
            raise ValueError("attempted to set a position for a cell "
                             "in an un-structured population")
        elif self._positions is None:
            self._structure.generate_positions(self._vertex.n_atoms)
        self._positions[cell_id] = pos

        # state that something has changed in the population,
        self._change_requires_mapping = True

    def _set_positions(self, positions):
        """ Sets all the positions in the population.
        """
        # TODO: Remove?  This is never used
        if self._structure is None:
            raise ValueError("attempted to set positions "
                             "in an un-structured population")
        else:
            self._positions = positions

        # state that something has changed in the population,
        self._change_requires_mapping = True

    def set(self, parameter, value=None):
        """
        Set one or more parameters for every cell in the population.

        param can be a dict, in which case val should not be supplied, or a
        string giving the parameter name, in which case val is the parameter
        value. val can be a numeric value, or list of such
        (e.g. for setting spike times)::

          p.set("tau_m", 20.0).
          p.set({'tau_m':20, 'v_rest':-65})
        :param parameter: the parameter to set
        :param value: the value of the parameter to set.
        """
        if not isinstance(self._vertex, AbstractPopulationSettable):
            raise KeyError("Population does not have property {}".format(
                parameter))

        if type(parameter) is str:
            if value is None:
                raise Exception("Error: No value given in set() function for "
                                "population parameter. Exiting.")
            self._vertex.set_value(parameter, value)
            return

        if type(parameter) is not dict:
                raise Exception("Error: invalid parameter type for "
                                "set() function for population parameter."
                                " Exiting.")

        # Add a dictionary-structured set of new parameters to the current set:
        for (key, value) in parameter.iteritems():
            self._vertex.set_value(key, value)

        # state that something has changed in the population,
        self._change_requires_mapping = True

    @property
    def structure(self):
        """ Return the structure for the population.
        """
        return self._structure

    # NONE PYNN API CALL
    def set_constraint(self, constraint):
        """
        Apply a constraint to a population that restricts the processor
        onto which its sub-populations will be placed.
        """
        if isinstance(constraint, AbstractConstraint):
            self._vertex.add_constraint(constraint)
        else:
            raise exceptions.ConfigurationException(
                "the constraint entered is not a recongised constraint. "
                "try again")

        # state that something has changed in the population,
        self._change_requires_mapping = True

    # NONE PYNN API CALL
    def add_placement_constraint(self, x, y, p=None):
        """ Add a placement constraint

        :param x: The x-coordinate of the placement constraint
        :type x: int
        :param y: The y-coordinate of the placement constraint
        :type y: int
        :param p: The processor id of the placement constraint (optional)
        :type p: int
        """
        self._vertex.add_constraint(PlacerChipAndCoreConstraint(x, y, p))

        # state that something has changed in the population,
        self._change_requires_mapping = True

    # NONE PYNN API CALL
    def set_mapping_constraint(self, constraint_dict):
        """ Add a placement constraint - for backwards compatibility

        :param constraint_dict: A dictionary containing "x", "y" and\
                    optionally "p" as keys, and ints as values
        :type constraint_dict: dict of str->int
        """
        self.add_placement_constraint(**constraint_dict)

        # state that something has changed in the population,
        self._change_requires_mapping = True

    # NONE PYNN API CALL
    def set_model_based_max_atoms_per_core(self, new_value):
        """ Supports the setting of each models max atoms per core parameter

        :param new_value: the new value for the max atoms per core.
        """
        if hasattr(self._vertex, "set_model_max_atoms_per_core"):
            self._vertex.set_model_max_atoms_per_core(new_value)
        else:
            raise exceptions.ConfigurationException(
                "This population does not support its max_atoms_per_core "
                "variable being adjusted by the end user. Sorry")

        # state that something has changed in the population,
        self._change_requires_mapping = True

    @property
    def size(self):
        """ The number of neurons in the population
        :return:
        """
        return self._vertex.n_atoms

    def tset(self, parametername, value_array):
        """
        'Topographic' set. Set the value of parametername to the values in
        value_array, which must have the same dimensions as the Population.
        :param parametername: the name of the parameter
        :param value_array: the array of values which must have the correct\
                number of elements.
        """
        if len(value_array) != self._vertex.n_atoms:
            raise exceptions.ConfigurationException(
                "To use Tset, you must have a array of values which matches "
                "the size of the population. Please change this and try "
                "again, or alternatively, use set()")
        self.set(parametername, value_array)

        # state that something has changed in the population,
        self._change_requires_mapping = True

    def _end(self):
        """ Do final steps at the end of the simulation
        """
        if self._record_spike_file is not None:
            self.printSpikes(self._record_spike_file)
        if self._record_v_file is not None:
            self.print_v(self._record_v_file)
        if self._record_gsyn_file is not None:
            self.print_gsyn(self._record_gsyn_file)

    @property
    def _get_vertex(self):
        return self._vertex

    @property
    def _internal_delay_vertex(self):
        return self._delay_vertex

    @_internal_delay_vertex.setter
    def _internal_delay_vertex(self, delay_vertex):
        self._delay_vertex = delay_vertex
