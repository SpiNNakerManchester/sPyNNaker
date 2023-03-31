# Copyright (c) 2020 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from spinn_utilities.overrides import overrides
from spinn_utilities.helpful_functions import is_singleton
from pacman.model.graphs.application import ApplicationVertex
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.abstract_models import HasCustomAtomKeyMap
from pacman.utilities.utility_calls import get_field_based_keys


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

    # recording methods
    # If get_recordable_variables implemented other recording methods must
    # be too

    def get_recordable_variables(self):
        """ Get a list of the names and types of things that can be recorded

        This methods list the variable recorded via the Population

        :rtype: list(str)
        """
        return []

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
        # pylint: disable=unused-argument
        if self.get_recordable_variables() == []:
            raise KeyError("This Population does not support recording")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"set_recording")

    def set_not_recording(self, name, indices=None):
        """ Set a variable not recording

        :param str name: The name of the variable to not record
        :param indices:
            The list of neuron indices to not record or None for all
        :type indices: list(int) or None
        :raises KeyError: if the variable cannot be stopped from recording
        """
        # pylint: disable=unused-argument
        if self.get_recordable_variables() == []:
            raise KeyError("This Population does not support recording")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"set_not_recording")

    def get_recording_variables(self):
        """ Get a list of variables that are currently being recorded

        :rtype: list(str)
        """
        if self.get_recordable_variables() == []:
            return []
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_recording_variables")

    def get_buffer_data_type(self, name):
        """ Get the type of data recorded by the buffer manager

        The BufferDatabase value controls how data returned by the cores is
        handled in NeoBufferDatabase

        :param str name: The name of the variable recorded
        :rtype: ~spynnaker.pyNN.utilities.neo_buffer_database.BufferDatabase
        :raises KeyError: if the variable isn't being recorded
        """
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_recording_variables")

    def get_sampling_interval_ms(self, name):
        """ Get the sampling interval of the recording for the given variable

        The values is in ms and unless selective recording is used will be
        SpynnakerDataView.get_simulation_time_step_us()

        :rtype: float
        :raises KeyError: If the variable isn't being recorded
        """
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_recording_variables")

    def get_data_type(self, name):
        """ Get the type data returned by a recording of the variable

        This is the type of data the C code is returning.
        For instance dta such as spikes this will be None

        :param str name: The name of the variable to get the type of
        :rtype: ~data_specification.enums.DataType or None
        :raise KeyError: If the variable isn't recordable
        """
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_data_type")

    def get_recording_region(self, name):
        """
        Gets the recording region for the named variable

        :param str name: The name of the variable to get the region of
        :rtype: int
        :raises KeyError: If the variable isn't being recorded
        """
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_recording_region")

    def get_neurons_recording(self, name, vertex_slice):
        """
        Gets the neurons being recorded on the core with this slice

        Typically vertex_slice.get_raster_ids(atoms_shape)
        But may be a sublist if doing selective recording

        :param str name: The name of the variable to get the region of
        :param vertex_slice:
        :return: A list of the global raster IDs of the atoms in recording
            named variable within this slice
        """
        # pylint: disable=unused-argument
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_neurons_recording")

    # end of recording methods

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
        ids = vertex_slice.get_raster_ids(pre_vertex.app_vertex.atoms_shape)
        return zip(ids, keys)
