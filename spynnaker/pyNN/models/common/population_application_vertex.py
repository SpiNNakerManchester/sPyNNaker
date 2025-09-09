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
from typing import Collection, Container, Iterable, List, Optional, Tuple

from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.abstract_sized import Selector

from pacman.model.graphs.machine import MachineVertex
from pacman.model.graphs.common import Slice
from pacman.model.routing_info import RoutingInfo
from pacman.utilities.utility_calls import get_keys

from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.abstract_models import HasCustomAtomKeyMap
from spinn_front_end_common.interface.ds import DataType

from spynnaker.pyNN.models.abstract_models import ColouredApplicationVertex
from spynnaker.pyNN.models.common.parameter_holder import ParameterHolder
from spynnaker.pyNN.utilities.buffer_data_type import BufferDataType
from spynnaker.pyNN.models.current_sources import AbstractCurrentSource
from .types import Names, Values


# pylint: disable=abstract-method
class PopulationApplicationVertex(
        ColouredApplicationVertex, HasCustomAtomKeyMap):
    """
    A vertex that can be used in a Population.

    Provides some default functions that can be overridden if the vertex
    supports these.
    """

    # No data required here; makes it easy to mix in!
    __slots__ = ()

    @staticmethod
    def _as_list(names: Names) -> List[str]:
        """
        Normalise the input to a list.

        :param names: The item or items to normalise
        """
        if isinstance(names, str):
            return [names]
        return list(names)

    @staticmethod
    def _check_names(names: Names, allowed: Container[str],
                     type_of_thing: str) -> None:
        """
        Check the list of names are allowed or not.

        :param names: The names to check
        :param allowed: The set of allowed names
        :param type_of_thing: The "type of thing" to report in any error
        :raises KeyError: If one of the names is not allowed
        """
        for name in PopulationApplicationVertex._as_list(names):
            if name not in allowed:
                raise KeyError(f"{name} is not a recognized {type_of_thing}")

    @staticmethod
    def _check_parameters(names: Names, allowed: Container[str]) -> None:
        """
        Check that parameters are allowed.

        :param names: The names to check
        :param allowed: The set of allowed names
        """
        PopulationApplicationVertex._check_names(names, allowed, "parameter")

    @staticmethod
    def _check_variables(names: Names, allowed: Container[str]) -> None:
        """
        Check that state variables are allowed.

        :param names: The names to check
        :param allowed: The set of allowed names
        """
        PopulationApplicationVertex._check_names(names, allowed, "variable")

    def get_parameter_values(
            self, names: Names, selector: Selector = None) -> ParameterHolder:
        """
        :param names: The name or names of the parameter to get
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :returns: The values of a parameter or parameters for the whole
            Population or a subset if the selector is used.
        :raise KeyError: if the parameter is not something that can be read
        """
        raise KeyError(
            "This Population does not support the reading of parameters")

    def set_parameter_values(
            self, name: str, value: Values, selector: Selector = None) -> None:
        """
        Set the values of a parameter for the whole Population or a subset
        if the selector is used.

        :param name: The name of the parameter to set
        :param value: The new value
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :raise KeyError: if the parameter is not something that can be changed
        """
        raise KeyError(
            "This Population does not support the setting of parameters")

    def get_parameters(self) -> List[str]:
        """
        :returns: The names of all the parameters that can be obtained
        """
        return []

    def get_initial_state_values(
            self, names: Names, selector: Selector = None) -> ParameterHolder:
        """
        :param names: The name or names of the variable to get
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :returns: The initial values of a state variable
            for the whole Population
            or a subset if the selector is used.
        :raise KeyError: if the variable is not something that can be read
        """
        raise KeyError(
            "This Population does not support the reading of state"
            " variables")

    def set_initial_state_values(
            self, name: str, value: Values, selector: Selector = None) -> None:
        """
        Set the initial values of a state variable for the whole Population
        or a subset if the selector is used.

        :param name: The name of the variable to set
        :param value: The new value
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :raise KeyError: if the variable is not something that can be changed
        """
        raise KeyError(
            "This Population does not support the initialization of state"
            " variables")

    def get_current_state_values(
            self, names: Names, selector: Selector = None) -> ParameterHolder:
        """
        :param names: The name or names of the variable to get
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids
        :returns: The current values of a state variable for
            the whole Population or a subset if the selector is used.
        :raise KeyError: if the variable is not something that can be read
        """
        raise KeyError(
            "This Population does not support the reading of state"
            " variables")

    def set_current_state_values(
            self, name: str, value: Values, selector: Selector = None) -> None:
        """
        Set the current values of a state variable for the whole Population
        or a subset if the selector is used.

        :param name: The name of the variable to set
        :param value: The new value
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :raise KeyError: if the variable is not something that can be changed
        """
        raise KeyError(
            "This Population does not support the setting of state"
            " variables")

    def get_state_variables(self) -> List[str]:
        """
        :returns: A list of supported state variables.
        """
        return []

    def get_units(self, name: str) -> str:
        """
        Get the units of the given parameter or state variable.

        :param name: the name of the parameter to get the units of
        :returns: The unit or this variable. For example 'mV' or 'uS'.
           Will be an empty string for things like spikes and probability
        :raise KeyError:
            if the name isn't recognised or the units cannot be identified
        """
        raise KeyError(f"The units for {name} cannot be found")

    @property
    def conductance_based(self) -> bool:
        """
        Whether the vertex models post-synaptic inputs as
        currents or conductance.

        By default this is False; override if the model accepts
        conductance based input.
        """
        return False

    # recording methods
    # If get_recordable_variables implemented other recording methods must
    # be too

    def get_recordable_variables(self) -> List[str]:
        """
        Get a list of the names of things that can be recorded.

        This methods list the variable recorded via the Population.

        Includes both neuron and synapse recordable things

        :returns: List of variable names
        """
        return []

    def set_recording(
            self, name: str, sampling_interval: Optional[float] = None,
            indices: Optional[Collection[int]] = None) -> None:
        """
        Set a variable recording.

        :param name: The name of the variable to set the status of
        :param sampling_interval:
            How often the variable should be recorded or `None` for every
            time step, in milliseconds
        :param indices: The list of neuron indices to record or `None` for all
        :raises KeyError: if the variable cannot be recorded
        """
        _ = (name, sampling_interval, indices)
        if not self.get_recordable_variables():
            raise KeyError("This Population does not support recording")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"set_recording")

    def set_not_recording(self, name: str,
                          indices: Optional[Collection[int]] = None) -> None:
        """
        Set a variable not recording.

        :param name: The name of the variable to not record
        :param indices:
            The list of neuron indices to not record or `None` for all
        :raises KeyError: if the variable cannot be stopped from recording
        """
        _ = (name, indices)
        if not self.get_recordable_variables():
            raise KeyError("This Population does not support recording")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"set_not_recording")

    def get_recording_variables(self) -> List[str]:
        """
        :returns: A list of variables that are currently being recorded.
        """
        if not self.get_recordable_variables():
            return []
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_recording_variables")

    def get_buffer_data_type(self, name: str) -> BufferDataType:
        """
        Get the type of data recorded by the buffer manager.

        The buffer data type controls how data returned by the cores is
        handled in NeoBufferDatabase.

        :param name: The name of the variable recorded
        :raises KeyError: if the variable isn't being recorded
        :returns: Data type in the Buffer Database
        """
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_recording_variables")

    def get_sampling_interval_ms(self, name: str) -> float:
        """
        Get the sampling interval of the recording for the given variable.

        The values is in ms and unless selective recording is used will be
        `SpynnakerDataView.get_simulation_time_step_us()`

        :param name: The name of the variable
        :returns: Sampling rate in milliseconds for this variable
        :raises KeyError: If the variable isn't being recorded
        """
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_recording_variables")

    def get_data_type(self, name: str) -> Optional[DataType]:
        """
        Get the type data returned by a recording of the variable.

        This is the type of data the C code is returning.
        For instance data such as spikes this will be `None`.

        :param name: The name of the variable to get the type of
        :returns: The data type used by the C code
        :raise KeyError: If the variable isn't recordable
        """
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_data_type")

    def get_recording_region(self, name: str) -> int:
        """
        :param name: The name of the variable to get the region of
        :returns: The recording region for the named variable.
        :raises KeyError: If the variable isn't being recorded
        """
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_recording_region")

    def get_neurons_recording(
            self, name: str, vertex_slice: Slice) -> Optional[Collection[int]]:
        """
        Gets the neurons being recorded on the core with this slice.

        Typically `vertex_slice.get_raster_ids(atoms_shape)`
        but may be a sublist if doing selective recording.

        :param name: The name of the variable to get the region of
        :param vertex_slice:
        :return: A list of the global raster IDs of the atoms in recording
            named variable within this slice
        """
        _ = (name, vertex_slice)
        if name not in self.get_recordable_variables():
            raise KeyError(f"{name} is not being recorded")
        raise NotImplementedError(
            f"{type(self)} has recording variables so should implement "
            f"get_neurons_recording")

    # end of recording methods

    def inject(self, current_source: AbstractCurrentSource,
               selector: Selector = None) -> None:
        """
        Inject a current source into this population.

        :param current_source: the current source to be injected
        :param selector: a description of the subrange to accept, or ``None``
            for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :raises \
            ~spinn_front_end_common.utilities.exceptions.ConfigurationException:
            if the population doesn't support injection
        """
        raise ConfigurationException(
            "This Population doesn't support injection")

    @property
    @overrides(ColouredApplicationVertex.n_colour_bits)
    def n_colour_bits(self) -> int:
        return 0

    @overrides(HasCustomAtomKeyMap.get_atom_key_map)
    def get_atom_key_map(
            self, pre_vertex: MachineVertex, partition_id: str,
            routing_info: RoutingInfo) -> Iterable[Tuple[int, int]]:
        base_key = routing_info.get_key_from(
            pre_vertex, partition_id)
        vertex_slice = pre_vertex.vertex_slice
        keys = get_keys(base_key, vertex_slice, self.n_colour_bits)
        return zip(vertex_slice.get_raster_ids(), keys)
