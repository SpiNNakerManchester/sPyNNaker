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
from spinn_utilities.abstract_base import abstractproperty
from spinn_front_end_common.interface.provenance import ProvenanceWriter


class SynapseProvenance(ctypes.LittleEndianStructure):
    """ Provenance items from synapse processing
    """
    _fields_ = [
        # A count of presynaptic events.
        ("n_pre_synaptic_events", ctypes.c_uint32),
        # A count of synaptic saturations.
        ("n_saturations", ctypes.c_uint32),
        # The number of STDP weight saturations.
        ("n_plastic_saturations", ctypes.c_uint32),
        # The number of searches of the population table that hit nothing
        ("n_ghost_searches", ctypes.c_uint32),
        # The number of bitfields that couldn't fit in DTCM
        ("n_failed_bitfield_reads", ctypes.c_uint32),
        # The number of population table hits on INVALID entries
        ("n_invalid_pop_table_hits", ctypes.c_uint32),
        # The number of spikes that didn't transfer empty rows
        ("n_filtered_by_bitfield", ctypes.c_uint32),
        # The number of synapses skipped due to late spikes
        ("n_skipped_synapses", ctypes.c_uint32),
        # The number of spikes detecte as late
        ("n_late_spikes", ctypes.c_uint32),
        # The maximum lateness of a spike
        ("max_late_spike", ctypes.c_uint32)
    ]

    N_ITEMS = len(_fields_)


class PopulationMachineSynapsesProvenance(object):
    """ Mix-in to add synapse provenance gathering without other synapse things
    """

    # This MUST stay empty to allow mixing with other things with slots
    __slots__ = []

    TOTAL_PRE_SYNAPTIC_EVENT_NAME = "Total_pre_synaptic_events"
    SATURATION_COUNT_NAME = "Times_synaptic_weights_have_saturated"
    SATURATED_PLASTIC_WEIGHTS_NAME = (
        "Times_plastic_synaptic_weights_have_saturated")
    GHOST_SEARCHES = "Number of failed pop table searches"
    BIT_FIELDS_NOT_READ = "N bit fields not able to be read into DTCM"
    INVALID_MASTER_POP_HITS = "Invalid Master Pop hits"
    BIT_FIELD_FILTERED_PACKETS = \
        "How many packets were filtered by the bitfield filterer."
    SYNAPSES_SKIPPED = "Skipped synapses"
    LATE_SPIKES = "Late spikes"
    MAX_LATE_SPIKE = "Max late spike"

    @abstractproperty
    def _app_vertex(self):
        """ The application vertex of the machine vertex.

        :note: This is likely to be available via the MachineVertex.

        :rtype: AbstractPopulationVertex
        """

    def _parse_synapse_provenance(self, label,  x, y, p, provenance_data):
        """ Extract and yield synapse provenance

        :param str label: The label of the node
        :param int x: x coordinate of the chip where this core
        :param int y: y coordinate of the core where this core
        :param int p: virtual id of the core
        :param list(int) provenance_data: A list of data items to interpret
        :return: a list of provenance data items
        :rtype: iterator of ProvenanceDataItem
        """
        synapse_prov = SynapseProvenance(*provenance_data)

        with ProvenanceWriter() as db:
            db.insert_core(
                x, y, p, self.TOTAL_PRE_SYNAPTIC_EVENT_NAME,
                synapse_prov.n_pre_synaptic_events)

            db.insert_core(
                x, y, p, self.SATURATION_COUNT_NAME,
                synapse_prov.n_saturations)
            if synapse_prov.n_saturations > 0:
                db.insert_report(
                    f"The weights from the synapses for {label} saturated "
                    f"{synapse_prov.n_saturations} times. ")

            db.insert_core(
                x, y, p, self.SATURATED_PLASTIC_WEIGHTS_NAME,
                synapse_prov.n_plastic_saturations)
            if synapse_prov.n_plastic_saturations > 0:
                db.insert_report(
                    f"The weights from the plastic synapses for {label} "
                    f"saturated {synapse_prov.n_plastic_saturations} times. ")

            db.insert_core(
                x, y, p, self.GHOST_SEARCHES, synapse_prov.n_ghost_searches)
            if synapse_prov.n_ghost_searches > 0:
                db.insert_report(
                    f"The number of failed population table searches for "
                    f"{label} was {synapse_prov.n_ghost_searches}. ")

            db.insert_core(
                x, y, p, self.BIT_FIELDS_NOT_READ,
                synapse_prov.n_failed_bitfield_reads)
            if synapse_prov.n_failed_bitfield_reads:
                db.insert_report(
                    f"On {label}, the filter for stopping redundant DMAs "
                    f"couldn't be fully filled in; it failed to read "
                    f"{synapse_prov.n_failed_bitfield_reads} entries. "
                    "Try reducing neurons per core.")

            db.insert_core(
                x, y, p, self.INVALID_MASTER_POP_HITS,
                synapse_prov.n_invalid_pop_table_hits)
            if synapse_prov.n_invalid_pop_table_hits > 0:
                db.insert_report(
                    f"On {label}, there were "
                    f"{synapse_prov.n_invalid_pop_table_hits} keys received "
                    f"that had no master pop entry for them.")

            db.insert_core(
                x, y, p, self.BIT_FIELD_FILTERED_PACKETS,
                synapse_prov.n_filtered_by_bitfield)

            db.insert_core(
                x, y, p, self.SYNAPSES_SKIPPED,
                synapse_prov.n_skipped_synapses)
            if synapse_prov.n_skipped_synapses > 0:
                db.insert_report(
                    f"On {label}, there were {synapse_prov.n_skipped_synapses}"
                    " that were skipped because a spike was received later"
                    " than the delay in the synapse")

            db.insert_core(
                x, y, p, self.LATE_SPIKES, synapse_prov.n_late_spikes)
            db.insert_core(
                x, y, p, self.MAX_LATE_SPIKE, synapse_prov.max_late_spike)
