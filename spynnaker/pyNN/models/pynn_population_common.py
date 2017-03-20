from spinn_front_end_common.abstract_models. \
    abstract_changable_after_run import AbstractChangableAfterRun
from spinn_front_end_common.utilities import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_contains_units import \
    AbstractContainsUnits
from spynnaker.pyNN.models.abstract_models.abstract_population_settable import \
    AbstractPopulationSettable
from spynnaker.pyNN.utilities import globals_variables


class PyNNPopulationCommon(object):
    def __init__(
            self, spinnaker_control, size, vertex, structure,
            initial_values):

        self._spinnaker_control = spinnaker_control
        self._vertex = vertex
        self._delay_vertex = None

        # initialise common stuff
        self._size = size
        self._record_spike_file = None
        self._record_v_file = None
        self._record_gsyn_file = None

        # parameter
        self._change_requires_mapping = True

        # Internal structure now supported 23 November 2014 ADR
        # structure should be a valid Space.py structure type.
        # generation of positions is deferred until needed.
        if structure:
            self._structure = structure
            self._positions = None
        else:
            self._structure = None

        if size is not None and size <= 0:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative or zero size.")

        # copy the parameters so that the end users are not exposed to the
        # additions placed by spinnaker.
        if initial_values is not None:
            for name, value in initial_values:
                self._vertex.set_value(name, value)

        # add objects to the spinnaker control class
        self._spinnaker_control.add_population(self)
        self._spinnaker_control.add_application_vertex(self._vertex)

    @property
    def requires_mapping(self):
        if isinstance(self._vertex, AbstractChangableAfterRun):
            return self._vertex.requires_mapping
        return self._change_requires_mapping

    @requires_mapping.setter
    def requires_mapping(self, new_value):
        self._change_requires_mapping = new_value

    def mark_no_changes(self):
        self._change_requires_mapping = False
        if isinstance(self._vertex, AbstractChangableAfterRun):
            self._vertex.mark_no_changes()

    @staticmethod
    def create_label(label):
        # Create a graph vertex for the population and add it
        # to PACMAN
        cell_label = label
        if label is None:
            cell_label = "Population {}".format(
                globals_variables.get_simulator().none_labelled_vertex_count)
            globals_variables.get_simulator(). \
                increment_none_labelled_vertex_count()
        return cell_label

    def get(self, parameter_name, gather=False):
        """ Get the values of a parameter for every local cell in the\
            population.
        """
        if isinstance(self._vertex, AbstractPopulationSettable):
            return self._vertex.get_value(parameter_name)
        raise KeyError("Population does not have a property {}".format(
            parameter_name))

    def _get_variable_unit(self, parameter_name):
        """ helper method for getting units from a parameter used by the vertex

        :param parameter_name: the parameter name to find the units for
        :return: the units in string form
        """
        if isinstance(self._vertex, AbstractContainsUnits):
            return self._vertex.units(parameter_name)

    @property
    def size(self):
        """ The number of neurons in the population
        :return:
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
