# front end common imports
from spinn_front_end_common.utilities import exceptions

# spynnaker imports
from spynnaker.pyNN.models.abstract_models.abstract_population_settable import \
    AbstractPopulationSettable
from spynnaker.pyNN.models.pynn_assembly import Assembly
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models import high_level_function_utilties

# pynn imports
from pyNN import descriptions, random

# general imports
import logging
import numpy

logger = logging.getLogger(__name__)


class PopulationView(object):
    """
    Population view object. allows filtering of neurons
    """

    def __init__(
            self, parent_population_or_population_view, neuron_filter, label,
            spinnaker):
        """
        constructor for the pop view
        :param parent_population_or_population_view:
        :param neuron_filter: The filter for the neurons
        :param label:
        :param spinnaker:
        :type neuron_filter: iterable of booleans or iterable of ints,
        or a slice
        :return: a pop view object
        """
        self._spinnaker = spinnaker

        # update label accordingly
        if label is None:
            self._label = "Population_view {}".format(
                spinnaker.none_labelled_pop_view_count())
            spinnaker.increment_none_labelled_pop_view_count()

        self._parent_is_pop_view = False
        self._parent_population_or_population_view = \
            parent_population_or_population_view

        # store filter for usage
        self._neuron_filter = neuron_filter
        # turn filter from the 3 versions into an index based one
        self._neuron_filter = high_level_function_utilties.\
            translate_filter_to_ints(
                self._neuron_filter,
                self._parent_population_or_population_view.size)

        # filter down to the population, over the pop view
        self._population = self.locate_parent_population()
        self._model_name = self._population._vertex.model_name()

        # update atom mapping for spinnaker understanding
        self._update_atom_mapping()

        # update size
        self._size = len(self._get_atoms_for_pop_view())

        # storage for positions if needed.
        self._positions = None

    @property
    def label(self):
        """
        getter for the label
        :return:
        """
        return self._label

    def locate_parent_population(self):
        """
        filters down the pop views until they reach a population.
        :return: the underlying population.
        """
        if isinstance(self._parent_population_or_population_view,
                      PopulationView):
            self._parent_is_pop_view = True
            return self._parent_population_or_population_view.\
                locate_parent_population()
        else:
            return self._parent_population_or_population_view

    def _update_atom_mapping(self):
        """
        updates the spinnaker atom mapping so that its aware of this pop view
        :return:
        """
        # check model exists correctly
        atom_mappings = self._spinnaker.get_atom_mapping()
        if self._model_name not in atom_mappings:
            raise exceptions.ConfigurationException(
                "The population to view in this population view does not"
                " exist in our standard populations. Please fix and try again")

        # if valid, add neuron param objects to this list as well
        # (assumes a ref copy)
        atom_mappings[self._model_name][self] = list()
        atom_models_for_pop = atom_mappings[self._model_name][
            self._parent_population_or_population_view]

        # filter atoms from the parent
        for atom_index in range(0, len(atom_models_for_pop)):
            if atom_index in self._neuron_filter:
                atom_mappings[self._model_name][self].append(
                    atom_models_for_pop[atom_index])

    def _get_atoms_for_pop_view(self):
        """
        helper method for getting atoms from pop view
        :return:
        """
        atom_mapping = self._spinnaker.get_atom_mapping()
        model_name_atoms = atom_mapping[self._model_name]
        pop_view_atoms = \
            model_name_atoms[self._parent_population_or_population_view]
        return pop_view_atoms

    def __add__(self, other):
        """
        adds the population view and either another pop_view or population,
        to make a assembler
        :param other: other pop view or population
        :return:
        """

        # validate parameter
        if (not isinstance(other, PopulationView) and
                not isinstance(other, Population)):
            raise exceptions.ConfigurationException(
                "Can only add a population or a population view to a"
                " population view.")

        # build assembler
        return Assembly(
            populations=[self, other],
            label="assembler containing {}:{}".format(self._label, other.label),
            spinnaker=self._spinnaker)

    def __getitem__(self, index):
        """
        returns either a cell object or a population view object based off the
        filter.
        :param index: either a index or a slice.
        :return: a NeuronCell object or a Population View object
        """
        if isinstance(index, int):
            pop_view_atoms = self._get_atoms_for_pop_view()
            return pop_view_atoms[index]
        elif isinstance(index, slice):
            return PopulationView(self, index, None, self._spinnaker)

    def __iter__(self):
        """
        returns a iterator for the cells in the population view
        :return: iterator of NeuronCell
        """
        logger.warn(
            "There is no concept of local node in SpiNNaker, therefore you "
            "will receive the same functionality as self.all().")
        return self.all()

    def __len__(self):
        """
        returns the number of neurons in this pop view
        :return: int
        """
        return self._size

    def all(self):
        """
        returns a iterator for all the neurons in this pop view
        :return:iterator of NeuronCells
        """
        return iter(self._get_atoms_for_pop_view())

    def can_record(self, variable):
        """
        returns a bool which states if this PopulationView neurons can be
        recorded for the state requested.
        :param variable: state of either "spikes", "v", "gsyn"
        :return: bool
        """
        return self._population.can_record(variable)

    def describe(self, template='populationview_default.txt', engine='default'):
        """
        whatever: cloned and translated from pynn source code.
        :param template:
        :param engine:
        :return:
        """
        context = {"label": self._label,
                   "parent": self._population.label(),
                   "size": self._size,
                   "mask": self._neuron_filter}

        return descriptions.render(engine, template, context)

    def get(self, parameter_name, gather=True):
        """
        returns the parameters from all the atoms of this pop view
        :param parameter_name: the parameter to get values of
        :param gather: bool which has no context here
        :return: iterable.
        """
        # warn user
        if not gather:
            logging.warn("Spinnaker only does gather = true, will be ignored")

        # get pop view atoms
        pop_view_atoms = self._get_atoms_for_pop_view()
        elements = list()
        for atom in pop_view_atoms:
            elements.append(atom.get_param(parameter_name))
        return elements

    def getSpikes(self, gather=True, compatible_output=True):
        """
        gets the spikes from this pop view.
        :param gather: if they need to be gathered
        :param compatible_output: whatever
        :return: returns 2-column numpy array
        """
        return self._population.getSpikes(
            gather, compatible_output, self._neuron_filter)

    def get_gsyn(self, gather=True, compatible_output=True):
        """
        gets the gsyn from this pop view.
        :param gather: if they need to be gathered
        :param compatible_output: whatever
        :return: returns 2-column numpy array
        """
        return self._population.get_gsyn(
            gather, compatible_output, self._neuron_filter)

    def get_spike_counts(self, gather=True):
        """ Return the number of spikes for each neuron.
        :param gather: zzzzzzzzzzzzzzzzzzzzzzzz
        """
        return self._population.get_spike_counts(gather, self._neuron_filter)

    def get_v(self, gather=True, compatible_output=True):
        """
        gets the v from this pop view.
        :param gather: if they need to be gathered
        :param compatible_output: whatever
        :return: returns 2-column numpy array
        """
        return self._population.get_v(
            gather, compatible_output, self._neuron_filter)

    def id_to_index(self, id):
        """
        locates the index in the pop view for a given cell
        :param id: the cell to find.
        :return: the index in the population view.
        """
        pop_view_cells = self._get_atoms_for_pop_view()
        return pop_view_cells.index(id)

    def initialize(self, variable, value):
        """
        sets parameters with a given value set for all atoms in this
        population view
        :param variable: the variable to set
        :param value: the value to use
        :return: None
        """

        # get atoms in pop view
        pop_view_atoms = self._get_atoms_for_pop_view()

        high_level_function_utilties.initialize_parameters(
            variable, value, pop_view_atoms, self._size)

    def inject(self, current_source):
        """
        NEEDS EXTRA WORK FOR THIS
        :param current_source:
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def is_local(id):
        """
        has no meaning here
        :param id: blah
        :return: exception
        """
        raise exceptions.ConfigurationException(
            "This has no meaning in SpiNNaker. Go ask someone else.")

    def meanSpikeCount(self, gather=True):
        """
        returns the mean spike count
        :param gather: means nothing to spinnaker.
        :return: list of floats
        """
        return self._population.meanSpikeCount(gather, self._neuron_filter)

    def nearest(self, position):
        """
        gets the nearest neuron for this position
        :param position: the space position
        :return:
        """
        # get pop view positions
        if self._positions is None:
            self._positions = \
                self._population._generate_positions_for_atoms(
                    self._get_atoms_for_pop_view())
        # return closest position
        return self._population._nearest(position, self._positions)

    def printSpikes(self, file, gather=True, compatible_output=True):
        """
        returns the pop view spikes
        :param file: the absolute file path for where the gsyn are to be\
                    printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        """
        return self._population._print_spikes(
            file, gather, compatible_output, self._neuron_filter)

    def print_gsyn(self, file, gather=True, compatible_output=True):
        """
        returns the pop view gsyn
        :param file: the absolute file path for where the gsyn are to be\
                    printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        """
        return self._population._print_gsyn(
            file, gather, compatible_output, self._neuron_filter)

    def print_v(self, file, gather=True, compatible_output=True):
        """
        returns the pop view v
        :param file: the absolute file path for where the gsyn are to be\
                    printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        """
        return self._population._print_v(
            file, gather, compatible_output, self._neuron_filter)

    def randomInit(self, rand_distr):
        """
        sets up the membrane voltage of the pop view atoms
        :param rand_distr: the random distribution used for initialing v
        :return: None
        """
        self.initialize("v", rand_distr)

    def record(self, to_file=None):
        """
        sets all neurons in this pop view to record spikes
        :param to_file: the file path or a boolean
        :return: None
        """
        pop_view_atoms = self._get_atoms_for_pop_view()
        for atom in pop_view_atoms:
            atom.record_spikes(True)
            atom.record_spikes_to_file_flag(to_file)

    def record_gsyn(self, to_file=True):
        """
        sets all neurons in this pop view to record gsyn
        :param to_file: the file path or a boolean
        :return: None
        """
        pop_view_atoms = self._get_atoms_for_pop_view()
        for atom in pop_view_atoms:
            atom.set_record_gsyn(True)
            atom.record_gsyn_to_file_flag(to_file)

    def record_v(self, to_file=True):
        """
        sets all neurons in this pop view to record v
        :param to_file: the file path or a boolean
        :return: None
        """
        pop_view_atoms = self._get_atoms_for_pop_view()
        for atom in pop_view_atoms:
            atom.record_v(True)
            atom.record_v_to_file_flag(to_file)

    def rset(self, parametername, rand_distr):
        """
        sets all cells in this view with a given parametername with a value
        from this rand_distr
        :param parametername: parameter to set
        :param rand_distr: the random distribution
        :return:
        """
        self.initialize(parametername, rand_distr)

    def sample(self, n, rng=None):
        """
        builds a sample of neurons from the pop view and returns a new pop view
        :param n: the number of atoms to build
        :param rng: the random number distribution to use.
        :return: new populationView object
        """
        if self._size < n:
            raise exceptions.ConfigurationException(
                "Cant sample for more atoms than what reside in the "
                "population view.")
        if rng is None:
            rng = random.NumpyRNG()
        indices = rng.permutation(numpy.arange(len(self)))[0:n]
        return PopulationView(
            self, indices,
            "sampled_version of {} from {}".format(indices, self._label),
            self._spinnaker)

    def save_positions(self, file):
        """
        writes the positions of the atoms in this pop view.
        :param file:
        :return:
        """
        if self._positions is None:
            self._positions = \
                self._population._generate_positions_for_atoms(
                    self._get_atoms_for_pop_view())
        self._population._save_positions(file, self._positions)

    def set(self, param, val=None):
        """ Set one or more parameters for every cell in the population view.

        param can be a dict, in which case value should not be supplied, or a
        string giving the parameter name, in which case value is the parameter
        value. value can be a numeric value, or list of such
        (e.g. for setting spike times)::

          p.set("tau_m", 20.0).
          p.set({'tau_m':20, 'v_rest':-65})
        :param param: the parameter to set
        :param val: the value of the parameter to set.
        """
        # verify
        if not isinstance(self._population._vertex, AbstractPopulationSettable):
            raise KeyError("Population does not have property {}".format(
                param))
        if type(param) is not dict:
                raise Exception("Error: invalid parameter type for "
                                "set() function for population parameter."
                                " Exiting.")

        # set parameter
        if type(param) is str:
            if val is None:
                raise Exception("Error: No value given in set() function for "
                                "population parameter. Exiting.")
            self.initialize(param, val)
        else:
            # Add a dictionary-structured set of new parameters to the
            # current set:
            for (key, value) in param.iteritems():
                self.initialize(key, value)

    def tset(self, parametername, value_array):
        """ 'Topographic' set. Set the value of parametername to the values in\
            value_array, which must have the same dimensions as the Population
            view.
        :param parametername: the name of the parameter
        :param value_array: the array of values which must have the correct\
                number of elements.
        """
        if len(value_array) != self._size:
            raise exceptions.ConfigurationException(
                "To use tset, you must have a array of values which matches "
                "the size of the population. Please change this and try "
                "again, or alternatively, use set()")
        self.set(parametername, value_array)
