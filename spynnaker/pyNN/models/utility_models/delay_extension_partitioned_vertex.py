# data spec imports
from data_specification.data_specification_generator import \
    DataSpecificationGenerator

# pacman imports
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

# front end common imports
from spinn_front_end_common.interface.provenance\
    .provides_provenance_data_from_machine_impl \
    import ProvidesProvenanceDataFromMachineImpl
from spinn_front_end_common.utilities.utility_objs\
    .provenance_data_item import ProvenanceDataItem
from spinn_front_end_common.utilities import constants as common_constants

# general imports
from enum import Enum
import math
import random

_DELAY_PARAM_HEADER_WORDS = 7
DEFAULT_MALLOCS_USED = 2

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

    def generate_data_spec(
            self, subvertex, placement, partitioned_graph, routing_info,
            hostname, graph_mapper, report_folder, write_text_specs,
            application_run_time_folder, n_subvertices):

        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder,
                write_text_specs, application_run_time_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        n_words_per_stage = int(math.ceil(vertex_slice.n_atoms / 32.0))
        delay_params_sz = 4 * (_DELAY_PARAM_HEADER_WORDS +
                               (self._n_delay_stages * n_words_per_stage))

        spec.reserve_memory_region(
            region=(
                DelayExtensionPartitionedVertex.
                _DELAY_EXTENSION_REGIONS.SYSTEM.value),
            size=common_constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4,
            label='setup')

        spec.reserve_memory_region(
            region=(
                DelayExtensionPartitionedVertex.
                _DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value),
            size=delay_params_sz, label='delay_params')

        subvertex.reserve_provenance_data_region(spec)

        self.write_setup_info(spec)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = None
        partitions = partitioned_graph.\
            outgoing_edges_partitions_from_vertex(subvertex)
        for partition in partitions.values():
            keys_and_masks = \
                routing_info.get_keys_and_masks_from_partition(partition)

            # NOTE: using the first key assigned as the key.  Should in future
            # get the list of keys and use one per neuron, to allow arbitrary
            # key and mask assignments
            key = keys_and_masks[0].key

        incoming_key = None
        incoming_mask = None
        incoming_edges = partitioned_graph.incoming_subedges_from_subvertex(
            subvertex)

        for incoming_edge in incoming_edges:
            incoming_slice = graph_mapper.get_subvertex_slice(
                incoming_edge.pre_subvertex)
            if (incoming_slice.lo_atom == vertex_slice.lo_atom and
                    incoming_slice.hi_atom == vertex_slice.hi_atom):
                partition = partitioned_graph.get_partition_of_subedge(
                    incoming_edge)
                keys_and_masks = \
                    routing_info.get_keys_and_masks_from_partition(partition)
                incoming_key = keys_and_masks[0].key
                incoming_mask = keys_and_masks[0].mask

        self.write_delay_parameters(
            spec, vertex_slice, key, incoming_key, incoming_mask,
            n_subvertices)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

        return data_writer.filename

    def write_setup_info(self, spec):

        # Write this to the system region (to be picked up by the simulation):
        self._write_basic_setup_info(
            spec,
            (DelayExtensionPartitionedVertex.
                _DELAY_EXTENSION_REGIONS.SYSTEM.value))

    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask,
            n_subvertices):
        """ Generate Delay Parameter data
        """

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(
            region=(
                DelayExtensionPartitionedVertex.
                _DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value))

        # Write header info to the memory region:
        # Write Key info for this core and the incoming key and mask:
        spec.write_value(data=key)
        spec.write_value(data=incoming_key)
        spec.write_value(data=incoming_mask)

        # Write the number of neurons in the block:
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=self._n_delay_stages)

        # Write the random back off value
        spec.write_value(random.randint(0, n_subvertices))

        # Write the time between spikes
        spikes_per_timestep = self._n_delay_stages * vertex_slice.n_atoms
        time_between_spikes = (
            (self._machine_time_step * self._timescale_factor) /
            (spikes_per_timestep * 2.0))
        spec.write_value(data=int(time_between_spikes))

        # Write the actual delay blocks
        spec.write_array(array_values=self._delay_blocks[(
            vertex_slice.lo_atom, vertex_slice.hi_atom)].delay_block)

