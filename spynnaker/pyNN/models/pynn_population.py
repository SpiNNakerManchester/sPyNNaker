from pacman.model.constraints import AbstractConstraint
from pacman.model.constraints.placer_constraints\
    import PlacerChipAndCoreConstraint

from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.abstract_models.abstract_read_parameters_before_set\
    import AbstractReadParametersBeforeSet
from spynnaker.pyNN.models.abstract_models.abstract_population_settable \
    import AbstractPopulationSettable
from spynnaker.pyNN.models.abstract_models.abstract_population_initializable\
    import AbstractPopulationInitializable
from spynnaker.pyNN.models.neuron.input_types.input_type_conductance \
    import InputTypeConductance
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.models.common.abstract_gsyn_recordable \
    import AbstractGSynRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable \
    import AbstractVRecordable

from spinn_front_end_common.utilities import exceptions
from spinn_front_end_common.abstract_models.abstract_changable_after_run \
    import AbstractChangableAfterRun

import numpy
import logging

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
    """

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 structure=None):
        if size is not None and size <= 0:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative or zero size.")

        # Create a graph vertex for the population and add it
        # to PACMAN
        cell_label = label
        if label is None:
            cell_label = "Population {}".format(
                spinnaker.none_labelled_vertex_count)
            spinnaker.increment_none_labelled_vertex_count()

        # copy the parameters so that the end users are not exposed to the
        # additions placed by spinnaker.
        internal_cellparams = dict(cellparams)

        # set spinnaker targeted parameters
        internal_cellparams['label'] = cell_label
        internal_cellparams['n_neurons'] = size

        # create population vertex.
        self._vertex = cellclass(**internal_cellparams)
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
        self._spinnaker.add_application_vertex(self._vertex)

        # initialise common stuff
        self._size = size
        self._record_spike_file = None
        self._record_v_file = None
        self._record_gsyn_file = None

        # parameter
        self._change_requires_mapping = True
        self._has_read_neuron_parameters_this_run = False

    @property
    def requires_mapping(self):
        return self._change_requires_mapping

    def mark_no_changes(self):
        self._change_requires_mapping = False
        self._has_read_neuron_parameters_this_run = False

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
        """
        return self._vertex.default_parameters

    def describe(self, template='population_default.txt', engine='default'):
        """ Returns a human-readable description of the population.

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
                    "This population has not been set to record spikes")
        else:
            raise exceptions.ConfigurationException(
                "This population has not got the capability to record spikes")

        if not self._spinnaker.has_ran:
            logger.warn(
                "The simulation has not yet run, therefore spikes cannot"
                " be retrieved, hence the list will be empty")
            return numpy.zeros((0, 2))

        if self._spinnaker.use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 2))

        spikes = self._vertex.get_spikes(
            self._spinnaker.placements, self._spinnaker.graph_mapper,
            self._spinnaker.buffer_manager, self._spinnaker.machine_time_step)

        return spikes

    def get_spike_counts(self, gather=True):
        """ Return the number of spikes for each neuron.
        """
        spikes = self.getSpikes(True, gather)
        n_spikes = {}
        counts = numpy.bincount(spikes[:, 0].astype(dtype=numpy.int32),
                                minlength=self._vertex.n_atoms)
        for i in range(self._vertex.n_atoms):
            n_spikes[i] = counts[i]
        return n_spikes

    # noinspection PyUnusedLocal
    def get_gsyn(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time and synaptic\
        conductances for recorded cells.

        :param gather: not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output: not used - inserted to match PyNN specs
        :type compatible_output: bool
        """

        if isinstance(self._vertex, AbstractGSynRecordable):
            if not self._vertex.is_recording_gsyn():
                raise exceptions.ConfigurationException(
                    "This population has not been set to record gsyn")
        else:
            raise exceptions.ConfigurationException(
                "This population has not got the capability to record gsyn")

        if not self._spinnaker.has_ran:
            logger.warn(
                "The simulation has not yet run, therefore gsyn cannot"
                " be retrieved, hence the list will be empty")
            return numpy.zeros((0, 4))

        if self._spinnaker.use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 4))

        return self._vertex.get_gsyn(
            self._spinnaker.no_machine_time_steps, self._spinnaker.placements,
            self._spinnaker.graph_mapper, self._spinnaker.buffer_manager,
            self._spinnaker.machine_time_step)

    # noinspection PyUnusedLocal
    def get_v(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and V_m for\
        recorded cells.

        :param gather: not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output: not used - inserted to match PyNN specs
        :type compatible_output: bool
        """
        if isinstance(self._vertex, AbstractVRecordable):
            if not self._vertex.is_recording_v():
                raise exceptions.ConfigurationException(
                    "This population has not been set to record v")
        else:
            raise exceptions.ConfigurationException(
                "This population has not got the capability to record v")

        if not self._spinnaker.has_ran:
            logger.warn(
                "The simulation has not yet run, therefore v cannot"
                " be retrieved, hence the list will be empty")
            return numpy.zeros((0, 3))

        if self._spinnaker.use_virtual_board:
            logger.warn(
                "The simulation is using a virtual machine and so has not"
                " truly ran, hence the list will be empty")
            return numpy.zeros((0, 3))

        return self._vertex.get_v(
            self._spinnaker.no_machine_time_steps, self._spinnaker.placements,
            self._spinnaker.graph_mapper, self._spinnaker.buffer_manager,
            self._spinnaker.machine_time_step)

    def id_to_index(self, cell_id):
        """ Given the ID(s) of cell(s) in the Population, return its (their)\
            index (order in the Population).
        """

        # TODO: Need __getitem__
        raise NotImplementedError

    def id_to_local_index(self, cell_id):
        """ Given the ID(s) of cell(s) in the Population, return its (their)\
            index (order in the Population), counting only cells on the local\
            MPI node.
        """
        # TODO: Need __getitem__
        raise NotImplementedError

    def initialize(self, variable, value):
        """ Set the initial value of one of the state variables of the neurons\
            in this population.

        """
        if not isinstance(self._vertex, AbstractPopulationInitializable):
            raise KeyError(
                "Population does not support the initialisation of {}".format(
                    variable))
        if self._spinnaker.has_ran and not isinstance(
                self._vertex, AbstractChangableAfterRun):
            raise Exception("Population does not support changes after run")
        self._vertex.initialize(variable, utility_calls.convert_param_to_numpy(
            value, self._vertex.n_atoms))

    @staticmethod
    def is_local(cell_id):
        """ Determine whether the cell with the given ID exists on the local \
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
        """ Connect a current source to all cells in the Population.
        """

        # TODO:
        raise NotImplementedError

    def __iter__(self):
        """ Iterate over local cells
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
        return self._vertex.label

    @property
    def local_size(self):
        """ The number of local cells
        """

        # Doesn't make much sense on SpiNNaker
        return self._size

    # noinspection PyPep8Naming
    def meanSpikeCount(self, gather=True):
        """ The mean number of spikes per neuron

        :param gather: gather has no meaning in spinnaker, always set to true
        :return: an array which contains the average spike rate per neuron
        """
        return self.mean_spike_count(gather)

    def mean_spike_count(self, gather=True):
        """ The mean number of spikes per neuron
        """
        spike_counts = self.get_spike_counts(gather)
        total_spikes = sum(spike_counts.values())
        return total_spikes / self._size

    def nearest(self, position):
        """ Return the neuron closest to the specified position
        """
        # doesn't always work correctly if a position is equidistant between
        # two neurons, i.e. 0.5 should be rounded up, but it isn't always.
        # also doesn't take account of periodic boundary conditions

        # TODO: Enable when __getitem__ is enabled
        # pos = numpy.array([position] * self.positions.shape[1]).transpose()
        # dist_arr = (self.positions - pos) ** 2
        # distances = dist_arr.sum(axis=0)
        # nearest = distances.argmin()
        # return self[nearest]

        raise NotImplementedError

    # noinspection PyPep8Naming
    def randomInit(self, distribution):
        """ Set initial membrane potentials for all the cells in the\
            population to random values.

        :param `pyNN.random.RandomDistribution` distribution:\
            the distribution used to draw random values.

        """
        self.initialize('v', distribution)

    def record(self, to_file=None):
        """ Record spikes from all cells in the Population.

        :param to_file: file to write the spike data to
        """

        if not isinstance(self._vertex, AbstractSpikeRecordable):
            raise Exception(
                "This population does not support the recording of spikes")

        # Tell the vertex to record spikes
        if not self._vertex.is_recording_spikes():
            if self._spinnaker.has_ran and not isinstance(
                    self._vertex, AbstractChangableAfterRun):
                raise Exception(
                    "This population does not support changes to settings"
                    " after run has been called")
            self._vertex.set_recording_spikes()

        # set the file to store the spikes in once retrieved
        self._record_spike_file = to_file

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

        if not self._vertex.is_recording_gsyn():
            if self._spinnaker.has_ran and not isinstance(
                    self._vertex, AbstractChangableAfterRun):
                raise Exception(
                    "This population does not support changes to settings"
                    " after run has been called")
            self._vertex.set_recording_gsyn()

        self._record_gsyn_file = to_file

    def record_v(self, to_file=None):
        """ Record the membrane potential for all cells in the Population.

        :param to_file: the file to write the recorded v to.
        """
        if not isinstance(self._vertex, AbstractVRecordable):
            raise Exception(
                "This population does not support the recording of v")

        if not self._vertex.is_recording_v():
            if self._spinnaker.has_ran and not isinstance(
                    self._vertex, AbstractChangableAfterRun):
                raise Exception(
                    "This population does not support changes to settings"
                    " after run has been called")
            self._vertex.set_recording_v()

        self._record_v_file = to_file

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
            self._change_requires_mapping = True
        return self._positions

    @positions.setter
    def positions(self, positions):
        """ Sets all the positions in the population.
        """
        self._positions = positions
        self._change_requires_mapping = True

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
        """ 'Random' set. Set the value of parametername to a value taken\
             from rand_distr, which should be a RandomDistribution object.

        :param parametername: the parameter to set
        :param rand_distr: the random distribution object to set the parameter\
                     to
        """
        self.set(parametername, rand_distr)

    def sample(self, n, rng=None):
        """ Return a random selection of neurons from a population in the form\
            of a population view

        :param n: the number of neurons to sample
        :param rng: the random number generator to use.
        """

        # TODO: Need PopulationView support
        raise NotImplementedError

    def save_positions(self, file):  # @ReservedAssignment
        """ Save positions to file.

            :param file: the file to write the positions to.
        """
        file_handle = open(file, "w")
        file_handle.write(self.positions)
        file_handle.close()

    def set(self, parameter, value=None):
        """ Set one or more parameters for every cell in the population.

        param can be a dict, in which case value should not be supplied, or a
        string giving the parameter name, in which case value is the parameter
        value. value can be a numeric value, or list of such
        (e.g. for setting spike times)::

          p.set("tau_m", 20.0).
          p.set({'tau_m':20, 'v_rest':-65})

        :param parameter: the parameter to set
        :param value: the value of the parameter to set.
        """
        if not isinstance(self._vertex, AbstractPopulationSettable):
            raise KeyError("Population does not have property {}".format(
                parameter))

        if self._spinnaker.has_ran and not isinstance(
                self._vertex, AbstractChangableAfterRun):
            raise Exception(
                "This population does not support changes to settings after"
                " run has been called")

        if type(parameter) is str:
            if value is None:
                raise Exception("A value (not None) must be specified")
            self._read_parameters_before_set()
            self._vertex.set_value(parameter, value)
            return

        if type(parameter) is not dict:
            raise Exception(
                "Parameter must either be the name of a single parameter to"
                " set, or a dict of parameter: value items to set")

        # set new parameters
        self._read_parameters_before_set()
        for (key, value) in parameter.iteritems():
            self._vertex.set_value(key, value)

    def _read_parameters_before_set(self):
        """ Reads parameters from the machine before "set" completes

        :return: None
        """

        # If the tools have run before, and not reset, and the read
        # hasn't already been done, read back the data
        if (self._spinnaker.has_ran and not self._spinnaker.has_reset_last and
                isinstance(self._vertex, AbstractReadParametersBeforeSet) and
                not self._has_read_neuron_parameters_this_run):

            # locate machine vertices from the application vertices
            machine_vertices = \
                self._spinnaker.graph_mapper.get_machine_vertices(
                    self._vertex)

            # go through each machine vertex and read the neuron parameters
            # it contains
            for machine_vertex in machine_vertices:

                # tell the core to rewrite neuron params back to the
                # sdram space.
                placement = self._spinnaker.placements.\
                    get_placement_of_vertex(machine_vertex)

                self._vertex.read_parameters_from_machine(
                    self._spinnaker.transceiver, placement,
                    self._spinnaker.graph_mapper.get_slice(machine_vertex))

            self._has_read_neuron_parameters_this_run = True

    @property
    def structure(self):
        """ Return the structure for the population.
        """
        return self._structure

    # NONE PYNN API CALL
    def set_constraint(self, constraint):
        """ Apply a constraint to a population that restricts the processor\
            onto which its atoms will be placed.
        """
        if isinstance(constraint, AbstractConstraint):
            self._vertex.add_constraint(constraint)
        else:
            raise exceptions.ConfigurationException(
                "the constraint entered is not a recognised constraint")

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
                "variable being adjusted by the end user")

        # state that something has changed in the population,
        self._change_requires_mapping = True

    @property
    def size(self):
        """ The number of neurons in the population
        """
        return self._vertex.n_atoms

    def tset(self, parametername, value_array):
        """ 'Topographic' set. Set the value of parametername to the values in\
            value_array, which must have the same dimensions as the Population.

        :param parametername: the name of the parameter
        :param value_array: the array of values which must have the correct\
                number of elements.
        """
        if len(value_array) != self._vertex.n_atoms:
            raise exceptions.ConfigurationException(
                "To use tset, you must have a array of values which matches "
                "the size of the population. Please change this and try "
                "again, or alternatively, use set()")
        self.set(parametername, value_array)

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
        self._change_requires_mapping = True
