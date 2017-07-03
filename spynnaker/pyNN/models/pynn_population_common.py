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
from spynnaker.pyNN.utilities import globals_variables
from spynnaker.pyNN.models.abstract_models.abstract_contains_units import \
    AbstractContainsUnits

from spinn_front_end_common.utilities import exceptions
from spinn_front_end_common.abstract_models.abstract_changable_after_run \
    import AbstractChangableAfterRun

import logging
logger = logging.getLogger(__file__)


class PyNNPopulationCommon(object):
    def __init__(
            self, spinnaker_control, size, vertex, structure,
            initial_values):
        if size is not None and size <= 0:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative or zero size.")

        # copy the parameters so that the end users are not exposed to the
        # additions placed by spinnaker.
        if initial_values is not None:
            for name, value in initial_values:
                self._vertex.set_value(name, value)

        self._vertex = vertex
        self._spinnaker_control = spinnaker_control
        self._delay_vertex = None

        # Internal structure now supported 23 November 2014 ADR
        # structure should be a valid Space.py structure type.
        # generation of positions is deferred until needed.
        if structure:
            self._structure = structure
            self._positions = None
        else:
            self._structure = None

        # add objects to the spinnaker control class
        self._spinnaker_control.add_population(self)
        self._spinnaker_control.add_application_vertex(self._vertex)

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

    @requires_mapping.setter
    def requires_mapping(self, new_value):
        self._change_requires_mapping = new_value

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
        if globals_variables.get_simulator().has_ran and not isinstance(
                self._vertex, AbstractChangableAfterRun):
            raise Exception("Population does not support changes after run")
        self._vertex.initialize(variable, utility_calls.convert_param_to_numpy(
            value, self._vertex.n_atoms))

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

    @label.setter
    def label(self, new_value):
        self._vertex.label = new_value

    @property
    def local_size(self):
        """ The number of local cells
        """

        # Doesn't make much sense on SpiNNaker
        return self._size

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

        if globals_variables.get_simulator().has_ran and not isinstance(
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
        if (globals_variables.get_simulator().has_ran and not
            globals_variables.get_simulator().has_reset_last and
                isinstance(self._vertex, AbstractReadParametersBeforeSet) and
                not self._has_read_neuron_parameters_this_run):

            # locate machine vertices from the application vertices
            machine_vertices = globals_variables.get_simulator().graph_mapper\
                .get_machine_vertices(self._vertex)

            # go through each machine vertex and read the neuron parameters
            # it contains
            for machine_vertex in machine_vertices:

                # tell the core to rewrite neuron params back to the
                # sdram space.
                placement = globals_variables.get_simulator().placements.\
                    get_placement_of_vertex(machine_vertex)

                self._vertex.read_parameters_from_machine(
                    globals_variables.get_simulator().transceiver, placement,
                    globals_variables.get_simulator().graph_mapper.get_slice(
                        machine_vertex))

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

    @staticmethod
    def create_label(model_label, pop_level_label):
        """ helper method for choosing a label from model and population levels

        :param model_label: the model level label
        :param pop_level_label: the pop level label
        :return: the new model level label
        """
        cell_label = None
        if model_label is None and pop_level_label is None:
            cell_label = "Population {}".format(
                globals_variables.get_simulator().none_labelled_vertex_count)
            globals_variables.get_simulator(). \
                increment_none_labelled_vertex_count()
        elif model_label is None and pop_level_label is not None:
            cell_label = pop_level_label
        elif model_label is not None and pop_level_label is None:
            cell_label = model_label
        elif model_label is not None and pop_level_label is not None:
            cell_label = pop_level_label
            logger.warn("Don't know which label to use. Will use pop "
                        "label and carry on")
        return cell_label

    def _get_variable_unit(self, parameter_name):
        """ helper method for getting units from a parameter used by the vertex

        :param parameter_name: the parameter name to find the units for
        :return: the units in string form
        """
        if isinstance(self._vertex, AbstractContainsUnits):
            return self._vertex.get_units(parameter_name)
