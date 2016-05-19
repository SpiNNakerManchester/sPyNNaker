# spynnaker related imports
import numpy
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_population_view import PopulationView
from spynnaker.pyNN.models import high_level_function_utilties

# front end common imports
from spinn_front_end_common.utilities import exceptions

# general imports
import logging
from collections import OrderedDict
from pyNN import descriptions
from spynnaker.pyNN.utilities import utility_calls

logger = logging.getLogger(__name__)


class Assembly(object):
    """
    Assembly: a view on a collection of populations/population views / assembles
    """

    def __init__(self, populations, label, spinnaker):

        self._spinnaker = spinnaker

        # update label accordingly
        if label is None:
            self._label = "Assembler {}".format(
                spinnaker.none_labelled_assembly_count())
            spinnaker.increment_none_labelled_assembly_count()

        # stores for pops for adding functionality
        self._population_index_boundaries = OrderedDict()

        # update atom mapping
        self._update_atom_mapping(populations)

        self._size = len(self._spinnaker.get_atom_mapping()[self])

    def _get_atoms_for_assembly(self):
        """
        helper method for getting atoms from pop view
        :return:
        """
        atom_mapping = self._spinnaker.get_atom_mapping()
        assembly_atoms = atom_mapping[self]
        return assembly_atoms

    def _update_atom_mapping(self, populations):
        """
        translate the populations / population views or assemblies into the
        basic list of populations, without duplicates
        :param populations:
        :return: set of populations
        """

        # get atom mapping
        atom_mappings = self._spinnaker.get_atom_mapping()

        # separate the 3 types into the 2 important types
        populations, population_views = self._separate_input(
            populations, set(), set())

        # create holder for the assembly itself
        if self not in atom_mappings:
            atom_mappings[self] = list()

        # update assembly size
        size = 0
        for key in self._population_index_boundaries.keys():
            if size < key:
                size = key

        # update pop atoms
        for population in populations:
            # make new store
            model_name = population._vertex.model_name()
            if self not in atom_mappings[model_name]:
                atom_mappings[model_name][self] = list()

            # get pop based atoms
            atom_models_for_pop = atom_mappings[model_name][population]

            # update the two places for the assembly
            for atom in atom_models_for_pop:
                atom_mappings[model_name][self].append(atom)
                atom_mappings[self].append(atom)
                size += 1

            # update boundary tracker
            self._population_index_boundaries[size] = population

        # handle pop views atoms
        for population_view in population_views:
            related_population = population_view._population

            # check that related population not already stored via a population
            if related_population not in populations:

                # acquire pop view atoms
                model_name = related_population._vertex.model_name()
                pop_view_atoms = atom_mappings[model_name][population_view]

                # add mappings for both assembly and for the model level.
                for atom in pop_view_atoms:
                    if atom not in atom_mappings[self]:
                        atom_mappings[self].append(atom)
                        if self not in atom_mappings[model_name]:
                            atom_mappings[model_name][self] = list()
                        atom_mappings[model_name][self].appedn(atom)
                        size += 1
                self._population_index_boundaries[size] = population_view
            else:
                logging.warn(
                    "tried to add a PopulationView to an Assembly when its "
                    "parent Population is already been added. Will ignore "
                    "the population view.")

    def _separate_input(self, inputs, pops, pop_views):
        """
        takes all the inputs and splits them into populations and population
        views. Assemblies are broken down into its constituent pops and
        population views.
        :param inputs: the total populations / population views / assemblies.
        :param pops: the list to put populations into
        :param pop_views: the list to put population views into.
        :return: the population and population view objects.
        """
        for input_pop in inputs:
            if isinstance(input_pop, Population):
                pops.add(input_pop)
            if isinstance(input_pop, PopulationView):
                pop_views.add(input_pop)
            if isinstance(input_pop, Assembly):
                return self._separate_input(
                    input_pop._population_index_boundaries.values,
                    pops, pop_views)
            else:
                raise exceptions.ConfigurationException(
                    "Assembly can only handle populations, population views or"
                    " other assemblies.")
        return pops, pop_views

    def __add__(self, other):
        """
        returns a new assembly with the extra other.
        :param other: other population, population view or assembly.
        :return:
        """
        if other == self:
            raise exceptions.ConfigurationException(
                "Cannot add myself to myself")
        else:
            new_list = self._population_index_boundaries.values() + other
            return Assembly(
                new_list,
                "Assembly with {} and {}".format(
                    self._population_index_boundaries.values(), other),
                self._spinnaker)

    def __getitem__(self, index):
        """
        returns an assembly which covers the filter build from index
        :param index: the filter to use
        :return: An Assembly.
        """
        # get filter over the entire assembly.
        neuron_filter = high_level_function_utilties.\
            translate_filter_to_boolean_format(index, self._size)

        # start the search
        start_position = 0

        # build final assembly
        final_assembly = Assembly(
            [], "assembly from {} with {} filter".format(self, neuron_filter),
            self._spinnaker)

        # take each boundary case individually.
        for boundary_value in self._population_index_boundaries:

            # check that if the filter wants it all.
            all_valid = True
            for element_index in range(start_position, boundary_value):
                if not neuron_filter[element_index]:
                    all_valid = False

            # if valid, add the population.
            if all_valid:
                final_assembly += \
                    self._population_index_boundaries[boundary_value]
            else:
                # if not all, build a pop view on it
                pop_view_filter = neuron_filter[start_position:boundary_value]
                pop_view = PopulationView(
                    self._population_index_boundaries[boundary_value],
                    pop_view_filter,
                    "Pop view with filter {}".format(pop_view_filter),
                    self._spinnaker)
                final_assembly += pop_view

            # update position
            start_position += boundary_value
        return final_assembly

    def __iadd__(self, other):
        """
        adds a pop or pop view or assembly to this assembly
        :param other:  pop or pop view or assembly to be added to this assembly
        :return: None
        """
        # update mapping with the new stuff
        self._update_atom_mapping(other)

        # update size
        self._size = len(self._spinnaker.get_atom_mapping[self])

    def __iter__(self):
        """
        returns a iterator of the assembly atoms
        :return: iterator
        """
        return iter(self._spinnaker.get_atom_mapping()[self])

    def __len__(self):
        """
        returns the length of atoms in this assembly.
        :return: int
        """
        return self._size

    def describe(self, template='assembly_default.txt', engine='default'):
        """
        returns a human readable description of the assembly.

        The output may be customized by specifying a different template
        together with an associated template engine (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template context
        will be returned.
        :param template: the different format to write
        :param engine: the writer for the template.
        :return: ????????
        """
        context = {
            "label": self._label,
            "populations":
                [p.describe(template=None)
                 for p in self._population_index_boundaries.values]}
        return descriptions.render(engine, template, context)

    def get_gsyn(self, gather=True, compatible_output=True):
        """
        gets gsyn for all cells within the assembly.
        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        :return: 4 dimensional numpy array
        """
        start_point = 0
        gsyn_total = numpy.empty(shape=[4])
        for boundary_value in self._population_index_boundaries:
            # get pop/pop_view gsyn
            gsyn = self._population_index_boundaries[boundary_value].\
                get_gsyn(gather, compatible_output)

            # update indices
            gsyn[:, 0] += start_point

            # add to total
            gsyn_total.append(gsyn)

            # update point
            start_point += boundary_value
        return gsyn_total

    def get_population(self, label):
        """
        locate a given population/population_view by its label in this assembly.
        :param label: the label of the population/population_view to find
        :return: the population or population_view
        :raises: KeyError if no population exists
        """
        for pop in self._population_index_boundaries.values():
            if pop.label == label:
                return label
        raise KeyError("Population / Population view does not exist in this "
                       "Assembly")

    def get_spike_counts(self, gather=True):
        """
        Returns the number of spikes for each neuron.
        :param gather: gather means nothing to Spinnaker
        :return:
        """
        start_point = 0
        spike_count_total = {}
        for boundary_value in self._population_index_boundaries:
            spike_count = self._population_index_boundaries[boundary_value]\
                .get_spike_counts(gather)

            # update indices
            spike_count[:, 0] += start_point

            # add to total
            spike_count_total += spike_count

            # update point
            start_point += boundary_value
        return spike_count_total

    def get_v(self, gather=True, compatible_output=True):
        """
        gets v for all cells within the assembly.
        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        :return: 4 dimensional numpy array
        """
        start_point = 0
        v_total = numpy.empty(shape=[2])
        for boundary_value in self._population_index_boundaries:
            # get pop/pop_view gsyn
            v = self._population_index_boundaries[boundary_value].\
                get_v(gather, compatible_output)

            # update indices
            v[:, 0] += start_point

            # add to total
            v_total.append(v)

            # update point
            start_point += boundary_value
        return v_total

    def id_to_index(self, id):
        """
        returns the index in this assembly for a given cell
        :param id:  the neuron cell object to find the index of
        :return: index
        :rtype: int
        """
        assembly_cells = self._get_atoms_for_assembly()
        return assembly_cells.index(id)

    def initialize(self, variable, value):
        """
        sets parameters with a given value set for all atoms in this
        population view
        :param variable: the variable to set
        :param value: the value to use
        :return: None
        """
        # get atoms in assembly
        assembly_atoms = self._get_atoms_for_assembly()

        high_level_function_utilties.initialize_parameters(
            variable, value, assembly_atoms, self._size)

    def inject(self, current_source):
        """
        needs looking at.
        :param current_source:
        :return:
        """
        raise NotImplementedError

    def meanSpikeCount(self, gather=True):
        """
        returns the mean spike count for the entire assembly
        :param gather:
        :return:
        """
        spike_counts = self.get_spike_counts(gather)
        total_spikes = sum(spike_counts.values())
        return total_spikes / self._size

    def printSpikes(self, file, gather=True, compatible_output=True):
        """ Write spike time information from the assembly to a given file.
        :param file: the absolute file path for where the spikes are to\
                    be printed in
        :param gather: Supported from the PyNN language, but ignored here
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        if not compatible_output:
            logger.warn("Spynnaker only supports compatible_output = True, "
                        "will execute as if gather was true anyhow")
            compatible_output = True
        spikes = self._get_spikes(gather, compatible_output)
        if spikes is not None:
            first_id = 0
            num_neurons = len(self._get_atoms_for_assembly())
            dimensions = len(self._get_atoms_for_assembly())
            last_id = len(self._get_atoms_for_assembly()) - 1
            utility_calls.check_directory_exists_and_create_if_not(file)
            spike_file = open(file, "w")
            spike_file.write("# first_id = {}\n".format(first_id))
            spike_file.write("# n = {}\n".format(num_neurons))
            spike_file.write("# dimensions = [{}]\n".format(dimensions))
            spike_file.write("# last_id = {}\n".format(last_id))
            for (neuronId, time) in spikes:
                spike_file.write("{}\t{}\n".format(time, neuronId))
            spike_file.close()

    def _get_spikes(self, gather, compatible_output):
        """
        gets spikes for all cells within the assembly.
        :return: 2 dimensional numpy array
        """
        start_point = 0
        spikes_total = numpy.empty(shape=[2])
        for boundary_value in self._population_index_boundaries:
            # get pop/pop_view gsyn
            spikes = self._population_index_boundaries[boundary_value].\
                get_spikes(gather, compatible_output)

            # update indices
            spikes[:, 0] += start_point

            # add to total
            spikes_total.append(spikes)

            # update point
            start_point += boundary_value
        return spikes_total

    def print_gsyn(self, file, gather=True, compatible_output=True):
        """ Write gsyn time information from the assembly to a given file.
        :param file: the absolute file path for where the spikes are to\
                    be printed in
        :param gather: Supported from the PyNN language, but ignored here
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        if not compatible_output:
            logger.warn("Spynnaker only supports compatible_output = True, "
                        "will execute as if gather was true anyhow")
            compatible_output = True
        time_step = (self._spinnaker.machine_time_step * 1.0) / 1000.0
        gsyn = self.get_gsyn(gather, compatible_output)
        first_id = 0
        num_neurons = len(self._get_atoms_for_assembly())
        dimensions = len(self._get_atoms_for_assembly())
        utility_calls.check_directory_exists_and_create_if_not(file)
        file_handle = open(file, "w")
        file_handle.write("# first_id = {}\n".format(first_id))
        file_handle.write("# n = {}\n".format(num_neurons))
        file_handle.write("# dt = {}\n".format(time_step))
        file_handle.write("# dimensions = [{}]\n".format(dimensions))
        file_handle.write("# last_id = {{}}\n".format(num_neurons - 1))
        file_handle = open(file, "w")
        for (neuronId, time, value_e, value_i) in gsyn:
            file_handle.write("{}\t{}\t{}\t{}\n".format(
                time, neuronId, value_e, value_i))
        file_handle.close()

    def print_v(self, file, gather=True, compatible_output=True):
        """ Write conductance information from the population to a given file.
        :param filename: the absolute file path for where the gsyn are to be\
                    printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        :param neuron_filter: neuron filter or none if all of pop is to
        be returned
        """

        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        if not compatible_output:
            logger.warn("Spynnaker only supports compatible_output = True, "
                        "will execute as if gather was true anyhow")
            compatible_output = True

        time_step = (self._spinnaker.machine_time_step * 1.0) / 1000.0
        v = self.get_v(gather, compatible_output)
        utility_calls.check_directory_exists_and_create_if_not(file)
        file_handle = open(file, "w")
        first_id = 0
        num_neurons = len(self._get_atoms_for_assembly())
        dimensions = len(self._get_atoms_for_assembly())
        file_handle.write("# first_id = {}\n".format(first_id))
        file_handle.write("# n = {}\n".format(num_neurons))
        file_handle.write("# dt = {}\n".format(time_step))
        file_handle.write("# dimensions = [{}]\n".format(dimensions))
        file_handle.write("# last_id = {}\n".format(num_neurons - 1))
        for (neuronId, time, value) in v:
            file_handle.write("{}\t{}\t{}\n".format(time, neuronId, value))
        file_handle.close()

    def record(self, to_file=True):
        """
        sets all neurons in this assembly to record spikes
        :param to_file: the file path or a boolean
        :return: None
        """
        assembly_atoms = self._get_atoms_for_assembly()
        for atom in assembly_atoms:
            atom.record_spikes(True)
            atom.record_spikes_to_file_flag(to_file)

    def record_gsyn(self, to_file=True):
        """
        sets all neurons in this assembly to record gsyn
        :param to_file: the file path or a boolean
        :return: None
        """
        assembly_atoms = self._get_atoms_for_assembly()
        for atom in assembly_atoms:
            atom.set_record_gsyn(True)
            atom.record_gsyn_to_file_flag(to_file)

    def record_v(self, to_file=True):
        """
        sets all neurons in this assembly to record v
        :param to_file: the file path or a boolean
        :return: None
        """
        assembly_atoms = self._get_atoms_for_assembly()
        for atom in assembly_atoms:
            atom.record_v(True)
            atom.record_v_to_file_flag(to_file)

    def save_positions(self, file):
        """
        writes the positions of the atoms in this pop view.
        :param file:
        :return:
        """
        for boundary_value in self._population_index_boundaries:
            # get pop/pop_view gsyn
            self._population_index_boundaries[boundary_value]\
                .save_positions(file)
