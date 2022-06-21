# Copyright (c) 2017-2020The University of Manchester
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
import ctypes
from collections import namedtuple

from spinn_utilities.abstract_base import abstractproperty, abstractmethod
from spinn_utilities.overrides import overrides

from pacman.utilities.utility_calls import get_field_based_keys

from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spinn_front_end_common.utilities import helpful_functions
from spynnaker.pyNN.models.abstract_models import (
    AbstractReadParametersBeforeSet)
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.models.current_sources import CurrentSourceIDs
from spynnaker.pyNN.utilities.utility_calls import convert_to


class NeuronProvenance(ctypes.LittleEndianStructure):
    """ Provenance items from neuron processing
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


# Identifiers for neuron regions
NeuronRegions = namedtuple(
    "NeuronRegions",
    ["neuron_params", "current_source_params", "neuron_recording"])


class PopulationMachineNeurons(
        AbstractReadParametersBeforeSet, allow_derivation=True):
    """ Mix-in for machine vertices that have neurons in them
    """

    # This MUST stay empty to allow mixing with other things with slots
    __slots__ = []

    @abstractproperty
    def _app_vertex(self):
        """ The application vertex of the machine vertex.

        :note: This is likely to be available via the MachineVertex.

        :rtype: AbstractPopulationVertex
        """

    @abstractproperty
    def _vertex_slice(self):
        """ The slice of the application vertex atoms on this machine vertex.

        :note: This is likely to be available via the MachineVertex.

        :rtype: ~pacman.model.graphs.common.Slice
        """

    @abstractproperty
    def _slice_index(self):
        """ The index of the slice of this vertex in the list of slices

        :rtype: int
        """

    @abstractproperty
    def _key(self):
        """ The key for spikes.

        :rtype: int
        """

    @abstractmethod
    def _set_key(self, key):
        """ Set the key for spikes.

        :note: This is required because this class cannot have any storage.

        :param int key: The key to be set
        """

    @abstractproperty
    def _neuron_regions(self):
        """ The region identifiers for the neuron regions

        :rtype: .NeuronRegions
        """

    def _parse_neuron_provenance(
            self, label, x, y, p, provenance_data):
        """ Extract and yield neuron provenance

        :param str label: The label of the node
        :param int x: x coordinate of the chip where this core
        :param int y: y coordinate of the core where this core
        :param int p: virtual id of the core
        :param list(int) provenance_data: A list of data items to interpret
        :return: a list of provenance data items
        :rtype: iterator of ProvenanceDataItem
        """
        neuron_prov = NeuronProvenance(*provenance_data)
        self._app_vertex.get_tdma_provenance_item(
            x, y, p, label, neuron_prov.n_tdma_misses)
        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, "Last_timer_tic_the_core_ran_to",
                neuron_prov.current_timer_tick)
            db.insert_core(
                x, y, p, "Earliest_send_time", neuron_prov.earliest_send)
            db.insert_core(
                x, y, p, "Latest_Send_time", neuron_prov.latest_send)

    def _write_neuron_data_spec(self, spec, routing_info, ring_buffer_shifts):
        """ Write the data specification of the neuron data

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param ~pacman.model.routing_info.RoutingInfo routing_info:
            The routing information to read the key from
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        """
        # Get and store the key
        self._set_key(routing_info.get_first_key_from_pre_vertex(
            self, SPIKE_PARTITION_ID))

        # Write the neuron parameters
        self._write_neuron_parameters(spec, ring_buffer_shifts)

        # Write the current source parameters
        self._write_current_source_parameters(spec)

        # Write the neuron recording region
        neuron_recorder = self._app_vertex.neuron_recorder
        spec.reserve_memory_region(
            region=self._neuron_regions.neuron_recording,
            size=neuron_recorder.get_metadata_sdram_usage_in_bytes(
                self._vertex_slice),
            label="neuron recording")
        neuron_recorder.write_neuron_recording_region(
            spec, self._neuron_regions.neuron_recording, self._vertex_slice)

    def _write_neuron_parameters(self, spec, ring_buffer_shifts):
        """ Write the neuron parameters region

        :param ~data_specification.DataSpecificationGenerator spec:
            The data specification to write to
        :param list(int) ring_buffer_shifts:
            The shifts to apply to convert ring buffer values to S1615 values
        """
        self._app_vertex.set_has_run()

        # pylint: disable=too-many-arguments
        n_atoms = self._vertex_slice.n_atoms
        spec.comment("\nWriting Neuron Parameters for {} Neurons:\n".format(
            n_atoms))

        # Reserve and switch to the memory region
        params_size = self._app_vertex.get_sdram_usage_for_neuron_params(
            self._vertex_slice)
        spec.reserve_memory_region(
            region=self._neuron_regions.neuron_params, size=params_size,
            label='NeuronParams')
        spec.switch_write_focus(self._neuron_regions.neuron_params)

        # store the tdma data here for this slice.
        data = self._app_vertex.generate_tdma_data_specification_data(
            self._slice_index)
        spec.write_array(data)

        # Write whether the key is to be used, and then the key, or 0 if it
        # isn't to be used
        if self._key is None:
            spec.write_value(data=0)
            keys = [0] * n_atoms
        else:
            spec.write_value(data=1)
            keys = get_field_based_keys(self._key, self._vertex_slice)

        # Write the number of neurons in the block:
        spec.write_value(data=n_atoms)
        spec.write_value(data=2**get_n_bits(n_atoms))

        # Write the ring buffer data
        # This is only the synapse types that need a ring buffer i.e. not
        # those stored in synapse dynamics
        n_synapse_types = self._app_vertex.neuron_impl.get_n_synapse_types()
        spec.write_value(n_synapse_types)
        spec.write_array(ring_buffer_shifts)

        # Write the keys
        spec.write_array(keys)

        # Write the neuron parameters
        neuron_data = self._app_vertex.neuron_impl.get_data(
            self._app_vertex.parameters, self._app_vertex.state_variables,
            self._vertex_slice, self._app_vertex.atoms_shape)
        spec.write_array(neuron_data)

    def _write_current_source_parameters(self, spec):
        # pylint: disable=too-many-arguments
        n_atoms = self._vertex_slice.n_atoms
        lo_atom = self._vertex_slice.lo_atom
        hi_atom = self._vertex_slice.hi_atom

        spec.comment(
            "\nWriting Current Source Parameters for {} Neurons:\n".format(
                n_atoms))

        # Reserve and switch to the current source region
        params_size = self._app_vertex.\
            get_sdram_usage_for_current_source_params(self._vertex_slice)
        spec.reserve_memory_region(
            region=self._neuron_regions.current_source_params,
            size=params_size, label='CurrentSourceParams')
        spec.switch_write_focus(self._neuron_regions.current_source_params)

        # Get the current sources from the app vertex
        app_current_sources = self._app_vertex.current_sources
        current_source_id_list = self._app_vertex.current_source_id_list

        # Work out which current sources are on this core
        current_sources = set()
        for app_current_source in app_current_sources:
            for n in range(lo_atom, hi_atom + 1):
                if (n in current_source_id_list[app_current_source]):
                    current_sources.add(app_current_source)

        n_current_sources = len(current_sources)

        # Write the number of sources
        spec.write_value(n_current_sources)

        # Don't write anything else if there are no current sources
        if n_current_sources != 0:
            # Sort the current sources into current_source_id order
            current_sources = sorted(
                current_sources, key=lambda x: x.current_source_id)

            # Array to keep track of the number of each type of current source
            # (there are four, but they are numbered 1 to 4, so five elements)
            cs_index_array = [0, 0, 0, 0, 0]

            # Data sent to the machine will be current sources per neuron
            # This array will have the first entry indicating the number of
            # sources for each neuron, then if this is non-zero, follow it with
            # the IDs indicating the current source ID value, and then the
            # index within that type of current source
            neuron_current_sources = [[0] for n in range(lo_atom, hi_atom + 1)]
            for current_source in current_sources:
                # Get the ID of the current source
                cs_id = current_source.current_source_id

                # Only use IDs that are on this core
                for n in range(lo_atom, hi_atom + 1):
                    if (n in current_source_id_list[current_source]):
                        # I think this is now right, but test it more...
                        neuron_current_sources[n-lo_atom][0] += 1
                        neuron_current_sources[n-lo_atom].append(cs_id)
                        neuron_current_sources[n-lo_atom].append(
                            cs_index_array[cs_id])

                # Increase the ID value in case a (different) current source
                # of the same type is also used
                cs_index_array[cs_id] += 1

            # Now loop over the neurons on this core and write the current
            # source ID and index for sources attached to each neuron
            for n in range(0, hi_atom + 1 - lo_atom):
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
                cs_data_types = current_source.get_parameter_types
                cs_id = current_source.current_source_id
                for key, value in current_source.get_parameters.items():
                    # StepCurrentSource currently handled with arrays
                    if (cs_id == CurrentSourceIDs.STEP_CURRENT_SOURCE.value):
                        n_params = len(current_source.get_parameters[key])
                        spec.write_value(n_params)
                        for n_p in range(n_params):
                            value_convert = convert_to(
                                value[n_p], cs_data_types[key]).view("uint32")
                            spec.write_value(data=value_convert)
                    # All other sources have single-valued params
                    else:
                        if hasattr(value, "__getitem__"):
                            for m in range(len(value)):
                                value_convert = convert_to(
                                    value[m],
                                    cs_data_types[key]).view("uint32")
                                spec.write_value(data=value_convert)
                        else:
                            value_convert = convert_to(
                                value, cs_data_types[key]).view("uint32")
                            spec.write_value(data=value_convert)

    @overrides(AbstractReadParametersBeforeSet.read_parameters_from_machine)
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):

        # locate SDRAM address to where the neuron parameters are stored
        neuron_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement, self._neuron_regions.neuron_params,
                transceiver)

        # shift past the extra stuff before neuron parameters that we don't
        # need to read
        neurons_pre_size = self._app_vertex.get_neuron_params_position(
            self._vertex_slice)
        neuron_parameters_sdram_address = (
            neuron_region_sdram_address + neurons_pre_size)

        # get size of neuron params
        size_of_region = self._app_vertex.get_sdram_usage_for_neuron_params(
            vertex_slice) - neurons_pre_size

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y, neuron_parameters_sdram_address,
            size_of_region)

        # update python neuron parameters with the data
        self._app_vertex.neuron_impl.read_data(
            byte_array, 0, vertex_slice, self._app_vertex.parameters,
            self._app_vertex.state_variables)
