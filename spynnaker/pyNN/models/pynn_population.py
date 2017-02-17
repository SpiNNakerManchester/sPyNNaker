from pacman.model.constraints.abstract_constraint\
    import AbstractConstraint
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from spynnaker.pyNN.models.pynn_population_common import PyNNPopulationCommon
from spynnaker.pyNN.models.recording_common import RecordingCommon

from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.abstract_models.abstract_population_settable \
    import AbstractPopulationSettable
from spynnaker.pyNN.models.abstract_models.abstract_population_initializable\
    import AbstractPopulationInitializable
from spynnaker.pyNN.models.neuron.input_types.input_type_conductance \
    import InputTypeConductance

from spinn_front_end_common.utilities import exceptions

import numpy
import logging

logger = logging.getLogger(__name__)


class Population(PyNNPopulationCommon, RecordingCommon):
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

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 structure=None):

        PyNNPopulationCommon.__init__(
            self, spinnaker_control=spinnaker, size=size,
            cellparams=cellparams, cellclass=cellclass, label=label)
        RecordingCommon.__init__(self, self, spinnaker)

        # Internal structure now supported 23 November 2014 ADR
        # structure should be a valid Space.py structure type.
        # generation of positions is deferred until needed.
        if structure:
            self._structure = structure
            self._positions = None
        else:
            self._structure = None

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

        self._compatible_output_and_gather_warnings(compatible_output, gather)
        return self._get_recorded_variable("spikes")

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
        Return a 3-column numpy array containing cell ids, time and synaptic
        conductances for recorded cells.
        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        """

        self._compatible_output_and_gather_warnings(compatible_output, gather)
        excit = self._get_recorded_variable("gsyn_exc")
        inhib = self._get_recorded_variable("gsyn_inh")
        # TODO join them together and then return the joined up thingy
        return None

    # noinspection PyUnusedLocal
    def get_v(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and V_m for
        recorded cells.

        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        """
        self._compatible_output_and_gather_warnings(compatible_output, gather)
        return self._get_recorded_variable("v")

    @staticmethod
    def _compatible_output_and_gather_warnings(compatible_output, gather):
        """ checks the values for compatible out and gather warnings

        :param compatible_output: if compatible with pynn
        :param gather: if gathering from pynn
        :return: None
        """
        if not gather:
            logger.warn(
                "Spynnaker 0.7 only supports gather = true, will  execute "
                "as if gather was true anyhow")

        if compatible_output:
            logger.warn(
                "Spynnaker 0.7 only supports compatible_output = false, will"
                " execute as if compatible_output was false anyhow")

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
        self._vertex.initialize(variable, utility_calls.convert_param_to_numpy(
            value, self._vertex.n_atoms))
        self._change_requires_mapping = True

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

        :param `pyNN.random.RandomDistribution` distribution:
            the distribution used to draw random values.

        """
        self.initialize('v', distribution)
        self._change_requires_mapping = True

    def record(self, to_file=None):
        """ Record spikes from all cells in the Population.

        :param to_file: file to write the spike data to
        """

        RecordingCommon._record(
            self, 'spikes', self._create_full_filter_list(1), 1)

        # state that something has changed in the population,
        self._change_requires_mapping = True

    def record_gsyn(self, to_file=None):
        """ Record the synaptic conductance for all cells in the Population.

        :param to_file: the file to write the recorded gsyn to.
        """

        # have to set each to record and set the file at that point, otherwise
        # itll not work due to pynn bug
        self._vertex.record(
            self, 'gsyn_exc', self._create_full_filter_list(1), 1)
        self.file = to_file
        self._vertex.set_recording_gsyn_inh(
            self, 'gsyn_inh', self._create_full_filter_list(1), 1)
        self.file = to_file

        # state that something has changed in the population,
        self._change_requires_mapping = True

    def record_v(self, to_file=None):
        """ Record the membrane potential for all cells in the Population.

        :param to_file: the file to write the recorded v to.
        """

        self._vertex.record(
            self, 'v', self._create_full_filter_list(1), 1)
        self.file = to_file

        # state that something has changed in the population,
        self._change_requires_mapping = True

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
        return self._positions

    @positions.setter
    def positions(self, positions):
        """ Sets all the positions in the population.
        """
        self._positions = positions

        # state that something has changed in the population,
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
        spikes = self._get_recorded_variable('spikes')
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
        time_step = (self._spinnaker_control.machine_time_step * 1.0) / 1000.0
        gsyn_exc = self._get_recorded_variable('gsyn_exc')
        gsyn_inh = self._get_recorded_variable('gsyn_inh')

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
        for (neuronId, time, value_e, _, _, value_i) in zip(
                gsyn_exc, gsyn_inh):
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
        time_step = (self._spinnaker_control.machine_time_step * 1.0) / 1000.0
        v = self._get_recorded_variable("v")
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
        :return:
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
