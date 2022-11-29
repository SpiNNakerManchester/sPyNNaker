# Copyright (c) 2020-2021 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from enum import Enum
from spinn_utilities.overrides import overrides
from spinn_utilities.helpful_functions import is_singleton
from pacman.model.graphs.application import ApplicationVertex
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.abstract_models import HasCustomAtomKeyMap
from pacman.utilities.utility_calls import get_field_based_keys


class RecordingType(Enum):
    """ The type of data being recorded
    """
    BIT_FIELD = 0
    MATRIX = 1
    EVENT = 2


class PopulationApplicationVertex(ApplicationVertex, HasCustomAtomKeyMap):
    """ A vertex that can be used in a Population.

        Provides some default functions that can be overridden if the vertex
        supports these.
    """

    # No data required here; makes it easy to mix in!
    __slots__ = []

    @staticmethod
    def _as_list(names):
        """ Normalise the input to a list

        :param names: The item or items to normalise
        :type names: str or list
        :rtype: list(str)
        """
        if is_singleton(names):
            return [names]
        return names

    @staticmethod
    def _check_names(names, allowed, type_of_thing):
        """ Check the list of names are allowed or not

        :param names: The names to check
        :type names: str or list
        :param set(str) allowed: The set of allowed names
        :param str type_of_thing: The "type of thing" to report in any error
        :raises KeyError: If one of the names is not allowed
        """
        for name in PopulationApplicationVertex._as_list(names):
            if name not in allowed:
                raise KeyError(f"{name} is not a recognized {type_of_thing}")

    @staticmethod
    def _check_parameters(names, allowed):
        """ Check that parameters are allowed

        :param names: The names to check
        :type names: str or list
        :param set(str) allowed: The set of allowed names
        """
        PopulationApplicationVertex._check_names(names, allowed, "parameter")

    @staticmethod
    def _check_variables(names, allowed):
        """ Check that state variables are allowed

        :param names: The names to check
        :type names: str or list
        :param set(str) allowed: The set of allowed names
        """
        PopulationApplicationVertex._check_names(names, allowed, "variable")

    def get_parameter_values(self, names, selector=None):
        """ Get the values of a parameter or parameters for the whole
            Population or a subset if the selector is used

        :param names: The name or names of the parameter to get
        :type names: str or list
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :rtype: ParameterHolder
        :raise KeyError: if the parameter is not something that can be read
        """
        raise KeyError(
            "This Population does not support the reading of parameters")

    def set_parameter_values(self, name, value, selector=None):
        """ Set the values of a parameter for the whole Population or a subset
            if the selector is used

        :param str name: The name of the parameter to set
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :raise KeyError: if the parameter is not something that can be changed
        """
        raise KeyError(
            "This Population does not support the setting of parameters")

    def get_parameters(self):
        """ Get the names of all the parameters that can be obtained

        :rtype: list(str)
        """
        return []

    def get_initial_state_values(self, names, selector=None):
        """ Get the initial values of a state variable for the whole Population
            or a subset if the selector is used

        :param names: The name or names of the variable to get
        :type name: str or list
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :rtype: ParameterHolder
        :raise KeyError: if the variable is not something that can be read
        """
        raise KeyError(
            "This Population does not support the reading of state"
            " variables")

    def set_initial_state_values(self, name, value, selector=None):
        """ Set the initial values of a state variable for the whole Population
            or a subset if the selector is used

        :param str name: The name of the variable to set
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :raise KeyError: if the variable is not something that can be changed
        """
        raise KeyError(
            "This Population does not support the initialization of state"
            " variables")

    def get_current_state_values(self, names, selector=None):
        """ Get the current values of a state variable for the whole Population
            or a subset if the selector is used

        :param names: The name or names of the variable to get
        :type name: str or list
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :rtype: ParameterHolder
        :raise KeyError: if the variable is not something that can be read
        """
        raise KeyError(
            "This Population does not support the reading of state"
            " variables")

    def set_current_state_values(self, name, value, selector=None):
        """ Set the current values of a state variable for the whole Population
            or a subset if the selector is used

        :param str name: The name of the variable to set
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :raise KeyError: if the variable is not something that can be changed
        """
        raise KeyError(
            "This Population does not support the setting of state"
            " variables")

    def get_state_variables(self):
        """ Get a list of supported state variables

        :rtype: list(str)
        """
        return []

    def get_units(self, name):
        """ Get the units of the given parameter or state variable

        :param str name: the name of the parameter to get the units of
        :rtype: str
        :raise KeyError:
            if the name isn't recognised or the units cannot be identified
        """
        raise KeyError(f"The units for {name} cannot be found")

    @property
    def conductance_based(self):
        """ Determine whether the vertex models post-synaptic inputs as
            currents or conductance.

            By default this returns False; override if the model accepts
            conductance based input.

        :rtype: bool.
        """
        return False

    def get_recordable_variables(self):
        """ Get a list of the names and types of things that can be recorded

        :rtype: list(str)
        """
        return []

    def can_record(self, name):
        """ Determine if the given variable can be recorded.

        :param str name: The name of the variable to test
        :rtype: bool
        """
        # pylint: disable=unused-argument
        return False

    def set_recording(self, name, sampling_interval=None, indices=None):
        """ Set a variable recording

        :param str name: The name of the variable to set the status of
        :param sampling_interval:
            How often the variable should be recorded or None for every
            time step, in milliseconds
        :type sampling_interval: float or None
        :param indices: The list of neuron indices to record or None for all
        :type indices: list(int) or None
        :raises KeyError: if the variable cannot be recorded
        """
        raise KeyError("This Population does not support recording")

    def set_not_recording(self, name, indices=None):
        """ Set a variable not recording

        :param str name: The name of the variable to not record
        :param indices:
            The list of neuron indices to not record or None for all
        :type indices: list(int) or None
        :raises KeyError: if the variable cannot be stopped from recording
        """
        raise KeyError(
            "This Population does not support the stopping of recording")

    def get_recording_variables(self):
        """ Get a list of variables that are currently being recorded

        :rtype: list(str)
        """
        return []

    def is_recording_variable(self, name):
        """ Indicate whether the given variable is being recorded

        :param str name: The name of the variable to check the status of
        :rtype: bool
        :raises KeyError: if the variable is not supported
        """
        raise KeyError("This Population does not support recording")

    def write_recording_metadata(self, first_id):
        """
        Writes the metatdata to get_recorded_data from NeoBufferedDatabase

        If the get_recorded_data method uses NeoBufferDatabase thios method
        must be implemented

        If the data comes from the BufferExtractor than it can be skipped

        :param int first_id: The ID of the first member of the population.
        """
        pass

    def get_recorded_data(self, name):
        """ Get the data recorded for a given variable

        :param str name: The name of the variable recorded
        :rtype: ndarray
        :raises KeyError: if the variable isn't being recorded
        """
        raise KeyError("This Population does not support recording")

    def get_recording_sampling_interval(self, name):
        """ Get the sampling interval of the recording for the given variable

        :rtype: float
        :raises KeyError: If the variable isn't being recorded
        """
        raise KeyError("This Population does not support recording")

    def get_recording_indices(self, name):
        """ Get the indices of the given variable that are being recorded

        :rtype: list(int)
        :raises KeyError: If the variable isn't being recorded
        """
        raise KeyError("This Population does not support recording")

    def get_recording_type(self, name):
        """ Get the type of recording of the variable

        :param str name: The name of the variable to get the type of
        :rtype: RecordingType
        :raise KeyError: If the variable isn't recordable
        """
        raise KeyError("This Population does not support recording")

    def clear_recording_data(self, name):
        """ Clear the data for the given recording

        :param str name: The name of the variable to clear the data from
        :raise KeyError: If the variable isn't recordable
        """
        raise KeyError("This Population does not support recording")

    def inject(self, current_source, selector=None):
        """ Inject a current source into this population

        :param ~pyNN.standardmodels.electrodes.StandardCurrentSource\
            current_source: the Current Source to be injected
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        :raise ConfigurationException:
            if the population doesn't support injection
        """
        raise ConfigurationException(
            "This Population doesn't support injection")

    @property
    def n_colour_bits(self):
        """ The number of colour bits sent by this vertex.

            Assumed 0 unless overridden

        :rtype: int
        """
        return 0

    @overrides(HasCustomAtomKeyMap.get_atom_key_map)
    def get_atom_key_map(self, pre_vertex, partition_id, routing_info):
        base_key = routing_info.get_first_key_from_pre_vertex(
            pre_vertex, partition_id)
        # This might happen if there are no edges
        if base_key is None:
            base_key = 0
        vertex_slice = pre_vertex.vertex_slice
        keys = get_field_based_keys(base_key, vertex_slice, self.n_colour_bits)
        return enumerate(keys, vertex_slice.lo_atom)
