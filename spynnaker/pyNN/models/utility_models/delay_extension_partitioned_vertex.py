# pacman imports
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

# front end common imports
from spinn_front_end_common.interface.provenance\
    .provides_provenance_data_from_machine_impl \
    import ProvidesProvenanceDataFromMachineImpl
from spinn_front_end_common.utilities.utility_objs\
    .provenance_data_item import ProvenanceDataItem

# general imports
from enum import Enum


class DelayExtensionPartitionedVertex(
        PartitionedVertex, ProvidesProvenanceDataFromMachineImpl):

    _DELAY_EXTENSION_REGIONS = Enum(
        value="DELAY_EXTENSION_REGIONS",
        names=[('SYSTEM', 0),
               ('DELAY_PARAMS', 1),
               ('PROVENANCE_REGION', 2)])

    EXTRA_PROVENANCE_DATA_ENTRIES = Enum(
        value="EXTRA_PROVENANCE_DATA_ENTRIES",
        names=[("N_PACKETS_RECEIVED", 0),
               ("N_PACKETS_PROCESSED", 1),
               ("N_PACKETS_ADDED", 2),
               ("N_PACKETS_SENT", 3),
               ("N_BUFFER_OVERFLOWS", 4),
               ("N_DELAYS", 5)])

    def __init__(self, resources_required, label, constraints=None):
        PartitionedVertex.__init__(
            self, resources_required, label, constraints=constraints)
        ProvidesProvenanceDataFromMachineImpl.__init__(
            self, self._DELAY_EXTENSION_REGIONS.PROVENANCE_REGION.value, 6)

    def get_provenance_data_from_machine(self, transceiver, placement):
        provenance_data = self._read_provenance_data(transceiver, placement)
        provenance_items = self._read_basic_provenance_items(
            provenance_data, placement)
        provenance_data = self._get_remaining_provenance_data_items(
            provenance_data)

        n_packets_received = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_PACKETS_RECEIVED.value]
        n_packets_processed = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_PACKETS_PROCESSED.value]
        n_packets_added = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_PACKETS_ADDED.value]
        n_packets_sent = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_PACKETS_SENT.value]
        n_buffer_overflows = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_BUFFER_OVERFLOWS.value]
        n_delays = provenance_data[
            self.EXTRA_PROVENANCE_DATA_ENTRIES.N_DELAYS.value]

        label, x, y, p, names = self._get_placement_details(placement)

        # translate into provenance data items
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_packets_received"),
            n_packets_received))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_packets_processed"),
            n_packets_processed,
            report=n_packets_received != n_packets_processed,
            message=(
                "The delay extension {} on {}, {}, {} only processed {} of {}"
                " received packets.  This could indicate a fault.".format(
                    label, x, y, p, n_packets_processed, n_packets_received))))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_packets_added_to_delay_slot"),
            n_packets_added,
            report=n_packets_added != n_packets_processed,
            message=(
                "The delay extension {} on {}, {}, {} only added {} of {}"
                " processed packets.  This could indicate a routing or"
                " filtering fault".format(
                    label, x, y, p, n_packets_added, n_packets_processed))))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_packets_sent"),
            n_packets_sent))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Times_the_input_buffer_lost_packets"),
            n_buffer_overflows,
            report=n_buffer_overflows > 0,
            message=(
                "The input buffer for {} on {}, {}, {} lost packets on {} "
                "occasions. This is often a sign that the system is running "
                "too quickly for the number of neurons per core.  Please "
                "increase the timer_tic or time_scale_factor or decrease the "
                "number of neurons per core.".format(
                    label, x, y, p, n_buffer_overflows))))
        provenance_items.append(ProvenanceDataItem(
            self._add_name(names, "Number_of_times_delayed_to_spread_traffic"),
            n_delays))
        return provenance_items
