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

    SATURATION_COUNT_NAME = "Times_synaptic_weights_have_saturated"
    INPUT_BUFFER_FULL_NAME = "Times_the_input_buffer_lost_packets"
    TOTAL_PRE_SYNAPTIC_EVENT_NAME = "Total_pre_synaptic_events"
    N_RE_WIRES_NAME = "Number_of_rewires"
    SATURATED_PLASTIC_WEIGHTS_NAME = (
        "Times_plastic_synaptic_weights_have_saturated")
    _N_LATE_SPIKES_NAME = "Number_of_late_spikes"
    _MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME = "Max_filled_size_input_buffer"
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

    def _parse_synapse_provenance(self, label, names, provenance_data):
        """ Extract and yield synapse provenance

        :param str label: The label of the node
        :param list(str) names: The hierarchy of names for the provenance data
        :param list(int) provenance_data: A list of data items to interpret
        :return: a list of provenance data items
        :rtype: iterator of ProvenanceDataItem
        """
        synapse_prov = SynapseProvenance(*provenance_data)

        yield ProvenanceDataItem(
            names + [self.SATURATION_COUNT_NAME],
            synapse_prov.n_saturations, synapse_prov.n_saturations > 0,
            f"The weights from the synapses for {label} saturated "
            f"{synapse_prov.n_saturations} times. If this causes issues you "
            "can increase the spikes_per_second and / or ring_buffer_sigma "
            "values located within the .spynnaker.cfg file.")
        yield ProvenanceDataItem(
            names + [self.INPUT_BUFFER_FULL_NAME],
            synapse_prov.n_buffer_overflows,
            synapse_prov.n_buffer_overflows > 0,
            f"The input buffer for {label} lost packets on "
            f"{synapse_prov.n_buffer_overflows} occasions. This is often a "
            "sign that the system is running too quickly for the number of "
            "neurons per core.  Please increase the timer_tic or"
            " time_scale_factor or decrease the number of neurons per core.")
        yield ProvenanceDataItem(
            names + [self.TOTAL_PRE_SYNAPTIC_EVENT_NAME],
            synapse_prov.n_pre_synaptic_events)
        yield ProvenanceDataItem(
            names + [self.SATURATED_PLASTIC_WEIGHTS_NAME],
            synapse_prov.n_plastic_saturations,
            synapse_prov.n_plastic_saturations > 0,
            f"The weights from the plastic synapses for {label} saturated "
            f"{synapse_prov.n_plastic_saturations} times. If this causes "
            "issues increase the spikes_per_second and / or ring_buffer_sigma"
            " values located within the .spynnaker.cfg file.")
        yield ProvenanceDataItem(
            names + [self.N_RE_WIRES_NAME], synapse_prov.n_rewires)
        yield ProvenanceDataItem(
            names + [self.GHOST_SEARCHES], synapse_prov.n_ghost_searches,
            synapse_prov.n_ghost_searches > 0,
            f"The number of failed population table searches for {label} was "
            f"{synapse_prov.n_ghost_searches}. If this number is large "
            "relative to the  predicted incoming spike rate, try increasing "
            " source and target neurons per core")
        yield ProvenanceDataItem(
            names + [self.BIT_FIELDS_NOT_READ],
            synapse_prov.n_failed_bitfield_reads, False,
            f"On {label}, the filter for stopping redundant DMAs couldn't be "
            f"fully filled in; it failed to read "
            f"{synapse_prov.n_failed_bitfield_reads} entries. "
            "Try reducing neurons per core.")
        yield ProvenanceDataItem(
            names + [self.DMA_COMPLETE], synapse_prov.n_dmas_complete)
        yield ProvenanceDataItem(
            names + [self.SPIKES_PROCESSED],
            synapse_prov.n_spikes_processed)
        yield ProvenanceDataItem(
            names + [self.INVALID_MASTER_POP_HITS],
            synapse_prov.n_invalid_pop_table_hits,
            synapse_prov.n_invalid_pop_table_hits > 0,
            f"On {label}, there were {synapse_prov.n_invalid_pop_table_hits} "
            "keys received that had no master pop entry for them. This is an "
            "error, which most likely stems from bad routing.")
        yield ProvenanceDataItem(
            names + [self.BIT_FIELD_FILTERED_PACKETS],
            synapse_prov.n_filtered_by_bitfield)

        late_message = (
            f"On {label}, {synapse_prov.n_late_packets} packets were dropped "
            "from the input buffer, because they arrived too late to be "
            "processed in a given time step. Try increasing the "
            "time_scale_factor located within the .spynnaker.cfg file or in "
            "the pynn.setup() method."
            if self._app_vertex.drop_late_spikes else
            f"On {label}, {synapse_prov.n_late_packets} packets arrived too "
            "late to be processed in a given time step. Try increasing the "
            "time_scale_factor located within the .spynnaker.cfg file or in "
            "the pynn.setup() method.")
        yield ProvenanceDataItem(
            names + [self._N_LATE_SPIKES_NAME], synapse_prov.n_late_packets,
            synapse_prov.n_late_packets > 0, late_message)

        yield ProvenanceDataItem(
            names + [self._MAX_FILLED_SIZE_OF_INPUT_BUFFER_NAME],
            synapse_prov.max_size_input_buffer, report=False)
