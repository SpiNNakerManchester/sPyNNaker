from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex import \
    AbstractDataSpecableVertex
from spynnaker.pyNN.models.utility_models.multicastsource \
    import MultiCastSource
from spynnaker.pyNN.utilities.parameters_surrogate\
    import PyNNParametersSurrogate
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.visualiser_package.visualiser_vertex import VisualiserVertex

from visualiser import visualiser_constants

from pacman.model.graph.edge import Edge

import logging
logger = logging.getLogger(__name__)


class Population(object):
    """
    A collection neuron of the same types. It encapsulates a type of 
    :class:`pacman103.lib.graph.Vertex`
    used with Spiking Neural Networks, comprising n cells (atoms)
    of the same :py:mod:`pacman103.front.pynn.models` type.

    :param int size:
        size (number of cells) of the Population.
    :param `pacman103.front.pynn.models` cellclass:
        specifies the neural model to use for the Population
    :param dict cellparams:
        a dictionary containing model specific parameters and values
    :param `pyNN.space` structure:
        a spatial structure - not supported
    :param string label:
        a label identifying the Population
    :returns a list of vertexes and edges
    """

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 machine_time_step, runtime,
                 multi_cast_vertex=None, structure=None):
        """
        Instantiates a :py:object:`Population`.
        """
        if size <= 0:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative or zero size.")
        # Raise an exception if the Pop. attempts to employ spatial structure
        if structure:
            raise Exception("Spatial structure is unsupported for Populations.")

        # Create a graph vertex for the population and add it to PACMAN
        self._vertex = cellclass(size, label, **cellparams)
        if issubclass(type(cellclass), AbstractDataSpecableVertex):
            if self._vertex.machine_time_step is None:
                self._vertex.set_machien_time_step(machine_time_step)
            if self._vertex.application_runtime is None:
                self._vertex.set_application_runtime(runtime)

        self._spinnaker = spinnaker

        #check if the vertex is a cmd sender, if so store for future
        if self._vertex.requires_multi_cast_source():
            if multi_cast_vertex is None:
                multi_cast_vertex = MultiCastSource()
                self._spinnaker.add_vertex(multi_cast_vertex)
            edge = Edge(multi_cast_vertex, self._vertex)
            self._spinnaker.add_edge(edge)

        self._parameters = PyNNParametersSurrogate(self._vertex)
        self._spinnaker.add_vertex(self._vertex)

        #add any dependant edges and verts if needed
        dependant_verts, dependant_edges = \
            self._vertex.get_dependant_vertexes_edges()

        if dependant_verts is not None:
            for dependant_vert in dependant_verts:
                self._spinnaker.add_vertex(dependant_vert)

        if dependant_edges is not None:
            for dependant_edge in dependant_edges:
                self._spinnaker.add_edge(dependant_edge)

        #initlise common stuff
        self._size = size
        self._record_spike_file = None
        self._record_v_file = None
        self._record_g_syn_file = None

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
        returns the position of a cell (no idea what a cell is)
        """
        raise NotImplementedError

    def _get_cell_initial_value(self, cell_id, variable):
        """
        set a given cells intial value
        """
        raise NotImplementedError

    #noinspection PyPep8Naming
    def getSpikes(self, compatible_output=False, gather=True):
        """
        Return a 2-column numpy array containing cell ids and spike times for
        recorded cells.   This is read directly from the memory for the board.
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute as"
                        "if gather was true anyhow")
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
        spikes = self._vertex.get_spikes(self._spinnaker, compatible_output)
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()
        return spikes

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
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
        gsyn = self._vertex.get_gsyn(self._spinnaker,
                                     compatible_output=compatible_output)
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()
        return gsyn

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
        timer = None
        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer = Timer()
            timer.start_timing()
        v = self._vertex.get_v(self._spinnaker,
                               compatible_output=compatible_output)

        if conf.config.getboolean("Reports", "outputTimesForSections"):
            timer.take_sample()

        return v

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
            raise Exception("Vertex does not support initialization of "
                            "parameter {%s}".format(variable))

        initialize_attr(value)

    def is_local(self, cell_id):
        """
        Determine whether the cell with the given ID exists on the local
        MPI node.
        """
        raise NotImplementedError

    def can_record(self, variable):
        """Determine whether `variable` can be recorded from this population."""
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
        return the neuron closest to the specificed position
        """
        raise NotImplementedError

    @property
    def position_generator(self):
        """
        returns a position generator
        """
        raise NotImplementedError

    def random_init(self, distribution):
        """
        Set initial membrane potentials for all the cells in the population to
        random values.

        :param `pyNN.random.RandomDistribution` distribution:
            the distribution used to draw random values.

        """
        new_entry_for_vinit = {'v_init': distribution}
        self._parameters.update(new_entry_for_vinit)

    def record(self, to_file=None, focus=None,
               visualiser_mode=visualiser_constants.RASTER,
               visualiser_2d_dimension=None, visualiser_raster_seperate=None,
               visualiser_no_colours=None, visualiser_average_period_tics=None,
               visualiser_longer_period_tics=None,
               visualiser_update_screen_in_tics=None,
               visualiser_reset_counters=None,
               visualiser_reset_counter_period=None):
        """
        Record spikes from all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering spike time recording.
        """
        record_attr = getattr(self._vertex, "record", None)
        if record_attr is None or not callable(record_attr):
            raise Exception("Vertex does not support recording of spikes")

        # Tell the vertex to record spikes
        self._vertex.record(focus=focus)
        if conf.config.getboolean("Visualiser", "enable"):
            visualiser_vertex = VisualiserVertex(
                visualiser_mode, visualiser_2d_dimension,
                visualiser_raster_seperate, visualiser_no_colours,
                visualiser_average_period_tics, visualiser_longer_period_tics,
                visualiser_update_screen_in_tics, visualiser_reset_counters,
                visualiser_reset_counter_period, self._vertex)
            self._spinnaker.add_visualiser_vertex(visualiser_vertex)
        self._record_spike_file = to_file

        # add an edge to the monitor
        self._spinnaker.add_edge_to_recorder_vertex(self._vertex)

    def record_gsyn(self, to_file=None):
        """
        Record the synaptic conductance for all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering gsyn value recording.
        """
        if (not hasattr(self._vertex, "record_gsyn")
                or not callable(self._vertex.record_gsyn)):
            raise Exception("Vertex does not support recording of gsyn")

        self._vertex.record_gsyn()
        self._record_g_syn_file = to_file

    def record_v(self, to_file=None):
        """
        Record the membrane potential for all cells in the Population.
        A flag is set for this population that is passed to the simulation,
        triggering potential recording.
        """
        if (not hasattr(self._vertex, "record_v")
                or not callable(self._vertex.record_v)):
            raise Exception("Vertex does not support recording of potential")

        self._vertex.record_v()
        self._record_v_file = to_file

    @property
    def positions(self):
        raise NotImplementedError

    #noinspection PyPep8Naming
    def printSpikes(self, filename, gather=True):
        """
        Write spike time information from the population to a given file.
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute as"
                        "if gather was true anyhow")
        spikes = self.getSpikes(compatible_output=True)
        if spikes is not None:
            first_id = 0
            num_neurons = self._vertex.atoms
            dimensions = self._vertex.atoms
            last_id = self._vertex.atoms - 1
            utility_calls.check_directory_exists(filename)
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
        time_step = (self._spinnaker.dao.machineTimeStep * 1.0) / 1000.0
        gsyn = self.get_gsyn(gather, compatible_output=True)
        first_id = 0
        num_neurons = self._vertex.atoms
        dimensions = self._vertex.atoms
        file_handle = open(filename, "w")
        file_handle.write("# first_id = %d\n" % first_id)
        file_handle.write("# n = %d\n" % num_neurons)
        file_handle.write("# dt = %f\n" % time_step)
        file_handle.write("# dimensions = [%d]\n" % dimensions)
        file_handle.write("# last_id = {%d}\n".format(num_neurons - 1))
        utility_calls.check_directory_exists(filename)
        file_handle = open(filename, "w")
        for (neuronId, time, value) in gsyn:
            file_handle.write("%f\t%d\t%f\n" % (time, neuronId, value))
        file_handle.close()

    def print_v(self, filename, gather=True):
        """
        Write membrane potential information from the population to a given
        file.
        """
        time_step = (self._spinnaker.dao.machineTimeStep * 1.0) / 1000.0
        v = self.get_v(gather, compatible_output=True)
        utility_calls.check_directory_exists(filename)
        file_handle = open(filename, "w")
        first_id = 0
        num_neurons = self._vertex.atoms
        dimensions = self._vertex.atoms
        file_handle.write("# first_id = %d\n" % first_id)
        file_handle.write("# n = %d\n" % num_neurons)
        file_handle.write("# dt = %f\n" % time_step)
        file_handle.write("# dimensions = [%d]\n" % dimensions)
        file_handle.write("# last_id = %d\n" % (num_neurons - 1))
        for (neuronId, time, value) in v:
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
        save positions to file
        """
        raise NotImplementedError

    def set(self, *args, **kargs):
        """
        converts key value pairs in key args into a collection of string
        parameter and value entries used with old fashion set.

        Assumes parameters_surrogate will throw error when entries not
        avilable for a vertex is given
        """
        if len(args) == 0:
            for key in kargs.keys():
                self._set_string_value_pair(key, kargs[key])
        else:
            for element in range(0, len(args), 2):
                self._set_string_value_pair(args[element], args[element + 1])

    def _set_cell_initial_value(self, cell_id, variable, value):
        """
        set a given cells intial value
        """
        raise NotImplementedError

    def _set_cell_position(self, cell_id, pos):
        """
        sets a cell to a given position
        """
        raise NotImplementedError

    def _set_string_value_pair(self, parameter, value=None):
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

    #NONE PYNN API CALL
    def set_constraint(self, constraint):
        """
        Apply a constraint to a population that restricts the processor
        onto which its sub-populations will be placed.
        """
        self._vertex.add_constraint(constraint)

    #NONE PYNN API CALL
    def set_model_based_max_atoms_per_core(self, new_value):
        if hasattr(self._vertex, "set_model_max_atoms_per_core"):
            self._vertex.set_model_max_atoms_per_core(new_value)
        else:
            raise exceptions.ConfigurationException(
                "This population does not support its max_atoms_per_core "
                "variable being adjusted by the end user. Sorry")

    @property
    def structure(self):
        raise NotImplementedError

    def tset(self, parametername, value_array):
        """
        'Topographic' set. Set the value of parametername to the values in
        value_array, which must have the same dimensions as the Population.
        """
        raise NotImplementedError