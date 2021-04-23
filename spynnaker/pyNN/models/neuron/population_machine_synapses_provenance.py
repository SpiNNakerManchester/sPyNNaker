# Copyright (c) 2021 The University of Manchester
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

from spinn_utilities.abstract_base import abstractproperty
from spinn_front_end_common.utilities.utility_objs import ProvenanceDataItem
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)

get_placement_details = \
    ProvidesProvenanceDataFromMachineImpl._get_placement_details
add_name = ProvidesProvenanceDataFromMachineImpl._add_name


class SynapseProvenance(ctypes.LittleEndianStructure):
    """ Provenance items from synapse processing
    """
    _fields_ = [
        # A count of presynaptic events.
        ("n_pre_synaptic_events", ctypes.c_uint32),
        # A count of synaptic saturations.
        ("n_saturations", ctypes.c_uint32),
        # A count of the times that the synaptic input circular buffers
        # overflowed
        ("n_buffer_overflows", ctypes.c_uint32),
        # The number of STDP weight saturations.
        ("n_plastic_saturations", ctypes.c_uint32),
        # The number of searches of the population table that hit nothing
        ("n_ghost_searches", ctypes.c_uint32),
        # The number of bitfields that couldn't fit in DTCM
        ("n_failed_bitfield_reads", ctypes.c_uint32),
        # The number of DMA transfers done
        ("n_dmas_complete", ctypes.c_uint32),
        # The number of spikes successfully processed
        ("n_spikes_processed", ctypes.c_uint32),
        # The number of population table hits on INVALID entries
        ("n_invalid_pop_table_hits", ctypes.c_uint32),
        # The number of spikes that didn't transfer empty rows
        ("n_filtered_by_bitfield", ctypes.c_uint32),
        # The number of rewirings performed.
        ("n_rewires", ctypes.c_uint32),
        # The number of packets that were dropped due to being late
        ("n_late_packets", ctypes.c_uint32),
        # The maximum size of the spike input buffer during simulation
        ("max_size_input_buffer", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class PopulationMachineSynapsesProvenance(object):

    # This MUST stay empty to allow mixing with other things with slots
    __slots__ = []

    # x words needed for a bitfield covering 256 atoms
    WORDS_TO_COVER_256_ATOMS = 8

    SATURATION_COUNT_NAME = "Times_synaptic_weights_have_saturated"
    SATURATION_COUNT_MESSAGE = (
        "The weights from the synapses for {} on {}, {}, {} saturated "
        "{} times. If this causes issues you can increase the "
        "spikes_per_second and / or ring_buffer_sigma "
        "values located within the .spynnaker.cfg file.")

    INPUT_BUFFER_FULL_NAME = "Times_the_input_buffer_lost_packets"
    INPUT_BUFFER_FULL_MESSAGE = (
        "The input buffer for {} on {}, {}, {} lost packets on {} "
        "occasions. This is often a sign that the system is running "
        "too quickly for the number of neurons per core.  Please "
        "increase the timer_tic or time_scale_factor or decrease the "
        "number of neurons per core.")

    TOTAL_PRE_SYNAPTIC_EVENT_NAME = "Total_pre_synaptic_events"
    N_RE_WIRES_NAME = "Number_of_rewires"

    SATURATED_PLASTIC_WEIGHTS_NAME = (
        "Times_plastic_synaptic_weights_have_saturated")
    SATURATED_PLASTIC_WEIGHTS_MESSAGE = (
        "The weights from the plastic synapses for {} on {}, {}, {} "
        "saturated {} times. If this causes issue increase the "
        "spikes_per_second and / or ring_buffer_sigma values located "
        "within the .spynnaker.cfg file.")

    _N_LATE_SPIKES_NAME = "Number_of_late_spikes"
    _N_LATE_SPIKES_MESSAGE_DROP = (
        "{} packets from {} on {}, {}, {} were dropped from the input buffer, "
        "because they arrived too late to be processed in a given time step. "
        "Try increasing the time_scale_factor located within the "
        ".spynnaker.cfg file or in the pynn.setup() method.")
    _N_LATE_SPIKES_MESSAGE_NO_DROP = (
        "{} packets from {} on {}, {}, {} arrived too late to be processed in"
        " a given time step. "
        "Try increasing the time_scale_factor located within the "
        ".spynnaker.cfg file or in the pynn.setup() method.")

    _MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME = "Max_filled_size_input_buffer"

    # provenance data items
    BIT_FIELD_FILTERED_PACKETS = \
        "How many packets were filtered by the bitfield filterer."
    INVALID_MASTER_POP_HITS = "Invalid Master Pop hits"
    SPIKES_PROCESSED = "how many spikes were processed"
    DMA_COMPLETE = "DMA's that were completed"
    BIT_FIELDS_NOT_READ = "N bit fields not able to be read into DTCM"
    GHOST_SEARCHES = "Number of failed pop table searches"
    PLASTIC_WEIGHT_SATURATION = "Times_plastic_synaptic_weights_have_saturated"
    LAST_TIMER_TICK = "Last_timer_tic_the_core_ran_to"
    TOTAL_PRE_SYNAPTIC_EVENTS = "Total_pre_synaptic_events"
    LOST_INPUT_BUFFER_PACKETS = "Times_the_input_buffer_lost_packets"

    @abstractproperty
    def _app_vertex(self):
        """ The application vertex of the machine vertex.

        :note: This is likely to be available via the MachineVertex.

        :rtype: AbstractPopulationVertex
        """

    def _append_synapse_provenance(
            self, provenance_items, prov_list_from_machine, offset, placement):
        """ Extract and add synapse provenance to the list of provenance items

        :param
            list(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)\
            provenance_items: The items already read, to append to
        :param list(int) prov_list_from_machine:
            The values read from the machine to be decoded
        :param int offset: Where in the list from the machine to start reading
        :param ~pacman.model.placements.Placement placement:
            Which vertex are we retrieving from, and where was it
        :return: The number of items read from prov_list_from_machine
        :rtype: int
        """
        synapse_prov = SynapseProvenance(
            *prov_list_from_machine[offset:SynapseProvenance.N_ITEMS + offset])
        label, x, y, p, names = get_placement_details(placement)

        times_timer_tic_overran = 0
        for item in provenance_items:
            if (item.names[-1] ==
                    ProvidesProvenanceDataFromMachineImpl._TIMER_TICK_OVERRUN):
                times_timer_tic_overran = item.value

        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.SATURATION_COUNT_NAME),
            synapse_prov.n_saturations, report=synapse_prov.n_saturations > 0,
            message=self.SATURATION_COUNT_MESSAGE.format(
                label, x, y, p, synapse_prov.n_saturations)))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.INPUT_BUFFER_FULL_NAME),
            synapse_prov.n_buffer_overflows,
            report=synapse_prov.n_buffer_overflows > 0,
            message=self.INPUT_BUFFER_FULL_MESSAGE.format(
                label, x, y, p, synapse_prov.n_buffer_overflows)))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.TOTAL_PRE_SYNAPTIC_EVENT_NAME),
            synapse_prov.n_pre_synaptic_events))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.SATURATED_PLASTIC_WEIGHTS_NAME),
            synapse_prov.n_plastic_saturations,
            report=synapse_prov.n_plastic_saturations > 0,
            message=self.SATURATED_PLASTIC_WEIGHTS_MESSAGE.format(
                label, x, y, p, synapse_prov.n_plastic_saturations)))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.N_RE_WIRES_NAME),
            synapse_prov.n_rewires))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.GHOST_SEARCHES),
            synapse_prov.n_ghost_searches,
            report=synapse_prov.n_ghost_searches > 0,
            message=(
                "The number of failed population table searches for {} on {},"
                " {}, {} was {}. If this number is large relative to the "
                "predicted incoming spike rate, try increasing source and "
                "target neurons per core".format(
                    label, x, y, p, synapse_prov.n_ghost_searches))))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.BIT_FIELDS_NOT_READ),
            synapse_prov.n_failed_bitfield_reads, report=False,
            message=(
                "The filter for stopping redundant DMA's couldn't be fully "
                "filled in, it failed to read {} entries, which means it "
                "required a max of {} extra bytes of DTCM (assuming cores "
                "have at max 256 neurons. Try reducing neurons per core, or "
                "size of buffers, or neuron params per neuron etc.".format(
                    synapse_prov.n_failed_bitfield_reads,
                    synapse_prov.n_failed_bitfield_reads *
                    self.WORDS_TO_COVER_256_ATOMS))))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.DMA_COMPLETE),
            synapse_prov.n_dmas_complete))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.SPIKES_PROCESSED),
            synapse_prov.n_spikes_processed))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self.INVALID_MASTER_POP_HITS),
            synapse_prov.n_invalid_pop_table_hits,
            report=synapse_prov.n_invalid_pop_table_hits > 0,
            message=(
                "There were {} keys which were received by core {}:{}:{} which"
                " had no master pop entry for it. This is a error, which most "
                "likely strives from bad routing.".format(
                    synapse_prov.n_invalid_pop_table_hits, x, y, p))))
        provenance_items.append((ProvenanceDataItem(
            add_name(names, self.BIT_FIELD_FILTERED_PACKETS),
            synapse_prov.n_filtered_by_bitfield,
            report=(synapse_prov.n_filtered_by_bitfield > 0 and (
                        synapse_prov.n_buffer_overflows > 0 or
                        times_timer_tic_overran > 0)),
            message=(
                "There were {} packets received by {}:{}:{} that were "
                "filtered by the Bitfield filterer on the core. These packets "
                "were having to be stored and processed on core, which means "
                "the core may not be running as efficiently as it could. "
                "Please adjust the network or the mapping so that these "
                "packets are filtered in the router to improve "
                "performance.".format(
                    synapse_prov.n_filtered_by_bitfield, x, y, p)))))
        late_message = (
            self._N_LATE_SPIKES_MESSAGE_DROP
            if self._app_vertex.drop_late_spikes
            else self._N_LATE_SPIKES_MESSAGE_NO_DROP)
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self._N_LATE_SPIKES_NAME),
            synapse_prov.n_late_packets,
            report=synapse_prov.n_late_packets > 0,
            message=late_message.format(
                synapse_prov.n_late_packets, label, x, y, p)))
        provenance_items.append(ProvenanceDataItem(
            add_name(names, self._MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME),
            synapse_prov.max_size_input_buffer, report=False))

        return SynapseProvenance.N_ITEMS
