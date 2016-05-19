from pyNN import descriptions, random
from pacman.model.constraints.abstract_constraints.abstract_constraint\
    import AbstractConstraint
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from spynnaker.pyNN.models import high_level_function_utilties
from spynnaker.pyNN.models.neuron_cell import \
    NeuronCell
from spynnaker.pyNN.models.pynn_assembly import Assembly
from spynnaker.pyNN.models.pynn_population_view import PopulationView
from spynnaker.pyNN.utilities import utility_calls
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
    :returns a list of vertexes and edges
    """

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 structure=None):
        if (size is not None and size <= 0) or size is None:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative, None or zero size.")

        # Create a partitionable_graph vertex for the population and add it
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
        internal_cellparams['machine_time_step'] = spinnaker.machine_time_step
        internal_cellparams['timescale_factor'] = spinnaker.timescale_factor

        # create population vertex.
        self._original_vertex = cellclass(**internal_cellparams)
        self._mapped_vertices = dict()
        self._spinnaker = spinnaker
        self._delay_vertex = None

        self._update_spinnaker_atom_mapping(cellparams, structure)

        # initialise common stuff
        self._size = size
        self._requires_remapping = True

    def _update_spinnaker_atom_mapping(self, cellparams, structure):
        """
        update the neuron cell mapping object of spinnaker
        :param cellparams:
        :return:
        """
        model_name = self._original_vertex.model_name
        atom_mappings = self._spinnaker.get_atom_mapping()
        if model_name not in atom_mappings:
            atom_mappings[model_name] = dict()
        atom_mappings[model_name][self] = list()
        params = dict()
        neuron_param_object = \
            NeuronCell(self._original_vertex.default_parameters,
                       self._original_vertex, structure)
        for cell_param in cellparams:
                params[cell_param] = self.get(cell_param)
        for atom in range(0, self._size):
            for cell_param in cellparams:
                neuron_param_object.set_param(
                    cell_param, params[cell_param][atom])
            atom_mappings[model_name][self].\
                append(neuron_param_object)

    def _get_atoms_for_pop(self):
        """
        helper method for getting atoms from pop
        :return: list of atoms for this pop
        """
        atom_mapping = self._spinnaker.get_atom_mapping()
        model_name_atoms = atom_mapping[self._original_vertex.model_name]
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

        if isinstance(self._original_vertex, AbstractChangableAfterRun):
            atoms = self._get_atoms_for_pop()
            for atom in atoms:
                if atom.has_change_that_requires_mapping():
                    return True
            return False
        return True

    def mark_no_changes(self):
        """
        inform all cells to start re tracking changes from now on.
        :return:
        """
        if isinstance(self._original_vertex, AbstractChangableAfterRun):
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
                    self._original_vertex.label, other.label),
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
        return isinstance(self._original_vertex.input_type,
                          InputTypeConductance)

    @property
    def default_parameters(self):
        """ The default parameters of the vertex from this population
        :return:
        """
        return self._original_vertex.default_parameters

    def describe(self, template='population_default.txt', engine='default'):
        """ Returns a human-readable description of the population.

        The output may be customised by specifying a different template
        together with an associated template engine (see ``pyNN.descriptions``)

        If template is None, then a dictionary containing the template context
        will be returned.
        """
        context = {
            "label": self._original_vertex.label,
            "celltype": self._original_vertex.model_name,
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
        if isinstance(self._original_vertex, AbstractPopulationSettable):
            # build a empty numpy array.
            values = numpy.empty(shape=1)

            # get atoms
            atoms = self._get_atoms_for_pop()

            # for each atom, add the parameter to the array
            for atom in atoms:
                values.append(atom.get_param(parameter_name))
            return values
        raise KeyError("Population does not have a property {}".format(
            parameter_name))

    # noinspection PyPep8Naming
    def getSpikes(self, compatible_output=True, gather=True):
        """
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

        if isinstance(self._original_vertex, AbstractSpikeRecordable):

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

        total_spikes = numpy.zeros((0, 2))

        # extract spikes from the vertices which hold some part of
        # this population
        for vertex in self._mapped_vertices:
            spikes = vertex.get_spikes(
                self._spinnaker.placements, self._spinnaker.graph_mapper,
                self._spinnaker.buffer_manager, self._mapped_vertices[vertex])
            # TODO reshape and add to total spikes
            total_spikes.append(spikes)

        return total_spikes

    def get_spike_counts(self, gather=True):
        """ Return the number of spikes for each neuron.
        """
        spikes = self.getSpikes(True, gather)
        n_spikes = {}
        counts = numpy.bincount(spikes[:, 0].astype(dtype="uint32"),
                                minlength=self._original_vertex.n_atoms)
        for i in range(self._original_vertex.n_atoms):
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

        if isinstance(self._original_vertex, AbstractGSynRecordable):

            # check atoms to see if its recording
            atoms = self._get_atoms_for_pop()
            recording_gsyn = False
            for atom in atoms:
                if atom.is_recording_gsyn:
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

        total_gsyn = numpy.zeros((0, 4))
        # extract spikes from the vertices which hold some part of
        # this population
        for vertex in self._mapped_vertices:
            gsyn = vertex.get_gsyn(
                self._spinnaker.no_machine_time_steps,
                self._spinnaker.placements, self._spinnaker.graph_mapper,
                self._spinnaker.buffer_manager, self._mapped_vertices[vertex])
            # TODO reshape and add to total spikes
            total_gsyn.append(gsyn)

        return total_gsyn

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
        if isinstance(self._original_vertex, AbstractVRecordable):
            if not self._original_vertex.is_recording_v():
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

        total_gsyn = numpy.zeros((0, 4))
        # extract spikes from the vertices which hold some part of
        # this population
        for vertex in self._mapped_vertices:
            gsyn = vertex.get_gsyn(
                self._spinnaker.no_machine_time_steps,
                self._spinnaker.placements, self._spinnaker.graph_mapper,
                self._spinnaker.buffer_manager, self._mapped_vertices[vertex])
            # TODO reshape and add to total spikes
            total_gsyn.append(gsyn)

        return total_gsyn

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
        if not isinstance(self._original_vertex,
                          AbstractPopulationInitializable):
            raise KeyError(
                "Population does not support the initialisation of {}".format(
                    variable))

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
            if isinstance(self._original_vertex, AbstractSpikeRecordable):
                return True
        elif variable == "v":
            if isinstance(self._original_vertex, AbstractVRecordable):
                return True
        elif variable == "gsyn":
            if isinstance(self._original_vertex, AbstractGSynRecordable):
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
        return self._original_vertex.label

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

        if not isinstance(self._original_vertex, AbstractSpikeRecordable):
            raise Exception(
                "This population does not support the recording of spikes!")

        # set the atoms to record spikes to the given file path
        atoms = self._get_atoms_for_pop()
        for atom in atoms:
            atom.record_spikes(True)
            atom.record_spikes_to_file_flag(to_file)

    def record_gsyn(self, to_file=None):
        """ Record the synaptic conductance for all cells in the Population.

        :param to_file: the file to write the recorded gsyn to.
        """
        if not isinstance(self._original_vertex, AbstractGSynRecordable):
            raise Exception(
                "This population does not support the recording of gsyn")
        if not isinstance(self._original_vertex.input_type, InputTypeConductance):
            logger.warn(
                "You are trying to record the conductance from a model which "
                "does not use conductance input.  You will receive "
                "current measurements instead.")

        # set the atoms to record gsyn to the given file path
        atoms = self._get_atoms_for_pop()
        for atom in atoms:
            atom.record_gsyn(True)
            atom.record_gsyn_to_file_flag(to_file)

    def record_v(self, to_file=None):
        """ Record the membrane potential for all cells in the Population.

        :param to_file: the file to write the recorded v to.
        """
        if not isinstance(self._original_vertex, AbstractVRecordable):
            raise Exception(
                "This population does not support the recording of v")

        # set the atoms to record v to the given file path
        atoms = self._get_atoms_for_pop()
        for atom in atoms:
            atom.record_v(True)
            atom.record_v_to_file_flag(to_file)

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
        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        if not compatible_output:
            logger.warn("Spynnaker only supports compatible_output = True, "
                        "will execute as if gather was true anyhow")
            compatible_output = True

        spikes = self.getSpikes(compatible_output)
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
                        neuron_filter[atom_index]):
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

        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        if not compatible_output:
            logger.warn("Spynnaker only supports compatible_output = True, "
                        "will execute as if gather was true anyhow")
            compatible_output = True

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
                    neuron_filter[atom_index]):
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

        if not gather:
            logger.warn("Spynnaker only supports gather = true, will execute"
                        " as if gather was true anyhow")
        if not compatible_output:
            logger.warn("Spynnaker only supports compatible_output = True, "
                        "will execute as if gather was true anyhow")
            compatible_output = True

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
                        neuron_filter[atom_index]):
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
        return PopulationView(
            self, indices,
            "sampled_version of {} from {}"
            .format(indices, self._original_vertex.label),
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
        if not isinstance(self._original_vertex, AbstractPopulationSettable):
            raise KeyError("Population does not have property {}".format(
                param))

        if type(param) is str:
            if val is None:
                raise Exception("Error: No value given in set() function for "
                                "population parameter. Exiting.")
            self._original_vertex.set_value(param, val)
            return

        if type(param) is not dict:
                raise Exception("Error: invalid parameter type for "
                                "set() function for population parameter."
                                " Exiting.")

        # Add a dictionary-structured set of new parameters to the current set:
        # get atoms in pop view
        pop_atoms = self._get_atoms_for_pop()
        for (key, value) in param.iteritems():
            high_level_function_utilties.initialize_parameters(
                key, value, pop_atoms, self._size)

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
            self._original_vertex.add_constraint(constraint)
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
        self._original_vertex.add_constraint(
            PlacerChipAndCoreConstraint(x, y, p))
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
        if hasattr(self._original_vertex, "set_model_max_atoms_per_core"):
            self._original_vertex.set_model_max_atoms_per_core(new_value)
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
        return self._original_vertex.n_atoms

    def tset(self, parametername, value_array):
        """ 'Topographic' set. Set the value of parametername to the values in\
            value_array, which must have the same dimensions as the Population.
        :param parametername: the name of the parameter
        :param value_array: the array of values which must have the correct\
                number of elements.
        """
        if len(value_array) != self._original_vertex.n_atoms:
            raise exceptions.ConfigurationException(
                "To use tset, you must have a array of values which matches "
                "the size of the population. Please change this and try "
                "again, or alternatively, use set()")
        self.set(parametername, value_array)

    def _end(self):
        """ Do final steps at the end of the simulation
        """
        atoms = self._get_atoms_for_pop()
        record_spikes = False
        record_v = False
        record_gsyn = False

        for atom in atoms:
            if atom.record_spikes_to_file_flag is not None:
                record_spikes = True
            if atom.record_v_to_file_flag is not None:
                record_v = True
            if atom.record_gsyn_to_file_flag is not None:
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
