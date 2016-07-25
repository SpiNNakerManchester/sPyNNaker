
# spynnaker imports
from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.neuron.master_pop_table_generators\
    .abstract_master_pop_table_factory import AbstractMasterPopTableFactory
import struct
from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge

from pacman.model.partitionable_graph.abstract_partitionable_vertex\
    import AbstractPartitionableVertex

# general imports
import logging
import numpy
import sys
import math

logger = logging.getLogger(__name__)


class _MasterPopEntry(object):
    """ internal class that contains a master pop entry
    """

    MASTER_POP_ENTRY_SIZE_BYTES = 12
    MASTER_POP_ENTRY_SIZE_WORDS = 3
    ADDRESS_LIST_ENTRY_SIZE_BYTES = 4
    ADDRESS_LIST_ENTRY_SIZE_WORDS = 1

    def __init__(self, routing_key, mask):
        self._routing_key = routing_key
        self._mask = mask
        self._addresses_and_row_lengths = list()

    def append(self, address, row_length, is_single):
        self._addresses_and_row_lengths.append(
            (address, row_length, is_single))

    @property
    def routing_key(self):
        """
        :return: the key combo of this entry
        """
        return self._routing_key

    @property
    def mask(self):
        """
        :return: the mask of the key for this master pop entry
        """
        return self._mask

    @property
    def addresses_and_row_lengths(self):
        """
        :return: the memory address that this master pop entry points at
        (synaptic matrix)
        """
        return self._addresses_and_row_lengths


