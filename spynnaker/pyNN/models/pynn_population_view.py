from spinn_front_end_common.utilities import exceptions

import logging

from spynnaker.pyNN.models.pynn_assemblier import Assemblier
from spynnaker.pyNN.models.pynn_population import Population

logger = logging.getLogger(__name__)


class PopulationView(object):

    def __init__(
            self, parent_population_or_population_view, neuron_filter, label,
            spinnaker):
        """
        constructor for the pop view
        :param parent_population_or_population_view:
        :param neuron_filter:
        :param label:
        :param spinnaker:
        :return:
        """
        self._spinnaker = spinnaker
        self._label = label
        self._parent_is_pop_view = False
        self._parent_population_or_population_view = \
            parent_population_or_population_view

        # store filter for usage
        self._neuron_filter = neuron_filter
        # turn filter from the 3 versions into an index based one
        self._translate_filter()

        # filter down to the population, over the pop view
        self._population = self.locate_parent_population()

        # update atom mapping for spinnaker understanding
        self._update_atom_mapping()

    def _translate_filter(self):
        """
        translates filter from bool / slice / index into index
        :return: None
        """
        # filter slice based filter into index's
        if isinstance(self._neuron_filter, slice):

            new_filter = self._convert_slice_into_index_list(
                self._neuron_filter,
                self._parent_population_or_population_view.size)

        # check for bool based filter
        elif len(self._neuron_filter) != 0:

            # if bool based filter, convert into index's based.
            if isinstance(self._neuron_filter[0], bool):

                # test the bool filters length to work correctly.
                if len(self._neuron_filter) != \
                        self._parent_population_or_population_view.size:
                    raise exceptions.ConfigurationException(
                        "The bool array must be the same size as the parent "
                        "population /population view")

                # convert into indices
                new_filter = list()
                for index in range(0, len(self._neuron_filter)):
                    if self._neuron_filter[index]:
                        new_filter.append(index)
                self._neuron_filter = new_filter

            # not bool or int, blow up
            elif not isinstance(self._neuron_filter[0], int):
                raise exceptions.ConfigurationException(
                    "The population view filter can only be either:"
                    "1. a slice, 2. a array of ints, a array of bools.")
        # not a bool, int, or a slice. blow up
        else:
            raise exceptions.ConfigurationException(
                    "The population view filter can only be either:"
                    "1. a slice, 2. a array of ints, a array of bools.")

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

    @staticmethod
    def _convert_slice_into_index_list(slice_object, size):
        """
        :param slice_object: the slice
        :param size: the size of the pop to slice into
        :return: the new filter of index's
        """
        position = slice_object.start
        new_filter = list()
        while position < slice_object.stop:
            if 0 < position < size:
                new_filter.append(position)
                position += slice_object.step
        return new_filter

    def _update_atom_mapping(self):
        # check model exists correctly
        model_name = self._population._vertex.model_name()
        atom_mappings = self._spinnaker.get_atom_mapping()
        if model_name not in atom_mappings:
            raise exceptions.ConfigurationException(
                "The population to view in this population view does not"
                " exist in our standard populations. Please fix and try again")

        # if valid, add neuron param objects to this list as well
        # (assumes a ref copy)
        atom_mappings[model_name][self] = list()
        atom_models_for_pop = atom_mappings[model_name][
            self._parent_population_or_population_view]

        # filter atoms from the parent
        for atom_index in range(0, len(atom_models_for_pop)):
            if atom_index in self._neuron_filter:
                atom_mappings[model_name][self].append(
                    atom_models_for_pop[atom_index])

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

        # build assemblier
        return Assemblier(
            populations=[self, other],
            label="{}:{}".format(self._label, other.label),
            spinnaker=self._spinnaker)

    def __getitem__(self, index):
        if isinstance(index, int):
           index = [index]
        elif isinstance(index, slice):

    def __iter__(self):
        logger.warn(
            "There is no concept of local node in SpiNNaker, therefore you "
            "will recieve the same functionality as self.all().")
        return self.all()

    def __len__(self):
        pass

    def all(self):
        pass

    def can_record(self, variable):
        pass

    def describe(self, template='populationview_default.txt', engine='default'):
        pass

    def get(self, parameter_name, gather=False):
        pass

    def getSpikes(self, gather=True, compatible_output=True):
        pass

    def get_gsyn(self, gather=True, compatible_output=True):
        pass

    def get_spike_counts(self, gather=True):
        pass

    def get_v(self, gather=True, compatible_output=True):
        pass

    def id_to_index(self, id):
        pass

    def initialize(self, variable, value):
        pass

    def inject(self, current_source):
        pass

    def is_local(self, id):
        pass

    def meanSpikeCount(self, gather=True):
        pass

    def nearest(self, position):
        pass

    def printSpikes(self, file, gather=True, compatible_output=True):
        pass

    def print_gsyn(self, file, gather=True, compatible_output=True):
        pass

    def print_v(self, file, gather=True, compatible_output=True):
        pass

    def randomInit(self, rand_distr):
        pass

    def record(self, to_file=True):
        pass

    def record_gsyn(self, to_file=True):
        pass

    def record_v(self, to_file=True):
        pass

    def rset(self, parametername, rand_distr):
        pass

    def sample(self, n, rng=None):
        pass

    def save_positions(self, file):
        pass

    def set(self, param, val=None):
        pass

    def tset(self, parametername, value_array):
        pass
