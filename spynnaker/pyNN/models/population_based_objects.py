# front end common imports
from spinn_front_end_common.utilities import exceptions
from spinn_front_end_common.abstract_models.abstract_changable_after_run \
    import AbstractChangableAfterRun

# pynn imports
from pyNN import descriptions, random

# spynnaker imports
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models import high_level_function_utilties
from spynnaker.pyNN.models.abstract_models.\
    abstract_population_settable import \
    AbstractPopulationSettable
from spynnaker.pyNN.models.neuron_cell import \
    NeuronCell
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

# pacman imports
from pacman.model.constraints.abstract_constraints.abstract_constraint\
    import AbstractConstraint
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint

# general imports
import logging
import numpy
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Lines for objects
# Assembly 42
# PopView 648
# Population 1142


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

        self._size = len(self._spinnaker.get_assembly_atom_mapping()[self])

    def _get_atoms_for_assembly(self):
        """
        helper method for getting atoms from pop view
        :return:
        """
        atom_mapping = self._spinnaker.get_assembly_atom_mapping()
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
        assembly_atom_mapping = self._spinnaker.get_assembly_atom_mapping()

        pop_atom_mappings = self._spinnaker.get_pop_atom_mapping()
        pop_view_atom_mapping = self._spinnaker.get_pop_view_atom_mapping()

        # separate the 3 types into the 2 important types
        populations, population_views = self._separate_input(
            populations, set(), set())

        # create holder for the assembly itself
        if self not in assembly_atom_mapping:
            assembly_atom_mapping[self] = list()

        # update assembly size
        size = 0
        for key in self._population_index_boundaries.keys():
            if size < key:
                size = key

        # update pop atoms
        for population in populations:

            # get pop based atoms
            atom_models_for_pop = \
                pop_atom_mappings[population._class][population]

            # update the two places for the assembly
            for atom in atom_models_for_pop:
                assembly_atom_mapping[self].append(atom)
                size += 1

            # update boundary tracker
            self._population_index_boundaries[size] = population

        # handle pop views atoms
        for population_view in population_views:
            related_population = population_view._population

            # check that related population not already stored via a population
            if related_population not in populations:

                # acquire pop view atoms
                model_class = related_population._class
                pop_view_atoms = pop_view_atom_mapping[population_view]

                # add mappings for both assembly and for the model level.
                for atom in pop_view_atoms:
                    if atom not in assembly_atom_mapping[self]:
                        assembly_atom_mapping[self].append(atom)
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
        # allow for scalar pops/views/assemblers
        if (isinstance(inputs, Population) or
                isinstance(inputs, PopulationView) or
                isinstance(inputs, Assembly)):
            inputs = [inputs]

        # filter input
        for input_pop in inputs:
            if isinstance(input_pop, Population):
                pops.add(input_pop)
            elif isinstance(input_pop, PopulationView):
                pop_views.add(input_pop)
            elif isinstance(input_pop, Assembly):
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

        # if only one element, hand it over otherwise hand over the assembly
        if len(final_assembly) == 1:
            return final_assembly._get_atoms_for_assembly()[0]
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
        self._size = len(self._spinnaker.get_assembly_atom_mapping()[self])

        return self

    def __iter__(self):
        """
        returns a iterator of the assembly atoms
        :return: iterator
        """
        return iter(self._spinnaker.get_assembly_atom_mapping()[self])

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
        gsyn_total = list()
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

        # convert into one list
        gsyn_total = numpy.vstack(gsyn_total)
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

    def getSpikes(self, gather=True, compatible_output=True):
        """
        gets the spikes from this pop view.
        :param gather: if they need to be gathered
        :param compatible_output: whatever
        :return: returns 2-column numpy array
        """
        start_point = 0
        spikes_total = list()
        for boundary_value in self._population_index_boundaries:
            # get pop/pop_view spikes
            spikes = self._population_index_boundaries[boundary_value].\
                getSpikes(gather, compatible_output)

            # update indices
            spikes[:, 0] += start_point

            # add to total
            spikes_total.append(spikes)

            # update point
            start_point += boundary_value

        # convert into one list
        spikes_total = numpy.vstack(spikes_total)
        return spikes_total

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
        v_total = list()
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

        # convert into one list
        v_total = numpy.vstack(v_total)
        return v_total

    def id_to_index(self, id):
        """
        returns the index in this assembly for a given cell
        :param id:  the neuron cell object to find the index of
        :return: index
        :rtype: int
        """
        assembly_cells = self._get_atoms_for_assembly()
        if isinstance(id, NeuronCell):
            return assembly_cells.index(id)
        if isinstance(id, Assembly):

            # handle the case of 1 element
            if len(id) == 1:
                atom = id[0]
                return assembly_cells.index(atom)

            # handle multiple atoms
            indices = list()
            for atom in id:
                indices.append(assembly_cells.index(atom))
            return indices
        else:
            raise exceptions.ConfigurationException("Dont recongise this id")

    def initialize(self, variable, value):
        """
        sets parameters with a given value set for all atoms in this
        population view
        :param variable: the variable to set
        :param value: the value to use
        :return: None
        """
        # check that vertex mapping has not occurred yet, If so, use vertices
        # for init, otherwise set atoms directly.
        if not self._check_for_vertex_mapping():
            # get atoms for assembly.
            assembly_atoms = self._get_atoms_for_assembly()

            # initialise_parameters.
            high_level_function_utilties.initialize_parameters(
                variable, value, assembly_atoms, self._size)
        else:
            for pop_pop_view in self._population_index_boundaries.values():

                # get mapped vertices
                mapped_verts, _ = self._get_mapped_vertex(pop_pop_view)

                # get the vertex and init attributes
                (vertex, _, _) = mapped_verts
                vertex.initialize_attr(variable, value)

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

    def record(self, to_file=None):
        """
        sets all neurons in this assembly to record spikes
        :param to_file: the file path or a boolean
        :return: None
        """
        if self._check_for_vertex_mapping():
            # locate vertex's to set to recording spikes
            for pop_pop_view in self._population_index_boundaries.values():
                (vertex, _, _) = self._get_mapped_vertex(pop_pop_view)
                if isinstance(pop_pop_view, Population):
                    vertex.set_recording_spikes(to_file)
                elif isinstance(pop_pop_view, PopulationView):
                    vertex.set_recording_spikes(
                        to_file, pop_pop_view._neuron_filter)
                else:
                    raise exceptions.ConfigurationException(
                        "Record method has found a object in the index "
                        "boundaries which isn't a population or population "
                        "view.")
        else:
            # set all the atoms directly for both states
            assembly_atoms = self._get_atoms_for_assembly()
            for atom in assembly_atoms:
                atom.record_spikes = True
                atom.record_spikes_to_file_flag = to_file

    def record_gsyn(self, to_file=None):
        """
        sets all neurons in this assembly to record gsyn
        :param to_file: the file path or a boolean
        :return: None
        """
        if self._check_for_vertex_mapping():
            # locate vertex's to set to recording spikes
            for pop_pop_view in self._population_index_boundaries.values():
                (vertex, _, _) = self._get_mapped_vertex(pop_pop_view)
                if isinstance(pop_pop_view, Population):
                    vertex.set_recording_gsyn(to_file)
                elif isinstance(pop_pop_view, PopulationView):
                    vertex.set_recording_gsyn(
                        to_file, pop_pop_view._neuron_filter)
        else:
            # set all the atoms directly for both states
            assembly_atoms = self._get_atoms_for_assembly()
            for atom in assembly_atoms:
                atom.set_record_gsyn = True
                atom.record_gsyn_to_file_flag = to_file

    def record_v(self, to_file=None):
        """
        sets all neurons in this assembly to record v
        :param to_file: the file path or a boolean
        :return: None
        """
        if self._check_for_vertex_mapping():
            # locate vertex's to set to recording spikes
            for pop_pop_view in self._population_index_boundaries.values():
                (vertex, _, _) = self._get_mapped_vertex(pop_pop_view)
                if isinstance(pop_pop_view, Population):
                    vertex.set_recording_v(to_file)
                elif isinstance(pop_pop_view, PopulationView):
                    vertex.set_recording_v(to_file, pop_pop_view._neuron_filter)
        else:
            # set all the atoms directly for both states
            assembly_atoms = self._get_atoms_for_assembly()
            for atom in assembly_atoms:
                atom.record_v = True
                atom.record_v_to_file_flag = to_file

    def rset(self, parametername, rand_distr):
        """
        sets all cells in this view with a given parametername with a value
        from this rand_distr
        :param parametername: parameter to set
        :param rand_distr: the random distribution
        :return:
        """
        if self._check_for_vertex_mapping():
            for pop_pop_view in self._population_index_boundaries.values():
                mapped_verts, _ = self._get_mapped_vertex(pop_pop_view)

                # get the vertex and init attributes
                (vertex, _, _) = mapped_verts
                vertex.set_value(parametername, rand_distr)
        else:
            self.set(parametername, rand_distr)

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

    def tset(self, parametername, value_array):
        """ 'Topographic' set. Set the value of parametername to the values in\
            value_array, which must have the same dimensions as the Population
            view.
        :param parametername: the name of the parameter
        :param value_array: the array of values which must have the correct\
                number of elements.
        """
        if hasattr(value_array, "__iter__") and hasattr(value_array, "__len__"):
            if len(value_array) != self._size:
                raise exceptions.ConfigurationException(
                    "To use tset, you must have a array of values which "
                    "matches the size of the population. Please change this"
                    " and try again, or alternatively, use set()")
            self.set(parametername, value_array)
        else:
            raise exceptions.ConfigurationException(
                "To use tset, you must have a array of values which "
                "matches the size of the population. Not a scalar. "
                "Please change this and try again, or alternatively, "
                "use set()")

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
        for pop_pop_view in self._population_index_boundaries.values():
            if issubclass(pop_pop_view, AbstractPopulationSettable):
                raise KeyError(
                    "Population does not have property {}".format(param))
            self._check_for_vertex_mapping()
        if self._check_for_vertex_mapping():
            for pop_pop_view in self._population_index_boundaries.values():
                mapped_verts, _ = self._get_mapped_vertex(pop_pop_view)

                # get the vertex and init attributes
                (vertex, _, _) = mapped_verts
                vertex.set_value(param, val)
        else:
            high_level_function_utilties.set_parameters(
                param, val, self._get_atoms_for_assembly(), None)

    @staticmethod
    def _get_mapped_vertex(pop_pop_view):
        """
        returns the mapping vertex object from the model types.
        :param pop_pop_view: a instance of a population or population view.
        :return: the mapped vertices object or raises a boom
        """
        if isinstance(pop_pop_view, Population):
            return pop_pop_view._mapped_vertices, None
        if isinstance(pop_pop_view, PopulationView):
            return pop_pop_view._population._mapped_vertices, \
                   pop_pop_view._neuron_filter
        raise exceptions.ConfigurationException(
            "Don't know what to do here.")

    def _check_for_vertex_mapping(self):
        """
        helper method for checking if the pops based in this assembly have
        been mapped to a vertex
        :return: bool statign if the pops have been mapped to vertices
        """
        for pop_pop_view in self._population_index_boundaries.values():
            if isinstance(pop_pop_view, Population):
                if pop_pop_view._mapped_vertices is not None:
                    return True
            if isinstance(pop_pop_view, PopulationView):
                if pop_pop_view._population._mapped_vertices is not None:
                    return True
        return False

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
                len(self._parent_population_or_population_view))

        # filter down to the population, over the pop view
        self._population = self.locate_parent_population()
        self._model_class = self._population._class

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
            return self._parent_population_or_population_view._population
        else:
            return self._parent_population_or_population_view

    def _update_atom_mapping(self):
        """
        updates the spinnaker atom mapping so that its aware of this pop view
        :return:
        """
        # check model exists correctly
        pop_view_atom_mappings = self._spinnaker.get_pop_view_atom_mapping()

        # if valid, add neuron param objects to this list as well
        # (assumes a ref copy)
        pop_view_atom_mappings[self] = list()

        pop_atoms = self._spinnaker.get_pop_atom_mapping()
        if self._parent_is_pop_view:
            atom_models_for_pop = pop_view_atom_mappings[
                self._parent_population_or_population_view]
        else:
            atom_models_for_pop = pop_atoms[self._model_class][
                self._parent_population_or_population_view]

        # filter atoms from the parent
        for atom_index in range(0, len(atom_models_for_pop)):
            if atom_index in self._neuron_filter:
                pop_view_atom_mappings[self].append(
                    atom_models_for_pop[atom_index])

    def _get_atoms_for_pop_view(self):
        """
        helper method for getting atoms from pop view
        :return:
        """
        atom_mapping = self._spinnaker.get_pop_view_atom_mapping()
        pop_view_atoms = atom_mapping[self]
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
            elements.append(atom.get(parameter_name))
        return elements

    def getSpikes(self, gather=True, compatible_output=True):
        """
        gets the spikes from this pop view.
        :param gather: if they need to be gathered
        :param compatible_output: whatever
        :return: returns 2-column numpy array
        """
        spikes = self._population._get_spikes(gather, compatible_output)

        # ensure that if you've gotten the spikes, not to print them out unless
        # it was actually asked for
        atoms = self._get_atoms_for_pop_view()
        for atom in atoms:
            if atom.record_spikes and atom.record_spikes_to_file_flag is None:
                atom.record_spikes_to_file_flag = False

        # filter out spikes from the pop not within this pop view
        view_neuron_filter = \
            high_level_function_utilties.translate_filter_to_ints(
                self._neuron_filter, self._population.size)
        mask = numpy.in1d(spikes[:, 0], view_neuron_filter)
        return spikes[mask]

    def get_gsyn(self, gather=True, compatible_output=True):
        """
        gets the gsyn from this pop view.
        :param gather: if they need to be gathered
        :param compatible_output: whatever
        :return: returns 2-column numpy array
        """
        gsyn = self._population._get_gsyn(gather, compatible_output)

        # ensure that if you've gotten the spikes, not to print them out unless
        # it was actually asked for
        atoms = self._get_atoms_for_pop_view()
        for atom in atoms:
            if atom.record_gsyn and atom.record_gsyn_to_file_flag is None:
                atom.record_gsyn_to_file_flag = False

        # filter out spikes from the pop not within this pop view
        view_neuron_filter = \
            high_level_function_utilties.translate_filter_to_ints(
                self._neuron_filter, self._population.size)
        mask = numpy.in1d(gsyn[:, 0], view_neuron_filter)
        return gsyn[mask]

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
        v = self._population._get_v(gather, compatible_output)
        # ensure that if you've gotten the spikes, not to print them out unless
        # it was actually asked for
        atoms = self._get_atoms_for_pop_view()
        for atom in atoms:
            if atom.record_v and atom.record_v_to_file_flag is None:
                atom.record_v_to_file_flag = False

        # filter out spikes from the pop not within this pop view
        view_neuron_filter = \
            high_level_function_utilties.translate_filter_to_ints(
                self._neuron_filter, self._population.size)
        mask = numpy.in1d(v[:,0], view_neuron_filter)
        return v[mask]

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

        if self._population._mapped_vertices is not None:
            (vertex, _, _) = self._population._mapped_vertices
            vertex.initialize(variable, value)
        else:
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
        if self._population._mapped_vertices is not None:
            (vertex, _, _) = self._population._mapped_vertices
            vertex.set_recording_spikes(to_file, self._neuron_filter)
        else:
            pop_view_atoms = self._get_atoms_for_pop_view()
            for atom in pop_view_atoms:
                atom.record_spikes = True
                atom.record_spikes_to_file_flag = to_file

    def record_gsyn(self, to_file=None):
        """
        sets all neurons in this pop view to record gsyn
        :param to_file: the file path or a boolean
        :return: None
        """
        if self._population._mapped_vertices is not None:
            (vertex, _, _) = self._population._mapped_vertices
            vertex.set_recording_gsyn(to_file, self._neuron_filter)
        else:
            pop_view_atoms = self._get_atoms_for_pop_view()
            for atom in pop_view_atoms:
                atom.record_gsyn = True
                atom.record_gsyn_to_file_flag = to_file

    def record_v(self, to_file=None):
        """
        sets all neurons in this pop view to record v
        :param to_file: the file path or a boolean
        :return: None
        """
        if self._population._mapped_vertices is not None:
            (vertex, _, _) = self._population._mapped_vertices
            vertex.set_recording_v(to_file, self._neuron_filter)
        else:
            pop_view_atoms = self._get_atoms_for_pop_view()
            for atom in pop_view_atoms:
                atom.record_v = True
                atom.record_v_to_file_flag = to_file

    def rset(self, parametername, rand_distr):
        """
        sets all cells in this view with a given parametername with a value
        from this rand_distr
        :param parametername: parameter to set
        :param rand_distr: the random distribution
        :return:
        """
        if self._population._mapped_vertices is not None:
            (vertex, _, _) = self._population._mapped_vertices
            vertex.set_value(parametername, rand_distr)
        else:
            self.set(parametername, rand_distr)

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
        if not issubclass(self._population._class, AbstractPopulationSettable):
            raise KeyError("Population does not have property {}".format(
                param))

        high_level_function_utilties.set_parameters(
            param, val, self._get_atoms_for_pop_view(),
            self._population._mapped_vertices)

    def tset(self, parametername, value_array):
        """ 'Topographic' set. Set the value of parametername to the values in\
            value_array, which must have the same dimensions as the Population
            view.
        :param parametername: the name of the parameter
        :param value_array: the array of values which must have the correct\
                number of elements.
        """
        if hasattr(value_array, "__iter__") and hasattr(value_array, "__len__"):
            if len(value_array) != self._size:
                raise exceptions.ConfigurationException(
                    "To use tset, you must have a array of values which "
                    "matches the size of the population. Please change this"
                    " and try again, or alternatively, use set()")
            self.set(parametername, value_array)
        else:
            raise exceptions.ConfigurationException(
                "To use tset, you must have a array of values which "
                "matches the size of the population. Not a scalar. "
                "Please change this and try again, or alternatively, "
                "use set()")


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

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 structure=None):
        if (size is not None and size <= 0) or size is None:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative, None or zero size.")

        # Create a partitionable_graph vertex for the population and add it
        # to PACMAN
        self._pop_label = label
        if label is None:
            self._pop_label = "Population {}".format(
                spinnaker.none_labelled_vertex_count)
            spinnaker.increment_none_labelled_vertex_count()

        # copy the parameters so that the end users are not exposed to the
        # additions placed by spinnaker.
        internal_cellparams = dict(cellparams)

        # create population vertex.
        self._class = cellclass
        self._mapped_vertices = None
        self._spinnaker = spinnaker
        self._delay_vertex = None

        # initialise common stuff
        self._size = size
        self._requires_remapping = True
        self._constraints = list()

        # update atom mapping
        self._update_spinnaker_atom_mapping(
            internal_cellparams, structure,
            {'machine_time_step': spinnaker.machine_time_step,
             'time_scale_factor': spinnaker.timescale_factor,
             'spikes_per_second': None,
             'ring_buffer_sigma': None,
             'incoming_spike_buffer_size': None})

    def set_mapping(self, vertex_mapping):
        self._mapped_vertices = vertex_mapping

    @property
    def constraints(self):
        return self._constraints

    def _update_spinnaker_atom_mapping(
            self, cellparams, structure, population_level_parameters):
        """
        update the neuron cell mapping object of spinnaker
        :param cellparams:
        :return:
        """
        atom_mappings = self._spinnaker.get_pop_atom_mapping()
        if self._class not in atom_mappings:
            atom_mappings[self._class] = dict()
        atom_mappings[self._class][self] = list()

        # filter pop level parameters from the model_variables and the
        # default handed down from a population
        population_level_parameters_fresh = dict()
        for population_level_parameter in self._class.model_variables:
            if population_level_parameter in population_level_parameters:
                population_level_parameters_fresh[population_level_parameter]\
                    = population_level_parameters[population_level_parameter]
            else:
                population_level_parameters_fresh[population_level_parameter]\
                    = None
            if population_level_parameter in cellparams:
                population_level_parameters_fresh[population_level_parameter]\
                    = cellparams[population_level_parameter]
        population_level_parameters = population_level_parameters_fresh

        # filter cell params for any population level parameters given by
        # the end user, If any exist, add them and then remove from cell params
        to_delete = list()
        for cell_param in cellparams:
            if cell_param in population_level_parameters:
                population_level_parameters[cell_param] = cellparams[cell_param]
                to_delete.append(cell_param)

        # delete population level parameters from end user cell params
        for cell_param_name in to_delete:
            del cellparams[cell_param_name]

        # convert default into atom scope
        default_params = self._convert_parameters_to_atom_scope(
            self._class.default_parameters, self._size,
            self._class.is_array_parameters)

        # collect state variables from class
        state_variables = self._class.state_variables

        # collect fixed cell parameters
        fixed_cell_params = self._class.fixed_parameters

        # convert end user params into atom scope
        cellparams = self._convert_parameters_to_atom_scope(
            cellparams, self._size, self._class.is_array_parameters)

        # build cell objects
        neuron_param_objects = list()
        for _ in range(0, self._size):
            neuron_param_objects.append(
                NeuronCell(
                    default_params.keys(), state_variables,
                    fixed_cell_params, population_level_parameters,
                    self._class, structure))

        # update with default parameters
        for atom in range(0, self._size):
            for cell_param in default_params:
                neuron_param_objects[atom].set_param(
                    cell_param, default_params[cell_param][atom])

        # update atoms with end user parameters
        for atom in range(0, self._size):
            for cell_param in cellparams:
                neuron_param_objects[atom].set_param(
                    cell_param, cellparams[cell_param][atom])

        # update atom mapping
        for atom in range(0, self._size):
            atom_mappings[self._class][self].\
                append(neuron_param_objects[atom])

    @staticmethod
    def _convert_parameters_to_atom_scope(
            converted_parameters, n_atoms, is_array):
        default_params = dict()
        for param_name in converted_parameters:
            default_params[param_name] = utility_calls.convert_param_to_numpy(
                converted_parameters[param_name], n_atoms,
                param_name in is_array)
        return default_params

    def _get_atoms_for_pop(self):
        """
        helper method for getting atoms from pop
        :return: list of atoms for this pop
        """
        atom_mapping = self._spinnaker.get_pop_atom_mapping()
        model_name_atoms = atom_mapping[self._class]
        pop_atoms = model_name_atoms[self]
        return pop_atoms

    @property
    def requires_mapping(self):
        """
        checks through all atoms of this population and sees if they require
        mapping process
        :return: boolean
        """
        if self._requires_remapping:
            return True

        if self._mapped_vertices is not None:
            (vertex, _, _) = self._mapped_vertices
            if isinstance(vertex, AbstractChangableAfterRun):
                return vertex.requires_mapping
            return True
        elif issubclass(self._class, AbstractChangableAfterRun):
            atoms = self._get_atoms_for_pop()
            for atom in atoms:
                if atom.requires_mapping:
                    return True
            return False
        return True

    def mark_no_changes(self):
        """
        inform all cells to start re tracking changes from now on.
        :return:
        """
        if self._mapped_vertices is not None:
            (vertex, _, _) = self._mapped_vertices
            if isinstance(vertex, AbstractChangableAfterRun):
                vertex.mark_no_changes()
        elif issubclass(self._class, AbstractChangableAfterRun):
            atoms = self._get_atoms_for_pop()
            for atom in atoms:
                atom.mark_no_changes()
        self._requires_remapping = False

    def __add__(self, other):
        """ Merges populations
        """
        if isinstance(other, Population) or isinstance(other, PopulationView):

            # if valid, make an assembly
            return Assembly(
                [self, other],
                label="Assembly for {} and {}".format(
                    self._pop_label, other.label),
                spinnaker=self._spinnaker)
        else:
            # not valid, blow up
            raise exceptions.ConfigurationException(
                "Can only add a population or a population view to "
                "a population.")

    def all(self):
        """ Iterator over cell ids on all nodes.
        """
        return self.__iter__()

    @property
    def conductance_based(self):
        """ True if the population uses conductance inputs
        """
        return issubclass(self._class.input_type, InputTypeConductance)

    @property
    def default_parameters(self):
        """ The default parameters of the vertex from this population
        :return:
        """
        return self._class.default_parameters

    def describe(self, template='population_default.txt', engine='default'):
        """ Returns a human-readable description of the population.

        The output may be customised by specifying a different template
        together with an associated template engine (see ``pyNN.descriptions``)

        If template is None, then a dictionary containing the template context
        will be returned.
        """

        context = {
            "label": self._pop_label,
            "celltype": self._class.model_name(),
            "structure": None,
            "size": self._size,
            "first_id": 0,
            "last_id": self._size - 1,
        }

        if self.structure:
            context["structure"] = self.structure.describe(template=None)
        return descriptions.render(engine, template, context)

    def __getitem__(self, index):
        """
        gets a item(s) (which is either a int, or a slice object)
        :param index: the slice or index
        :return: a cell or a pop view
        """
        if isinstance(index, int):
            pop_view_atoms = self._get_atoms_for_pop()
            return pop_view_atoms[index]
        elif isinstance(index, slice):
            return PopulationView(self, index, None, self._spinnaker)

    def get(self, parameter_name, gather=False):
        """ Get the values of a parameter for every local cell in the\
            population.
        """
        if issubclass(self._class, AbstractPopulationSettable):
            # build a empty numpy array.
            values = numpy.empty(shape=1)

            # get atoms
            atoms = self._get_atoms_for_pop()

            # for each atom, add the parameter to the array
            for atom in atoms:
                values.append(atom.get(parameter_name))
            return values
        raise KeyError("Population does not have a property {}".format(
            parameter_name))

    # noinspection PyPep8Naming
    def getSpikes(self, compatible_output=True, gather=True):
        """
        Return a 2-column numpy array containing cell ids and spike times for\
        recorded cells.
        """
        spikes = self._get_spikes(gather, compatible_output)

        # ensure that if you've gotten the spikes, not to print them out unless
        # it was actually asked for
        atoms = self._get_atoms_for_pop()
        for atom in atoms:
            if atom.record_spikes and atom.record_spikes_to_file_flag is None:
                atom.record_spikes_to_file_flag = False
        return spikes

    def _get_spikes(self, compatible_output, gather):
        """
        private method for:
        Return a 2-column numpy array containing cell ids and spike times for\
        recorded cells.
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will "
                        " execute as if gather was true anyhow")

        if not compatible_output:
            logger.warn(
                "Spynnaker only supports compatible_output = true, will "
                " execute as if compatible_output was true anyhow")

        if issubclass(self._class, AbstractSpikeRecordable):

            # check atoms to see if its recording
            atoms = self._get_atoms_for_pop()
            recording_spikes = False
            for atom in atoms:
                if atom.record_spikes:
                    recording_spikes = True

            if not recording_spikes:
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

        # extract spikes from the vertices which hold some part of
        # this population
        (vertex, start_atoms, end_atoms) = self._mapped_vertices
        return vertex.get_spikes(
            self._spinnaker.placements, self._spinnaker.graph_mapper,
            self._spinnaker.buffer_manager, start_atoms, end_atoms)

    def get_spike_counts(self, gather=True):
        """ Return the number of spikes for each neuron.
        """
        spikes = self.getSpikes(True, gather)
        n_spikes = {}
        counts = numpy.bincount(spikes[:, 0].astype(dtype="uint32"),
                                minlength=self._size)
        for i in range(self._size):
            n_spikes[i] = counts[i]
        return n_spikes

    # noinspection PyUnusedLocal
    def get_gsyn(self, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time and synaptic
        conductance's for recorded cells.
        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        """

        gsyn = self._get_gsyn(gather, compatible_output)

        # ensure that if you've gotten the v, not to print them out unless
        # it was actually asked for
        atoms = self._get_atoms_for_pop()
        for atom in atoms:
            if atom.record_gsyn and atom.record_gsyn_to_file_flag is None:
                atom.record_gsyn_to_file_flag = False
        return gsyn

    def _get_gsyn(self, gather, compatible_output):
        """
        private method for:
        Return a 3-column numpy array containing cell ids, time and synaptic
        conductance's for recorded cells.
        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        if not compatible_output:
            logger.warn("Spynnaker only supports compatible_output = True, "
                        "will execute as if gather was true anyhow")

        if issubclass(self._class, AbstractGSynRecordable):

            # check atoms to see if its recording
            atoms = self._get_atoms_for_pop()
            recording_gsyn = False
            for atom in atoms:
                if atom.record_gsyn:
                    recording_gsyn = True

            if not recording_gsyn:
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

        # extract spikes from the vertices which hold some part of
        # this population
        (vertex, start_atoms, end_atoms) = self._mapped_vertices
        gsyn = vertex.get_gsyn(
            self._spinnaker.no_machine_time_steps,
            self._spinnaker.placements, self._spinnaker.graph_mapper,
            self._spinnaker.buffer_manager, start_atoms, end_atoms)
        return gsyn

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

        v = self._get_v(gather, compatible_output)
        # ensure that if you've gotten the v, not to print them out unless
        # it was actually asked for
        atoms = self._get_atoms_for_pop()
        for atom in atoms:
            if atom.record_v and atom.record_v_to_file_flag is None:
                atom.record_v_to_file_flag = False
        return v

    def _get_v(self, gather, compatible_output):
        """
        private method for getting membrane potential
        Return a 3-column numpy array containing cell ids, time, and V_m for
        recorded cells.
        :param gather:
            not used - inserted to match PyNN specs
        :type gather: bool
        :param compatible_output:
            not used - inserted to match PyNN specs
        :type compatible_output: bool
        :return:3-column numpy array containing cell ids, time, and V_m
        """
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        if not compatible_output:
            logger.warn("Spynnaker only supports compatible_output = True, "
                        "will execute as if gather was true anyhow")

        if issubclass(self._class, AbstractVRecordable):
            recording = False
            for atom in self._get_atoms_for_pop():
                if atom.record_v:
                    recording = True
            if not recording:
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

        # extract spikes from the vertices which hold some part of
        # this population
        (vertex, start_atoms, end_atoms) = self._mapped_vertices
        return vertex.get_v(
            self._spinnaker.no_machine_time_steps,
            self._spinnaker.placements, self._spinnaker.graph_mapper,
            self._spinnaker.buffer_manager, start_atoms, end_atoms)

    def id_to_index(self, id):
        """ Given the ID(s) of cell(s) in the Population, return its (their)\
            index (order in the Population).
        """
        atoms = self._get_atoms_for_pop()
        return atoms.index(id)

    def id_to_local_index(self, id):
        """ Given the ID(s) of cell(s) in the Population, return its (their)\
            index (order in the Population), counting only cells on the local\
            MPI node.
        """
        return self.id_to_index(id)

    def initialize(self, variable, value):
        """ Set the initial value of one of the state variables of the neurons\
            in this population.

        """
        if not issubclass(self._class,
                          AbstractPopulationInitializable):
            raise KeyError(
                "Population does not support the initialisation of {}".format(
                    variable))

        if self._mapped_vertices is not None:
            (vertex, _, _) = self._mapped_vertices
            vertex.initialize(variable, value)
        else:
            pop_atoms = self._get_atoms_for_pop()
            high_level_function_utilties.initialize_parameters(
                variable, value, pop_atoms, self._size)

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
        :param variable: the parameter name to check recording for
        """
        if variable == "spikes":
            if issubclass(self._class, AbstractSpikeRecordable):
                return True
        elif variable == "v":
            if issubclass(self._class, AbstractVRecordable):
                return True
        elif variable == "gsyn":
            if issubclass(self._class, AbstractGSynRecordable):
                return True
        else:
            raise exceptions.ConfigurationException(
                "The only variables that are currently recordable are:"
                "1. spikes, 2. v, 3. gsyn.")

    def inject(self, current_source):
        """ Connect a current source to all cells in the Population.
        """
        # TODO:
        raise NotImplementedError

    def __iter__(self):
        """ Iterate over local cells
        """
        atoms = self._get_atoms_for_pop()
        return iter(atoms)

    def __len__(self):
        """ Get the total number of cells in the population.
        """
        return self._size

    @property
    def label(self):
        """ The label of the population
        """
        return self._pop_label

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
        :param position: space position
        """
        return self._nearest(position, self.positions)

    def _nearest(self, position, positions):
        """ Return the neuron closest to the specified position
        :param position: space position
        """
        # doesn't always work correctly if a position is equidistant between
        # two neurons, i.e. 0.5 should be rounded up, but it isn't always.
        # also doesn't take account of periodic boundary conditions
        pos = numpy.array([position] * positions.shape[1]).transpose()
        dist_arr = (positions - pos) ** 2
        distances = dist_arr.sum(axis=0)
        nearest = distances.argmin()
        return self[nearest]

    # noinspection PyPep8Naming
    def randomInit(self, distribution):
        """ Set initial membrane potentials for all the cells in the\
            population to random values.

        :param `pyNN.random.RandomDistribution` distribution:
            the distribution used to draw random values.

        """
        self.initialize('v', distribution)

    def record(self, to_file=None):
        """ Record spikes from all cells in the Population.

        :param to_file: file to write the spike data to
        """

        if not issubclass(self._class, AbstractSpikeRecordable):
            raise Exception(
                "This population does not support the recording of spikes!")

        if self._mapped_vertices is not None:
            (vertex, _, _) = self._mapped_vertices
            vertex.set_recording_spikes(to_file)
        else:
            # set the atoms to record spikes to the given file path
            atoms = self._get_atoms_for_pop()
            for atom in atoms:
                atom.record_spikes = True
                atom.record_spikes_to_file_flag = to_file

    def record_gsyn(self, to_file=None):
        """ Record the synaptic conductance for all cells in the Population.

        :param to_file: the file to write the recorded gsyn to.
        """
        if not issubclass(self._class, AbstractGSynRecordable):
            raise Exception(
                "This population does not support the recording of gsyn")
        if not issubclass(self._class.input_type, InputTypeConductance):
            logger.warn(
                "You are trying to record the conductance from a model which "
                "does not use conductance input.  You will receive "
                "current measurements instead.")

        if self._mapped_vertices is not None:
            (vertex, _, _) = self._mapped_vertices
            vertex.set_recording_gsyn(to_file)
        else:
            # set the atoms to record gsyn to the given file path
            atoms = self._get_atoms_for_pop()
            for atom in atoms:
                atom.record_gsyn = True
                atom.record_gsyn_to_file_flag = to_file

    def record_v(self, to_file=None):
        """ Record the membrane potential for all cells in the Population.

        :param to_file: the file to write the recorded v to.
        """
        if not issubclass(self._class, AbstractVRecordable):
            raise Exception(
                "This population does not support the recording of v")

        if self._mapped_vertices is not None:
            (vertex, _, _) = self._mapped_vertices
            vertex.set_recording_v(to_file)
        else:
            # set the atoms to record v to the given file path
            atoms = self._get_atoms_for_pop()
            for atom in atoms:
                atom.record_v = True
                atom.record_v_to_file_flag = to_file

    @property
    def positions(self):
        """ Return the position array for structured populations.
        """
        atoms = self._get_atoms_for_pop()
        return self._generate_positions_for_atoms(atoms)

    @staticmethod
    def _generate_positions_for_atoms(atoms):
        positions = None
        used_structure = None
        for atom_index in range(0, len(atoms)):
            atom = atoms[atom_index]
            if atom.position is None:
                if atom.structure is None:
                    raise ValueError("attempted to retrieve positions "
                                     "for an unstructured population")

                # get positions as needed
                if atom_index == 0:
                    positions = atom.structure.generate_positions(len(atoms))
                    used_structure = atom.structure
                elif atom.structure != used_structure:
                    raise exceptions.ConfigurationException(
                        "Atoms in the population have different "
                        "structures, this is considered an error here.")

                # update atom with position
                atom.position = positions[atom_index]
        return positions

    # noinspection PyPep8Naming
    def printSpikes(self, file, gather=True, compatible_output=True):
        """ Write spike time information from the population to a given file.
        :param file: the absolute file path for where the spikes are to\
                    be printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        """
        self._print_spikes(file, gather, compatible_output)

    def _print_spikes(self, filename, gather, compatible_output,
                      neuron_filter=None):
        """ Write spike time information from the population to a given file.
        :param filename: the absolute file path for where the spikes are to\
                    be printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param neuron_filter: neuron filter or none if all of pop is to
        be returned
        """
        spikes = self.getSpikes(compatible_output, gather)
        if spikes is not None:

            # get data items needed for the writing
            file_based_atoms = 0
            last_id = None
            first_id = None

            # iterate for data
            atoms = self._get_atoms_for_pop()
            for atom_index in range(0, len(atoms)):
                atom = atoms[atom_index]
                if (atom.record_spikes_to_file_flag and
                        (neuron_filter is None or  neuron_filter[atom_index])):
                    file_based_atoms += 1
                    last_id = atom_index
                    if first_id is None:
                        first_id = atom_index

            # write blurb
            utility_calls.check_directory_exists_and_create_if_not(filename)
            spike_file = open(filename, "w")
            spike_file.write("# first_id = {}\n".format(first_id))
            spike_file.write("# n = {}\n".format(file_based_atoms))
            spike_file.write("# last_id = {}\n".format(last_id))

            # write data
            for (neuronId, time) in spikes:
                # check that atom is in filter, is to file flag
                if (neuron_filter is None or
                        (neuron_filter[neuronId] and
                             atoms[neuronId].record_spikes_to_file_flag)):
                    spike_file.write("{}\t{}\n".format(time, neuronId))
            spike_file.close()

    def print_gsyn(self, file, gather=True, compatible_output=True):
        """ Write conductance information from the population to a given file.
        :param file: the absolute file path for where the gsyn are to be\
                    printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        """
        return self._print_gsyn(file, gather, compatible_output)

    def _print_gsyn(self, filename, gather, compatible_output,
                    neuron_filter=None):
        """ Write conductance information from the population to a given file.
        :param filename: the absolute file path for where the gsyn are to be\
                    printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        :param neuron_filter: neuron filter or none if all of pop is to
        be returned
        """
        time_step = (self._spinnaker.machine_time_step * 1.0) / 1000.0
        gsyn = self.get_gsyn(gather, compatible_output)

        # get data items needed for the writing
        file_based_atoms = 0
        last_id = None
        first_id = None

        # iterate for data
        atoms = self._get_atoms_for_pop()
        for atom_index in range(0, len(atoms)):
            atom = atoms[atom_index]
            if (atom.record_gsyn_to_file_flag and
                    (neuron_filter is None or neuron_filter[atom_index])):
                file_based_atoms += 1
                last_id = atom_index
                if first_id is None:
                    first_id = atom_index

        if filename is not None:
            utility_calls.check_directory_exists_and_create_if_not(filename)
            file_handle = open(filename, "w")
            file_handle.write("# first_id = {}\n".format(first_id))
            file_handle.write("# n = {}\n".format(file_based_atoms))
            file_handle.write("# dt = {}\n".format(time_step))
            file_handle.write("# last_id = {}\n".format(last_id))
            file_handle = open(filename, "w")
            for (neuronId, time, value_e, value_i) in gsyn:

                # check that atom is in filter, is to file flag
                if (neuron_filter is None or
                         (neuron_filter[neuronId] and
                              atoms[neuronId].record_gsyn_to_file_flag)):
                    file_handle.write("{}\t{}\t{}\t{}\n".format(
                        time, neuronId, value_e, value_i))
            file_handle.close()

    def print_v(self, file, gather=True, compatible_output=True):
        """ Write membrane potential information from the population to a\
            given file.
        :param file: the absolute file path for where the voltage are to\
                     be printed in
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        :param gather: Supported from the PyNN language, but ignored here
        """
        return self._print_v(file, gather, compatible_output)

    def _print_v(self, filename, gather, compatible_output,
                 neuron_filter=None):
        """ Write conductance information from the population to a given file.
        :param filename: the absolute file path for where the gsyn are to be\
                    printed in
        :param gather: Supported from the PyNN language, but ignored here
        :param compatible_output: Supported from the PyNN language,
         but ignored here
        :param neuron_filter: neuron filter or none if all of pop is to
        be returned
        """
        time_step = (self._spinnaker.machine_time_step * 1.0) / 1000.0
        v = self.get_v(gather, compatible_output)

        if filename is not None:
            utility_calls.check_directory_exists_and_create_if_not(filename)
            file_handle = open(filename, "w")

            # get data items needed for the writing
            file_based_atoms = 0
            last_id = None
            first_id = None

            # iterate for data
            atoms = self._get_atoms_for_pop()
            for atom_index in range(0, len(atoms)):
                atom = atoms[atom_index]
                if (atom.record_v_to_file_flag and
                        (neuron_filter is None or neuron_filter[atom_index])):
                    file_based_atoms += 1
                    last_id = atom_index
                    if first_id is None:
                        first_id = atom_index

            # write blurb
            file_handle.write("# first_id = {}\n".format(first_id))
            file_handle.write("# n = {}\n".format(file_based_atoms))
            file_handle.write("# dt = {}\n".format(time_step))
            file_handle.write("# last_id = {}\n".format(last_id))

            # write data
            for (neuronId, time, value) in v:
                if (neuron_filter is None or
                        (neuron_filter[neuronId] and
                            atoms[neuronId].record_v_to_file_flag)):
                    file_handle.write(
                        "{}\t{}\t{}\n".format(time, neuronId, value))
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
        if self._size < n:
            raise exceptions.ConfigurationException(
                "Cant sample for more atoms than what reside in the "
                "population view.")
        if rng is None:
            rng = random.NumpyRNG()
        indices = rng.permutation(numpy.arange(len(self)))[0:n]
        label = self._get_atoms_for_pop()[0]
        return PopulationView(
            self, indices,
            "sampled_version of {} from {}"
            .format(indices, label),
            self._spinnaker)

    def save_positions(self, file):  # @ReservedAssignment
        """ Save positions to file.
            :param file: the file to write the positions to.
        """
        self._save_positions(file, self.positions)

    @staticmethod
    def _save_positions(file_name, positions):
        """
        Save positions to file.
        :param file_name: the file to write the positions to.
        :param positions: the positions to write to a file.
        :return: None
        """
        file_handle = open(file_name, "w")
        file_handle.write(positions)
        file_handle.close()

    def set(self, param, val=None):
        """ Set one or more parameters for every cell in the population.

        param can be a dict, in which case value should not be supplied, or a
        string giving the parameter name, in which case value is the parameter
        value. value can be a numeric value, or list of such
        (e.g. for setting spike times)::

          p.set("tau_m", 20.0).
          p.set({'tau_m':20, 'v_rest':-65})
        :param param: the parameter to set
        :param val: the value of the parameter to set.
        """
        if not issubclass(self._class, AbstractPopulationSettable):
            raise KeyError("Population does not have property {}".format(
                param))

        high_level_function_utilties.set_parameters(
            param, val, self._get_atoms_for_pop(), self._mapped_vertices)



    @property
    def structure(self):
        """ Return the structure for the population.
        """
        pop_atoms = self._get_atoms_for_pop()
        structure = None
        for atom in pop_atoms:
            if structure is None:
                structure = atom.structure
            elif structure != atom.structure:
                raise exceptions.ConfigurationException(
                    "The neurons in this population have different structures.")
        return structure

    # NONE PYNN API CALL
    def set_constraint(self, constraint):
        """ Apply a constraint to a population that restricts the processor\
            onto which its sub-populations will be placed.
        """
        if isinstance(constraint, AbstractConstraint):
            self._constraints.append(constraint)
        else:
            raise exceptions.ConfigurationException(
                "the constraint entered is not a recognised constraint")
        self._requires_remapping = True

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
        self._constraints.append(PlacerChipAndCoreConstraint(x, y, p))
        self._requires_remapping = True

    # NONE PYNN API CALL
    def set_mapping_constraint(self, constraint_dict):
        """ Add a placement constraint - for backwards compatibility

        :param constraint_dict: A dictionary containing "x", "y" and\
                    optionally "p" as keys, and ints as values
        :type constraint_dict: dict of str->int
        """
        self.add_placement_constraint(**constraint_dict)
        self._requires_remapping = True

    # NONE PYNN API CALL
    def set_model_based_max_atoms_per_core(self, new_value):
        """ Supports the setting of each models max atoms per core parameter

        :param new_value: the new value for the max atoms per core.
        """
        if hasattr(self._class, "set_model_max_atoms_per_core"):
            self._class.set_model_max_atoms_per_core(new_value)
            self._requires_remapping = True
        else:
            raise exceptions.ConfigurationException(
                "This population does not support its max_atoms_per_core "
                "variable being adjusted by the end user")

    @property
    def size(self):
        """ The number of neurons in the population
        :return:
        """
        return self._size

    def tset(self, parametername, value_array):
        """ 'Topographic' set. Set the value of parametername to the values in\
            value_array, which must have the same dimensions as the Population.
        :param parametername: the name of the parameter
        :param value_array: the array of values which must have the correct\
                number of elements.
        """
        if hasattr(value_array, "__iter__") and hasattr(value_array, "__len__"):
            if len(value_array) != self._size:
                raise exceptions.ConfigurationException(
                    "To use tset, you must have a array of values which "
                    "matches the size of the population. Please change this"
                    " and try again, or alternatively, use set()")
            self.set(parametername, value_array)
        else:
            raise exceptions.ConfigurationException(
                "To use tset, you must have a array of values which "
                "matches the size of the population. Not a scalar. "
                "Please change this and try again, or alternatively, "
                "use set()")

    def _end(self):
        """ Do final steps at the end of the simulation
        """
        atoms = self._get_atoms_for_pop()
        record_spikes = False
        record_v = False
        record_gsyn = False

        for atom in atoms:
            if ((atom.record_spikes_to_file_flag is None or
                    atom.record_spikes_to_file_flag) and atom.record_spikes):
                record_spikes = True
            if ((atom.record_v_to_file_flag is None or
                    atom.record_v_to_file_flag) and atom.record_v):
                record_v = True
            if ((atom.record_gsyn_to_file_flag is None or
                    atom.record_gsyn_to_file_flag) and atom.record_gsyn):
                record_gsyn = True

        if record_spikes:
            self.printSpikes("spikes")
        if record_gsyn:
            self.print_gsyn("gsyn")
        if record_v:
            self.print_v("v")

    @property
    def _get_vertex(self):
        raise NotImplementedError

    @property
    def _internal_delay_vertex(self):
        return self._delay_vertex

    @_internal_delay_vertex.setter
    def _internal_delay_vertex(self, delay_vertex):
        self._delay_vertex = delay_vertex