class MasterPopTableAsBinarySearch(AbstractMasterPopTableFactory):
    """
    binary search master pop class.
    """

    # Switched ordering of count and start as numpy will switch them back
    # when asked for view("<4")
    MASTER_POP_ENTRY_DTYPE = [
        ("key", "<u4"), ("mask", "<u4"), ("start", "<u2"), ("count", "<u2")]

    ADDRESS_LIST_DTYPE = "<u4"

    SINGLE_BIT_FLAG_BIT = 0x80000000 # top bit of the 32 bit number
    ROW_LENGTH_MASK = 0xFF
    ADDRESS_MASK = 0x7FFFFF00

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)
        self._entries = None
        self._n_addresses = 0

    def get_master_population_table_size(self, vertex_slice, in_edges):
        """

        :param vertex_slice:the slice of the partitionable vertex that the\
                partitioned vertex will be holding
        :param in_edges: the in coming edges for the partitioned vertex this\
                master pop is associated with.
        :return: the size the master pop table will take in SDRAM (in bytes)
        """

        # Entry for each sub-edge - but don't know the subedges yet, so
        # assume multiple entries for each edge
        n_subvertices = 0
        n_entries = 0
        for in_edge in in_edges:

            if isinstance(in_edge, ProjectionPartitionableEdge):

                # TODO: Fix this to be more accurate!
                # May require modification to the master population table
                # Get the number of atoms per core incoming
                max_atoms = sys.maxint
                edge_pre_vertex = in_edge.pre_vertex
                if isinstance(edge_pre_vertex, AbstractPartitionableVertex):
                    max_atoms = in_edge.pre_vertex.get_max_atoms_per_core()
                if in_edge.pre_vertex.n_atoms < max_atoms:
                    max_atoms = in_edge.pre_vertex.n_atoms

                # Get the number of likely subvertices
                n_edge_subvertices = int(math.ceil(
                    float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))
                n_subvertices += n_edge_subvertices
                n_entries += (
                    n_edge_subvertices * len(in_edge.synapse_information))

        # Multiply by 2 to get an upper bound
        return (
            (n_subvertices * 2 * _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * 2 * _MasterPopEntry.ADDRESS_LIST_ENTRY_SIZE_BYTES) +
            8)

    def get_exact_master_population_table_size(
            self, subvertex, partitioned_graph, graph_mapper):
        """
        :return: the size the master pop table will take in SDRAM (in bytes)
        """
        in_edges = partitioned_graph.incoming_subedges_from_subvertex(
            subvertex)

        n_subvertices = len(in_edges)
        n_entries = 0
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionPartitionedEdge):
                edge = graph_mapper.\
                    get_partitionable_edge_from_partitioned_edge(in_edge)
                n_entries += len(edge.synapse_information)

        # Multiply by 2 to get an upper bound
        return (
            (n_subvertices * 2 * _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * 2 * _MasterPopEntry.ADDRESS_LIST_ENTRY_SIZE_BYTES) +
            8)

    def get_allowed_row_length(self, row_length):
        """

        :param row_length: the row length being considered
        :return: the row length available
        """
        if row_length > 255:
            raise Exception("Only rows of up to 255 entries are allowed")
        return row_length

    def get_next_allowed_address(self, next_address):
        """

        :param next_address: The next address that would be used
        :return: The next address that can be used following next_address
        """
        return next_address

    def initialise_table(self, spec, master_population_table_region):
        """ Initialises the master pop data structure

        :param spec: the dsg writer
        :param master_population_table_region: the region in memory that the\
                master pop table will be written in
        :return:
        """
        self._entries = dict()
        self._n_addresses = 0
        self._n_single_entries = 0

    def update_master_population_table(
            self, spec, block_start_addr, row_length, keys_and_masks,
            master_pop_table_region, is_single=False):
        """ Adds a entry in the binary search to deal with the synaptic matrix

        :param spec: the writer for dsg
        :param block_start_addr: where the synaptic matrix block starts
        :param row_length: how long in bytes each synaptic entry is
        :param keys_and_masks: the keys and masks for this master pop entry
        :param master_pop_table_region: the region id for the master pop
        :param is_single: flag that states if the entry is a direct entry for
        a single row.
        :return: None
        """
        key_and_mask = keys_and_masks[0]
        if key_and_mask.key not in self._entries:
            self._entries[key_and_mask.key] = _MasterPopEntry(
                key_and_mask.key, key_and_mask.mask)
        start_addr = block_start_addr
        # if single, dont add to start address as its going in its own block
        if not is_single:
            start_addr = block_start_addr / 4
        self._entries[key_and_mask.key].append(
            start_addr, row_length, is_single)
        self._n_addresses += 1

    def finish_master_pop_table(self, spec, master_pop_table_region):
        """ Completes any operations required after all entries have been added
        :param spec: the writer for the dsg
        :param master_pop_table_region: the region to which the master pop\
                resides in
        :return: None
        """

        spec.switch_write_focus(region=master_pop_table_region)

        # sort entries by key
        entries = sorted(
            self._entries.values(),
            key=lambda pop_table_entry: pop_table_entry.routing_key)

        # write no master pop entries and the address list size
        n_entries = len(entries)
        spec.write_value(n_entries)
        spec.write_value(self._n_addresses)

        # Generate the table and list as arrays
        pop_table = numpy.zeros(
            n_entries, dtype=self.MASTER_POP_ENTRY_DTYPE)
        address_list = numpy.zeros(
            self._n_addresses, dtype=self.ADDRESS_LIST_DTYPE)
        start = 0
        for i, entry in enumerate(entries):
            pop_table[i]["key"] = entry.routing_key
            pop_table[i]["mask"] = entry.mask
            pop_table[i]["start"] = start
            count = len(entry.addresses_and_row_lengths)
            pop_table[i]["count"] = count
            for j, (address, row_length, is_single) in enumerate(
                    entry.addresses_and_row_lengths):
                single_bit = 0
                if is_single:
                    single_bit = \
                        MasterPopTableAsBinarySearch.SINGLE_BIT_FLAG_BIT
                address_list[start + j] = (
                    (single_bit |
                     (address & 0x7FFFFF) << 8) |
                    (row_length &
                     MasterPopTableAsBinarySearch.ROW_LENGTH_MASK))
            start += count

        # Write the arrays
        spec.write_array(pop_table.view("<u4"))
        spec.write_array(address_list)

        del self._entries
        self._entries = None
        self._n_addresses = 0

    def extract_synaptic_matrix_data_location(
            self, incoming_key_combo, master_pop_base_mem_address, txrx,
            chip_x, chip_y):

        # get entries in master pop
        count_data = txrx.read_memory(
            chip_x, chip_y, master_pop_base_mem_address, 8)
        n_entries, n_addresses = struct.unpack("<II", buffer(count_data))
        n_entry_bytes = (
            n_entries * _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES)
        n_address_bytes = (
            n_addresses * _MasterPopEntry.ADDRESS_LIST_ENTRY_SIZE_BYTES)

        # read in master pop structure
        full_data = txrx.read_memory(
            chip_x, chip_y, master_pop_base_mem_address + 8,
            n_entry_bytes + n_address_bytes)

        # convert into a numpy arrays
        entry_list = numpy.frombuffer(
            full_data, 'uint8', n_entry_bytes, 0).view(
                dtype=self.MASTER_POP_ENTRY_DTYPE)
        address_list = numpy.frombuffer(
            full_data, 'uint8', n_address_bytes, n_entry_bytes).view(
                dtype=self.ADDRESS_LIST_DTYPE)

        entry = self._locate_entry(entry_list, incoming_key_combo)
        if entry is None:
            return []
        addresses = list()
        for i in range(entry["start"], entry["start"] + entry["count"]):
            address_and_row_length = address_list[i]
            is_single = (
                address_and_row_length &
                MasterPopTableAsBinarySearch.SINGLE_BIT_FLAG_BIT) > 0
            address = (
                address_and_row_length &
                MasterPopTableAsBinarySearch.ADDRESS_MASK)
            row_length = (
                address_and_row_length &
                MasterPopTableAsBinarySearch.ROW_LENGTH_MASK)
            if is_single:
                address = address >> 8
            else:
                address = address >> 6

            addresses.append((row_length, address, is_single))
        return addresses

    def _locate_entry(self, entries, key):
        """ searches the binary tree structure for the correct entry.

        :param key: the key to search the master pop table for a given entry
        :return the entry for this given key
        :rtype: _MasterPopEntry
        """
        imin = 0
        imax = len(entries)

        while imin < imax:
            imid = (imax + imin) / 2
            entry = entries[imid]
            if key & entry["mask"] == entry["key"]:
                return entry
            if key > entry["key"]:
                imin = imid + 1
            else:
                imax = imid
        return None

    def get_edge_constraints(self):
        """ Returns any constraints placed on the edges because of having this\
            master pop table implemented in the cores.
        :return:
        """
        return list()
