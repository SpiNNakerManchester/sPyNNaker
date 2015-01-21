from pacman.model.constraints.abstract_constraint import AbstractConstraint
from pacman.model.constraints.vertex_has_dependent_constraint import \
    VertexHasDependentConstraint
from pacman.model.constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from spynnaker.pyNN.models.abstract_models.abstract_population_vertex \
    import AbstractPopulationVertex
from pacman.model.constraints.vertex_requires_multi_cast_source_constraint \
    import VertexRequiresMultiCastSourceConstraint
from pacman.model.partitionable_graph.partitionable_edge \
    import PartitionableEdge
from pacman.utilities import utility_calls as pacman_utility_calls
from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex

from pyNN.space import Space

from spynnaker.pyNN.models.utility_models.command_sender \
    import CommandSender
from spynnaker.pyNN.utilities.parameters_surrogate\
    import PyNNParametersSurrogate
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN import exceptions

import numpy
import logging

logger = logging.getLogger(__name__)


class Population(object):
    """
    A collection neuron of the same types. It encapsulates a type of
    :class:`pacman103.lib.partitionable_graph.AbstractConstrainedVertex`
    used with Spiking Neural Networks, comprising n cells (atoms)
    of the same :py:mod:`pacman103.front.pynn.models` type.

    :param int size:
        size (number of cells) of the Population.
    :param `pacman103.front.pynn.models` cellclass:
        specifies the neural model to use for the Population
    :param dict cellparams:
        a dictionary containing model specific parameters and values
    :param `pyNN.space` structure:
        a spatial structure
    :param string label:
        a label identifying the Population
    :returns a list of vertexes and edges
    """

    _non_labelled_vertex_count = 0

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 multi_cast_vertex=None, structure=None):
        """
        Instantiates a :py:object:`Population`.
        """
        if size <= 0:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative or zero size.")

        # Create a partitionable_graph vertex for the population and add it
        # to PACMAN
        cell_label = label
        if label is None:
            cell_label = "Population {}"\
                         .format(Population._non_labelled_vertex_count)
            Population._non_labelled_vertex_count += 1
        cellparams['label'] = cell_label
        cellparams['n_neurons'] = size
        cellparams['machine_time_step'] = spinnaker.machine_time_step
        cellparams['timescale_factor'] = spinnaker.timescale_factor
        cellparams['spikes_per_second'] = spinnaker.spikes_per_second
        cellparams['ring_buffer_sigma'] = spinnaker.ring_buffer_sigma
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

        self._spinnaker.add_vertex(self._vertex)

        # check if the vertex is a cmd sender, if so store for future
        require_multi_cast_source_constraints = \
            pacman_utility_calls.locate_constraints_of_type(
                self._vertex.constraints,
                VertexRequiresMultiCastSourceConstraint)

        for require_multi_cast_source_constraint \
                in require_multi_cast_source_constraints:
            if multi_cast_vertex is None:
                multi_cast_vertex = CommandSender(
                    self._spinnaker.machine_time_step,
                    self._spinnaker.timescale_factor)
                self._spinnaker.add_vertex(multi_cast_vertex)
            multi_cast_vertex = self._spinnaker.get_multi_cast_source
            edge = PartitionableEdge(multi_cast_vertex, self._vertex)
            multi_cast_vertex.add_commands(
                require_multi_cast_source_constraint.commands, edge)
            self._spinnaker.add_edge(edge)

        self._parameters = PyNNParametersSurrogate(self._vertex)

        # add any dependent edges and verts if needed
        dependant_vertex_constraints = \
            pacman_utility_calls.locate_constraints_of_type(
                self._vertex.constraints, VertexHasDependentConstraint)

        for dependant_vertex_constrant in dependant_vertex_constraints:
            dependant_vertex = dependant_vertex_constrant.vertex
            self._spinnaker.add_vertex(dependant_vertex)
            dependant_edge = PartitionableEdge(pre_vertex=self._vertex,
                                               post_vertex=dependant_vertex)
            self._spinnaker.add_edge(dependant_edge)

        # initialize common stuff
        self._size = size
        self._record_spike_file = None
        self._record_v_file = None
        self._record_g_syn_file = None

        self._spikes = None
        self._v = None
        self._gsyn = None

    def __add__(self, other):
        """
        merges populations
        """
        raise NotImplementedError

    def _add_recorder(self, variable):
        """Create a new Recorder for the supplied variable."""
        raise NotImplementedError

    def all(self):
        """
        Iterator over cell ids on all nodes.
        """
        raise NotImplementedError

    @property
    def conductance_based(self):
        """
        returns a boolean based on if the population is a conductance based pop
        """
        raise NotImplementedError

    def describe(self, template='population_default.txt', engine='default'):
        """
        Returns a human-readable description of the population.

        The output may be customized by specifying a different template
        togther with an associated template engine (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        raise NotImplementedError

    @property
    def grandparent(self):
        raise NotImplementedError

    def get(self, paramter_name, gather=False):
        """
        Get the values of a parameter for every local cell in the population.
        """
        raise NotImplementedError

    def _get_cell_position(self, cell_id):
        """
        returns the position of a cell.
        """
        if self._structure is None:
            raise ValueError("Attempted to get the position of a cell "
                             "in an un-structured population")
        elif self._positions is None:
            self._structure.generate_positions(self._vertex.n_atoms)
        return self._positions[cell_id]

    def _get_cell_initial_value(self, cell_id, variable):
        """
        set a given cells intial value
        """
        raise NotImplementedError

    # noinspection PyPep8Naming
    def getSpikes(self, compatible_output=False, gather=True):
        """
        Return a 2-column numpy array containing cell ids and spike times for
        recorded cells.   This is read directly from the memory for the board.
        """
        if self._spikes is None:

            if not gather:
                logger.warn("Spynnaker only supports gather = true, will "
                            " execute as if gather was true anyhow")
            timer = None

            if not self._vertex.record:
                raise exceptions.ConfigurationException(
                    "This population has not been set to record spikes. "
                    "Therefore spikes cannot be retrieved. Please set this "
                    "vertex to record spikes before running this command.")

            if not self._spinnaker.has_ran:
                raise exceptions.SpynnakerException(
                    "The simulation has not yet ran, therefore spikes cannot "
                    "be retrieved. Please execute the simulation before "
                    "running this command")

            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer = Timer()
                timer.start_timing()
            self._spikes = self._vertex.get_spikes(
                txrx=self._spinnaker.transceiver,
                placements=self._spinnaker.placements,
                graph_mapper=self._spinnaker.graph_mapper,
                compatible_output=compatible_output)
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer.take_sample()
        return self._spikes

    def get_spike_counts(self, gather=True):
        """
        Returns the number of spikes for each neuron.
        """
        raise NotImplementedError

    # noinspection PyUnusedLocal
    def get_gsyn(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids and synaptic
        conductances for recorded cells.

        """
        if self._gsyn is None:
            timer = None
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer = Timer()
                timer.start_timing()
            self._gsyn = self._vertex.get_gsyn(
                has_ran=self._spinnaker.has_ran,
                txrx=self._spinnaker.transceiver,
                placements=self._spinnaker.placements,
                machine_time_step=self._spinnaker.machine_time_step,
                graph_mapper=self._spinnaker.graph_mapper,
                compatible_output=compatible_output)
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer.take_sample()
        return self._gsyn

    # noinspection PyUnusedLocal
    def get_v(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and Vm for
        recorded cells.

        :param bool gather:
            not used - inserted to match PyNN specs
        :param bool compatible_output:
            not used - inserted to match PyNN specs
        """
        if self._v is None:
            timer = None
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer = Timer()
                timer.start_timing()
            self._v = self._vertex.get_v(
                has_ran=self._spinnaker.has_ran,
                txrx=self._spinnaker.transceiver,
                placements=self._spinnaker.placements,
                machine_time_step=self._spinnaker.machine_time_step,
                graph_mapper=self._spinnaker.graph_mapper,
                compatible_output=compatible_output)

            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer.take_sample()

        return self._v

    def id_to_index(self, cell_id):
        """
        Given the ID(s) of cell(s) in the Population, return its (their) index
        (order in the Population).
        """
        raise NotImplementedError

    def id_to_local_index(self, cell_id):
        """
        Given the ID(s) of cell(s) in the Population, return its (their) index
        (order in the Population), counting only cells on the local MPI node.
        """
        raise NotImplementedError

    def initialize(self, variable, value):
        """
        Set the initial value of one of the state variables of the neurons in
        this population.

        """
        initialize_attr = \
            getattr(self._vertex, "initialize_%s" % variable, None)
        if initialize_attr is None or not callable(initialize_attr):
            raise Exception("AbstractConstrainedVertex does not support "
                            "initialization of parameter {%s}".format(
                                variable))

        initialize_attr(value)

    def is_local(self, cell_id):
        """
        Determine whether the cell with the given ID exists on the local
        MPI node.
        """
        raise NotImplementedError

    def can_record(self, variable):
        """ Determine whether `variable` can be recorded from this population.
        """
        raise NotImplementedError

    def inject(self, current_source):
        """
        Connect a current source to all cells in the Population.
        """
        raise NotImplementedError

    def __iter__(self):
        """
        suppose to iterate over local cells
        """
        raise NotImplementedError

    def __len__(self):
        """
        Returns the total number of cells in the population.
        """
        return self._size

    @property
    def local_size(self):
        """
        returns the number of local cells ???
        """
        raise NotImplementedError

    def mean_spike_count(self, gather=True):
        """
        Returns the mean number of spikes per neuron.
        """
        raise NotImplementedError

    def nearest(self, position):
        """
        return the neuron closest to the specified position.
        Added functionality 23 November 2014 ADR
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
        """
        returns a position generator. Added functionality 27 November 2014 ADR
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

    def record(self, to_file=None):
        """
        Record spikes from all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering spike time recording.
        """

        if not isinstance(self._vertex, AbstractRecordableVertex):
            raise Exception("This population does not support recording!")

        # Tell the vertex to record spikes
        self._vertex.set_record(True)

        # set the file to store the spikes in once retrieved
        self._record_spike_file = to_file

    def record_gsyn(self, to_file=None):
        """
        Record the synaptic conductance for all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering gsyn value recording.
        """
        if not isinstance(self._vertex, AbstractRecordableVertex):
            raise Exception("AbstractConstrainedVertex does not support "
                            "recording of gsyn")

        self._vertex.set_record_gsyn(True)
        self._record_g_syn_file = to_file

    def record_v(self, to_file=None):
        """
        Record the membrane potential for all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering potential recording.
        """
        if not isinstance(self._vertex, AbstractRecordableVertex):
            raise Exception("AbstractConstrainedVertex does not support "
                            "recording of potential")

        self._vertex.set_record_v(True)
        self._record_v_file = to_file

    @property
    def positions(self):
        """
        Returns the position array for structured populations.
        Added functionality 27 November 2014 ADR
        """
        if self._structure is None:
            raise ValueError("attempted to retrieve positions "
                             "for an un-structured population")
        elif self._positions is None:
            self._positions = self._structure.generate_positions(
                self._vertex.n_atoms)
        return self._positions

    # noinspection PyPep8Naming
    def printSpikes(self, filename, gather=True):
        """
        Write spike time information from the population to a given file.
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
            spike_file.write("# first_id = %d\n" % first_id)
            spike_file.write("# n = %d\n" % num_neurons)
            spike_file.write("# dimensions = [%d]\n" % dimensions)
            spike_file.write("# last_id = %d\n" % last_id)
            for (neuronId, time) in spikes:
                spike_file.write("%d\t%d\n" % (time, neuronId))
            spike_file.close()

    def print_gsyn(self, filename, gather=True):
        """
        Write conductance information from the population to a given file.

        """
        time_step = (self._spinnaker.machine_time_step * 1.0) / 1000.0
        gsyn = self.get_gsyn(gather, compatible_output=True)
        first_id = 0
        num_neurons = self._vertex.n_atoms
        dimensions = self._vertex.n_atoms
        utility_calls.check_directory_exists_and_create_if_not(filename)
        file_handle = open(filename, "w")
        file_handle.write("# first_id = %d\n" % first_id)
        file_handle.write("# n = %d\n" % num_neurons)
        file_handle.write("# dt = %f\n" % time_step)
        file_handle.write("# dimensions = [%d]\n" % dimensions)
        file_handle.write("# last_id = {%d}\n".format(num_neurons - 1))
        file_handle = open(filename, "w")
        for (neuronId, time, value) in gsyn:
            file_handle.write("%f\t%d\t%f\n" % (time, neuronId, value))
        file_handle.close()

    def print_v(self, filename, gather=True):
        """
        Write membrane potential information from the population to a given
        file.
        """
        time_step = (self._spinnaker.machine_time_step * 1.0) / 1000.0
        v = self.get_v(gather, compatible_output=True)
        utility_calls.check_directory_exists_and_create_if_not(filename)
        file_handle = open(filename, "w")
        first_id = 0
        num_neurons = self._vertex.n_atoms
        dimensions = self._vertex.n_atoms
        file_handle.write("# first_id = %d\n" % first_id)
        file_handle.write("# n = %d\n" % num_neurons)
        file_handle.write("# dt = %f\n" % time_step)
        file_handle.write("# dimensions = [%d]\n" % dimensions)
        file_handle.write("# last_id = %d\n" % (num_neurons - 1))
        for (neuronId, _, value) in v:
            file_handle.write("%f\t%d\n" % (value, neuronId))
        file_handle.close()

    def rset(self, parametername, rand_distr):
        """
        'Random' set. Set the value of parametername to a value taken from
        rand_distr, which should be a RandomDistribution object.
        """
        raise NotImplementedError

    def sample(self, n, rng=None):
        """
        returns a random selection fo neurons from a population in the form
        of a population view
        """
        raise NotImplementedError

    def save_positions(self, file_name):
        """
        save positions to file. Added functionality 23 November 2014 ADR
        """
        if self._structure is None:
            raise ValueError("attempted to retrieve positions "
                             "for an un-structured population")
        elif self._positions is None:
            self._structure.generate_positions(self._vertex.n_atoms)
        file_handle = open(file_name, "w")
        file_handle.write(self._positions)
        file_handle.close()

    def _set_cell_initial_value(self, cell_id, variable, value):
        """
        set a given cells intial value
        """
        raise NotImplementedError

    def _set_cell_position(self, cell_id, pos):
        """
        sets a cell to a given position
        """
        if self._structure is None:
            raise ValueError("attempted to set a position for a cell "
                             "in an un-structured population")
        elif self._positions is None:
            self._structure.generate_positions(self._vertex.n_atoms)
        self._positions[cell_id] = pos

    def _set_positions(self, positions):
        """
        sets all the positions in the population.
        """
        if self._structure is None:
            raise ValueError("attempted to set positions "
                             "in an un-structured population")
        else:
            self._positions = positions

    def set(self, parameter, value=None):
        """
        Set one or more parameters for every cell in the population.

        param can be a dict, in which case val should not be supplied, or a
        string giving the parameter name, in which case val is the parameter
        value. val can be a numeric value, or list of such
        (e.g. for setting spike times)::

          p.set("tau_m", 20.0).
          p.set({'tau_m':20, 'v_rest':-65})
        """
        if type(parameter) is str:
            if value is None:
                raise Exception("Error: No value given in set() function for "
                                "population parameter. Exiting.")
            self._parameters[parameter] = value
            return
        if type(parameter) is not dict:
                raise Exception("Error: invalid parameter type for "
                                "set() function for population parameter."
                                " Exiting.")
        # Add a dictionary-structured set of new parameters to the current set:
        self._parameters.update(parameter)

    @property
    def structure(self):
        """
        Returns the structure for the population. Added 23 November 2014 ADR
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

    # NONE PYNN API CALL
    def set_mapping_constraint(self, constraint_dict):
        """ Add a placement constraint - for backwards compatibility

        :param constraint_dict: A dictionary containing "x", "y" and\
                    optionally "p" as keys, and ints as values
        :type constraint_dict: dict of str->int
        """
        self.add_placement_constraint(**constraint_dict)

    # NONE PYNN API CALL
    def set_model_based_max_atoms_per_core(self, new_value):
        if hasattr(self._vertex, "set_model_max_atoms_per_core"):
            self._vertex.set_model_max_atoms_per_core(new_value)
        else:
            raise exceptions.ConfigurationException(
                "This population does not support its max_atoms_per_core "
                "variable being adjusted by the end user. Sorry")

    @property
    def size(self):
        return self._vertex.n_atoms

    def tset(self, parametername, value_array):
        """
        'Topographic' set. Set the value of parametername to the values in
        value_array, which must have the same dimensions as the Population.
        """
        raise NotImplementedError

    @property
    def _get_vertex(self):
        return self._vertex

    @property
    def _internal_delay_vertex(self):
        return self._delay_vertex

    @_internal_delay_vertex.setter
    def _internal_delay_vertex(self, delay_vertex):
        self._delay_vertex = delay_vertex
