
# spynnaker imports
import struct
from pacman.model.abstract_classes import AbstractHasGlobalMaxAtoms
from pacman.model.graphs.application import ApplicationVertex
from spinn_utilities.overrides import overrides

from spynnaker.pyNN.models.neural_projections \
    import ProjectionApplicationEdge, ProjectionMachineEdge
from spynnaker.pyNN.exceptions import SynapseRowTooBigException,\
    SynapticConfigurationException
from .abstract_master_pop_table_factory import AbstractMasterPopTableFactory

# general imports
import logging
import numpy
import sys
import math

logger = logging.getLogger(__name__)
_TWO_WORDS = struct.Struct("<II")


class _MasterPopEntry(object):
    """ Internal class that contains a master population table entry
    """
    __slots__ = [
        "_addresses_and_row_lengths",
        "_mask",
        "_routing_key",
	"_conn_lookup"]

    MASTER_POP_ENTRY_SIZE_BYTES = 12
    MASTER_POP_ENTRY_SIZE_WORDS = 3
    ADDRESS_LIST_ENTRY_SIZE_BYTES = 4
    ADDRESS_LIST_ENTRY_SIZE_WORDS = 1
    CONN_LOOKUP_SIZE_BYTES = 4#1#

    def __init__(self, routing_key, mask):
        self._routing_key = routing_key
        self._mask = mask
        self._addresses_and_row_lengths = list()
	self._conn_lookup = None


    def append(self, address, row_length, is_single):
        self._addresses_and_row_lengths.append(
            (address, row_length, is_single))
    def set_conn_lookup(self,conn_lookup):
	self._conn_lookup = conn_lookup
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
        :return: the memory address that this master pop entry points at\
            (synaptic matrix)
        """
        return self._addresses_and_row_lengths


class MasterPopTableAsBinarySearch(AbstractMasterPopTableFactory):
    """ Master population table, implemented as binary search master.
    """
    __slots__ = [
        "_entries",
        "_n_addresses",
        "_n_single_entries",
        "_conn_lookup",
        "_n_conn_lookup_words_per_entry"]

    # Switched ordering of count and start as numpy will switch them back
    # when asked for view("<4")
    MASTER_POP_ENTRY_DTYPE = [
        ("key", "<u4"), ("mask", "<u4"), ("start", "<u2"), ("count", "<u2")]

    ADDRESS_LIST_DTYPE = "<u4"
    CONN_LOOKUP_DTYPE = "<u4"#"<u1"
    N_ATOMS_PER_CORE = 255#128

    # top bit of the 32 bit number
    SINGLE_BIT_FLAG_BIT = 0x80000000
    ROW_LENGTH_MASK = 0xFF
    ADDRESS_MASK = 0x7FFFFF00
    ADDRESS_SCALE = 16
    ADDRESS_SCALED_SHIFT = 8 - 4

    def __init__(self):
        self._entries = None
        self._n_addresses = 0
        self._n_single_entries = None
        self._conn_lookup = None
        self._n_conn_lookup_words_per_entry = int(numpy.ceil(self.N_ATOMS_PER_CORE / 32.))


    @overrides(AbstractMasterPopTableFactory.get_master_population_table_size)
    def get_master_population_table_size(self, vertex_slice, in_edges):
        """
        :param vertex_slice: the slice of the vertex
        :param in_edges: the in coming edges
        :return: the size the master pop table will take in SDRAM (in bytes)
        """

        # Entry for each edge - but don't know the edges yet, so
        # assume multiple entries for each edge
        n_vertices = 0
        n_entries = 0
        for in_edge in in_edges:

            if isinstance(in_edge, ProjectionApplicationEdge):

                # TODO: Fix this to be more accurate!
                # May require modification to the master population table
                # Get the number of atoms per core incoming
                max_atoms = sys.maxsize
                edge_pre_vertex = in_edge.pre_vertex
                if (isinstance(edge_pre_vertex, ApplicationVertex) and
                        isinstance(
                            edge_pre_vertex, AbstractHasGlobalMaxAtoms)):

                    max_atoms = in_edge.pre_vertex.get_max_atoms_per_core()
                if in_edge.pre_vertex.n_atoms < max_atoms:
                    max_atoms = in_edge.pre_vertex.n_atoms

                # Get the number of likely vertices
                n_edge_vertices = int(math.ceil(
                    float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))
                n_vertices += n_edge_vertices
                n_entries += (
                    n_edge_vertices * len(in_edge.synapse_information))

        # Multiply by 2 to get an upper bound
        return (
            (n_vertices * 2 * _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * 2 * _MasterPopEntry.ADDRESS_LIST_ENTRY_SIZE_BYTES) +
            8)

    def get_exact_master_population_table_size(
            self, vertex, machine_graph, graph_mapper):
        """
        :return: the size the master pop table will take in SDRAM (in bytes)
        """
        in_edges = machine_graph.get_edges_ending_at_vertex(vertex)

        n_vertices = len(in_edges)
        n_entries = 0
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionMachineEdge):
                edge = graph_mapper.get_application_edge(in_edge)
                n_entries += len(edge.synapse_information)

        # Multiply by 2 to get an upper bound
        return (
            (n_vertices * 2 * _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * 2 * _MasterPopEntry.ADDRESS_LIST_ENTRY_SIZE_BYTES) +
            # 8 + (2*n_entries * self.N_ATOMS_PER_CORE * _MasterPopEntry.CONN_LOOKUP_SIZE_BYTES))
            8 + (2*n_entries * self._n_conn_lookup_words_per_entry * _MasterPopEntry.CONN_LOOKUP_SIZE_BYTES))

    def get_allowed_row_length(self, row_length):
        """
        :param row_length: the row length being considered
        :return: the row length available
        """
        if row_length > 255:
            raise SynapseRowTooBigException(
                255, "Only rows of up to 255 entries are allowed")
        return row_length

    def get_next_allowed_address(self, next_address):
        """
        :param next_address: The next address that would be used
        :return: The next address that can be used following next_address
        """
        next_address = (
            (next_address + (self.ADDRESS_SCALE - 1)) //
            self.ADDRESS_SCALE) * self.ADDRESS_SCALE
        if (next_address / self.ADDRESS_SCALE) > 0x7FFFFF:
            raise SynapticConfigurationException(
                "Address {} is out of range for this population table!".format(
                    hex(next_address)))
        return next_address

    def initialise_table(self, spec, master_population_table_region):
        """ Initialise the master pop data structure

        :param spec: the DSG writer
        :param master_population_table_region: \
            the region in memory that the master pop table will be written in
        :rtype: None
        """
        self._entries = dict()
        self._n_addresses = 0
        self._n_single_entries = 0
        # self._conn_lookup = numpy.zeros(0,dtype=bool)
        self._conn_lookup = numpy.zeros(0,dtype="uint32")

    @overrides(AbstractMasterPopTableFactory.update_master_population_table,
               extend_doc=False)
    def update_master_population_table(
            self, spec, block_start_addr, row_length, key_and_mask,
            master_pop_table_region, is_single=False,conn_matrix=None):
        """ Add an entry in the binary search to deal with the synaptic matrix

        :param spec: the writer for DSG
        :param block_start_addr: where the synaptic matrix block starts
        :param row_length: how long in bytes each synaptic entry is
        :param key_and_mask: the key and mask for this master pop entry
        :param master_pop_table_region: the region ID for the master pop
        :param is_single: \
            Flag that states if the entry is a direct entry for a single row.
        :rtype: None
        """
        # pylint: disable=too-many-arguments, arguments-differ
        if key_and_mask.key not in self._entries:
            self._entries[key_and_mask.key] = _MasterPopEntry(
                key_and_mask.key, key_and_mask.mask)
        start_addr = block_start_addr

        # if single, don' t add to start address as its going in its own block
        if not is_single:
            start_addr = block_start_addr // self.ADDRESS_SCALE
        self._entries[key_and_mask.key].append(
            start_addr, row_length, is_single)
        self._n_addresses += 1
	if conn_matrix is not None:
        	lookup_entry = numpy.sum(conn_matrix,axis=1,dtype=bool)
		if len(lookup_entry) < self.N_ATOMS_PER_CORE:
	    	    print "lookup entry len:{}".format(len(lookup_entry))
	    	    lookup_entry = numpy.append(lookup_entry,numpy.zeros(self.N_ATOMS_PER_CORE-len(lookup_entry),dtype=bool))
		self._entries[key_and_mask.key].set_conn_lookup(lookup_entry)
	else:
	    self._entries[key_and_mask.key].set_conn_lookup(numpy.ones(self.N_ATOMS_PER_CORE,dtype=bool))
	#self._conn_lookup = numpy.append(self._conn_lookup,lookup_entry)

    @overrides(AbstractMasterPopTableFactory.finish_master_pop_table)
    def finish_master_pop_table(self, spec, master_pop_table_region):
        spec.switch_write_focus(region=master_pop_table_region)

        # sort entries by key - This will screw up the matching of the conn lookup to each entry!
        entries = sorted(
            self._entries.values(),
            key=lambda entry: entry.routing_key)

        # write no master pop entries and the address list size
        n_entries = len(entries)
        spec.write_value(n_entries)
        spec.write_value(self._n_addresses)

        # Generate the table and list as arrays
        pop_table = numpy.zeros(n_entries, dtype=self.MASTER_POP_ENTRY_DTYPE)
        address_list = numpy.zeros(
            self._n_addresses, dtype=self.ADDRESS_LIST_DTYPE)
        start = 0
        for i, entry in enumerate(entries):
            start += self._make_pop_table_entry(
                entry, i, start, pop_table, address_list)
            bitfield_conn_lookup = numpy.zeros(self._n_conn_lookup_words_per_entry,dtype="uint32")
            for step,j in enumerate(range(0,self.N_ATOMS_PER_CORE,32)):
                lookup_bools = entry._conn_lookup[j:j+32]
                indices = numpy.nonzero(lookup_bools)[0]
                for idx in indices:
                    bitfield_conn_lookup[step]|= 1<<(31-idx)

            # self._conn_lookup = numpy.append(self._conn_lookup,entry._conn_lookup)
            self._conn_lookup = numpy.append(self._conn_lookup,bitfield_conn_lookup.flatten())

        # Write the arrays
        spec.write_array(pop_table.view("<u4"))
        spec.write_array(address_list)
	#bool_byte_array = self._conn_lookup.view(self.CONN_LOOKUP_DTYPE)
    #TODO: rewrite this stuff for bitfield imp
	print "n_entries ={}".format(n_entries)
	print "conn_lookup size:{}, dtype={}".format(self._conn_lookup.size,self._conn_lookup.dtype)
	# bool_array_len = self._conn_lookup.size
	# accepted_length = int(4 * numpy.ceil(bool_array_len/4.))
	# extra_bytes = accepted_length - bool_array_len
	# self._conn_lookup = numpy.append(self._conn_lookup,numpy.zeros(extra_bytes,dtype=bool))
	bool_byte_array = self._conn_lookup.view("uint32")
	print "bool byte array size:{}".format(bool_byte_array.size)
        spec.write_array(bool_byte_array)

        self._entries.clear()
        del self._entries
        self._entries = None
        self._n_addresses = 0

    def _make_pop_table_entry(self, entry, i, start, pop_table, address_list):
        # pylint: disable=too-many-arguments
        pop_table[i]["key"] = entry.routing_key
        pop_table[i]["mask"] = entry.mask
        pop_table[i]["start"] = start
        count = len(entry.addresses_and_row_lengths)
        pop_table[i]["count"] = count
        for j, (address, row_length, is_single) in enumerate(
                entry.addresses_and_row_lengths):
            single_bit = self.SINGLE_BIT_FLAG_BIT if is_single else 0
            address_list[start + j] = (
                (single_bit | (address & 0x7FFFFF) << 8) |
                (row_length & self.ROW_LENGTH_MASK))
        return count

    @overrides(
        AbstractMasterPopTableFactory.extract_synaptic_matrix_data_location)
    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address, txrx,
            chip_x, chip_y):
        # pylint: disable=too-many-arguments, too-many-locals, arguments-differ

        # get entries in master pop
        n_entries, n_addresses = _TWO_WORDS.unpack(txrx.read_memory(
            chip_x, chip_y, master_pop_base_mem_address, _TWO_WORDS.size))
        n_entry_bytes = (
            n_entries * _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES)
        n_address_bytes = (
            n_addresses * _MasterPopEntry.ADDRESS_LIST_ENTRY_SIZE_BYTES)

        # read in master pop structure
        full_data = txrx.read_memory(
            chip_x, chip_y, master_pop_base_mem_address + _TWO_WORDS.size,
            n_entry_bytes + n_address_bytes)

        # convert into a numpy arrays
        entry_list = numpy.frombuffer(
            full_data, 'uint8', n_entry_bytes, 0).view(
                dtype=self.MASTER_POP_ENTRY_DTYPE)
        address_list = numpy.frombuffer(
            full_data, 'uint8', n_address_bytes, n_entry_bytes).view(
                dtype=self.ADDRESS_LIST_DTYPE)

        entry = self._locate_entry(entry_list, incoming_key)
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
                address = address >> self.ADDRESS_SCALED_SHIFT

            addresses.append((row_length, address, is_single))
        return addresses

    @staticmethod
    def _locate_entry(entries, key):
        """ Search the binary tree structure for the correct entry.

        :param key: the key to search the master pop table for a given entry
        :return: the entry for this given key
        :rtype: :py:class:`_MasterPopEntry`
        """
        imin = 0
        imax = len(entries)

        while imin < imax:
            imid = (imax + imin) // 2
            entry = entries[imid]
            if key & entry["mask"] == entry["key"]:
                return entry
            if key > entry["key"]:
                imin = imid + 1
            else:
                imax = imid
        return None

    @overrides(AbstractMasterPopTableFactory.get_edge_constraints)
    def get_edge_constraints(self):
        return list()