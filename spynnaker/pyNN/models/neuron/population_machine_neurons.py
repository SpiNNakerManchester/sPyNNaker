# Copyright (c) 2017 The University of Manchester
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
from __future__ import annotations
from collections.abc import Container
import ctypes
import numpy
from typing import List, NamedTuple, Sequence, Set, Union, cast, TYPE_CHECKING

from spinn_utilities.abstract_base import abstractmethod
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.abstract_sized import Selector

from pacman.model.graphs import AbstractVertex
from pacman.model.graphs.common import Slice
from pacman.model.placements import Placement
from pacman.utilities.utility_calls import get_keys

from spinn_front_end_common.interface.ds import (
    DataSpecificationBase, DataSpecificationGenerator,
    DataSpecificationReloader)
from spinn_front_end_common.interface.provenance import ProvenanceWriter

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.models.abstract_models import AbstractNeuronExpandable
from spynnaker.pyNN.models.current_sources import CurrentSourceIDs
from spynnaker.pyNN.utilities.utility_calls import convert_to
if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
    from spynnaker.pyNN.models.neuron.neuron_data import NeuronData
    from spynnaker.pyNN.models.current_sources import AbstractCurrentSource


class NeuronProvenance(ctypes.LittleEndianStructure):
    """
    Provenance items from neuron processing.
    """
    _fields_ = [
        # The timer tick at the end of simulation
        ("current_timer_tick", ctypes.c_uint32),
        # The number of misses of TDMA time slots
        ("n_tdma_misses", ctypes.c_uint32),
        # The earliest send time within any time step
        ("earliest_send", ctypes.c_uint32),
        # The latest send time within any time step
        ("latest_send", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class NeuronRegions(NamedTuple):
    """
    Identifiers for neuron regions.
    """
    core_params: int
    neuron_params: int
    current_source_params: int
    neuron_recording: int
    neuron_builder: int
    initial_values: int


class PopulationMachineNeurons(
        AbstractNeuronExpandable, allow_derivation=True):
    """
    Mix-in for machine vertices that have neurons in them.
    """

    # This MUST stay empty to allow mixing with other things with slots
    __slots__ = ()

    @property
    @abstractmethod
    def _pop_vertex(self) -> AbstractPopulationVertex:
        """
        The application vertex of the machine vertex.

        .. note::
            This is likely to be available via the MachineVertex.

        :rtype: AbstractPopulationVertex
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _vertex_slice(self) -> Slice:
        """
        The slice of the application vertex atoms on this machine vertex.

        .. note::
            This is likely to be available via the MachineVertex.

        :rtype: ~pacman.model.graphs.common.Slice
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _slice_index(self) -> int:
        """
        The index of the slice of this vertex in the list of slices.

        :rtype: int
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _key(self) -> int:
        """
        The key for spikes.

        :rtype: int
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _has_key(self) -> bool:
        """
        Whether a key has been defined.
        """
        raise NotImplementedError

    @abstractmethod
    def _set_key(self, key: int):
        """
        Set the key for spikes.

        .. note::
            This is required because this class cannot have any storage.

        :param int key: The key to be set
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _neuron_regions(self) -> NeuronRegions:
        """
        The region identifiers for the neuron regions.

        :rtype: .NeuronRegions
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _neuron_data(self) -> NeuronData:
        """
        The neuron data handler.

        :rtype: NeuronData
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _max_atoms_per_core(self) -> int:
        """
        The maximum number of atoms on a core, used for neuron data transfer.

        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def set_do_neuron_regeneration(self) -> None:
        """
        Indicate that data re-generation of neuron parameters is required.
        """
        raise NotImplementedError

    def _parse_neuron_provenance(
            self, x: int, y: int, p: int, provenance_data: Sequence[int]):
        """
        Extract and yield neuron provenance.

        :param int x: x coordinate of the chip where this core
        :param int y: y coordinate of the core where this core
        :param int p: virtual id of the core
        :param list(int) provenance_data: A list of data items to interpret
        """
        neuron_prov = NeuronProvenance(*provenance_data)
        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, "Last_timer_tic_the_core_ran_to",
                neuron_prov.current_timer_tick)
            db.insert_core(
                x, y, p, "Earliest_send_time", neuron_prov.earliest_send)
            db.insert_core(
                x, y, p, "Latest_Send_time", neuron_prov.latest_send)

    def _write_neuron_data_spec(
            self, spec: DataSpecificationGenerator,
            ring_buffer_shifts: Sequence[int]):
        """
        Write the data specification of the neuron data.

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        """
        # Get and store the key
        routing_info = SpynnakerDataView.get_routing_infos()
        key = routing_info.get_first_key_from_pre_vertex(
            cast(AbstractVertex, self), SPIKE_PARTITION_ID)
        if key is not None:
            self._set_key(key)

        # Write the neuron core parameters
        self._write_neuron_core_parameters(spec, ring_buffer_shifts)

        # Write the current source parameters
        self._write_current_source_parameters(spec)

        # Write the other parameters
        self._neuron_data.write_data(
            spec, self._vertex_slice, self._neuron_regions)

    def _rewrite_neuron_data_spec(self, spec: DataSpecificationReloader):
        """
        Re-Write the data specification of the neuron data.

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        """
        # Write the current source parameters
        self._write_current_source_parameters(spec)

        # Write the other parameters after forcing a regeneration
        self._neuron_data.write_data(
            spec, self._vertex_slice, self._neuron_regions, False)

    def _write_neuron_core_parameters(
            self, spec: DataSpecificationGenerator,
            ring_buffer_shifts: Sequence[int]):
        """
        Write the neuron parameters region.

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        """
        n_atoms = self._vertex_slice.n_atoms
        spec.comment(f"\nWriting Neuron Parameters for {n_atoms} Neurons:\n")

        # Reserve and switch to the memory region
        params_size = self._pop_vertex.get_sdram_usage_for_core_neuron_params(
            n_atoms)
        spec.reserve_memory_region(
            region=self._neuron_regions.core_params, size=params_size,
            label='Neuron Core Params')
        spec.switch_write_focus(self._neuron_regions.core_params)

        # Write whether the key is to be used, and then the key, or 0 if it
        # isn't to be used
        keys: Union[numpy.ndarray, List[int]]
        if not self._has_key:
            spec.write_value(data=0)
            keys = [0] * n_atoms
        else:
            spec.write_value(data=1)
            keys = get_keys(
                self._key, self._vertex_slice, self._pop_vertex.n_colour_bits)

        # Write the number of neurons in the block:
        spec.write_value(data=n_atoms)

        # Write the maximum number of neurons based on the max atoms per core
        spec.write_value(data=2**get_n_bits(self._max_atoms_per_core))

        # Write the number of colour bits
        spec.write_value(self._pop_vertex.n_colour_bits)

        # Write the ring buffer data
        # This is only the synapse types that need a ring buffer i.e. not
        # those stored in synapse dynamics
        n_synapse_types = self._pop_vertex.neuron_impl.get_n_synapse_types()
        spec.write_value(n_synapse_types)
        spec.write_array(ring_buffer_shifts)

        # Write the keys
        spec.write_array(keys)

    def __in_selector(self, n: int, selector: Selector) -> bool:
        if isinstance(selector, Container):
            return n in selector
        return n == selector

    def _write_current_source_parameters(
            self, spec: DataSpecificationBase):
        n_atoms = self._vertex_slice.n_atoms

        spec.comment(
            f"\nWriting Current Source Parameters for {n_atoms} Neurons:\n")

        # Reserve and switch to the current source region
        params_size = self._pop_vertex.\
            get_sdram_usage_for_current_source_params(n_atoms)
        spec.reserve_memory_region(
            region=self._neuron_regions.current_source_params,
            size=params_size, label='CurrentSourceParams')
        spec.switch_write_focus(self._neuron_regions.current_source_params)

        # Get the current sources from the app vertex
        current_source_id_list = self._pop_vertex.current_source_id_list

        # Work out which current sources are on this core
        current_sources = self.__get_current_sources_sorted()

        # Write the number of sources
        spec.write_value(len(current_sources))

        # Don't write anything else if there are no current sources
        if current_sources:
            # Array to keep track of the number of each type of current source
            # (there are four, but they are numbered 1 to 4, so five elements)
            cs_index_array = [0, 0, 0, 0, 0]

            # Data sent to the machine will be current sources per neuron
            # This array will have the first entry indicating the number of
            # sources for each neuron, then if this is non-zero, follow it with
            # the IDs indicating the current source ID value, and then the
            # index within that type of current source
            neuron_current_sources = [[0] for n in range(n_atoms)]
            for current_source in current_sources:
                # Get the ID of the current source
                cs_id = current_source.current_source_id

                # Only use IDs that are on this core
                for i, n in enumerate(self._vertex_slice.get_raster_ids()):
                    if self.__in_selector(
                            n, current_source_id_list[current_source]):
                        # I think this is now right, but test it more...
                        neuron_current_sources[i][0] += 1
                        neuron_current_sources[i].append(cs_id)
                        neuron_current_sources[i].append(
                            cs_index_array[cs_id])

                # Increase the ID value in case a (different) current source
                # of the same type is also used
                cs_index_array[cs_id] += 1

            # Now loop over the neurons on this core and write the current
            # source ID and index for sources attached to each neuron
            for n in range(n_atoms):
                n_current_sources = neuron_current_sources[n][0]
                spec.write_value(n_current_sources)
                if n_current_sources != 0:
                    for csid in range(n_current_sources * 2):
                        spec.write_value(neuron_current_sources[n][csid+1])

            # Write the number of each type of current source
            for n in range(1, len(cs_index_array)):
                spec.write_value(cs_index_array[n])

            # Now loop over the current sources and write the data required
            # for each type of current source
            for current_source in current_sources:
                cs_data_types = current_source.parameter_types
                cs_id = current_source.current_source_id
                for key, value in current_source.parameters.items():
                    # StepCurrentSource currently handled with arrays
                    if cs_id == CurrentSourceIDs.STEP_CURRENT_SOURCE.value:
                        assert isinstance(value, Sequence)
                        n_params = len(value)
                        spec.write_value(n_params)
                        for n_p in range(n_params):
                            value_convert = convert_to(
                                value[n_p], cs_data_types[key]).view("uint32")
                            spec.write_value(data=value_convert)
                    # All other sources have single-valued params
                    else:
                        if isinstance(value, Sequence):
                            for m in range(len(value)):
                                value_convert = convert_to(
                                    value[m],
                                    cs_data_types[key]).item()
                                spec.write_value(data=value_convert)
                        else:
                            value_convert = convert_to(
                                value, cs_data_types[key]).item()
                            spec.write_value(data=value_convert)

    def __get_current_sources_sorted(self) -> List[AbstractCurrentSource]:
        app_current_sources = self._pop_vertex.current_sources
        current_source_id_list = self._pop_vertex.current_source_id_list

        current_sources: Set[AbstractCurrentSource] = set()
        for app_current_source in app_current_sources:
            for n in self._vertex_slice.get_raster_ids():
                if self.__in_selector(
                        n, current_source_id_list[app_current_source]):
                    current_sources.add(app_current_source)

        # Sort the current sources into current_source_id order
        return sorted(
            current_sources, key=lambda x: x.current_source_id)

    def read_parameters_from_machine(self, placement: Placement):
        """
        Read the parameters and state of the neurons from the machine
        at the current time.

        :param ~pacman.model.placements.Placement placement:
            Where to read the data from
        """
        self._neuron_data.read_data(placement, self._neuron_regions)

    def read_initial_parameters_from_machine(self, placement: Placement):
        """
        Read the parameters and state of the neurons from the machine
        as they were at the last time 0.

        :param ~pacman.model.placements.Placement placement:
            Where to read the data from
        """
        self._neuron_data.read_initial_data(placement, self._neuron_regions)

    @overrides(AbstractNeuronExpandable.gen_neurons_on_machine)
    def gen_neurons_on_machine(self) -> bool:
        return self._neuron_data.gen_on_machine

    @property
    @overrides(AbstractNeuronExpandable.neuron_generator_region)
    def neuron_generator_region(self) -> int:
        return self._neuron_regions.neuron_builder

    @overrides(AbstractNeuronExpandable.read_generated_initial_values)
    def read_generated_initial_values(self, placement: Placement):
        # Only do this if we actually need the data now i.e. if someone has
        # requested that the data be read before calling run
        if self._pop_vertex.read_initial_values:
            # If we do decide to read now, we can also copy the initial values
            self._neuron_data.read_data(placement, self._neuron_regions)
            self._pop_vertex.copy_initial_state_variables(self._vertex_slice)
