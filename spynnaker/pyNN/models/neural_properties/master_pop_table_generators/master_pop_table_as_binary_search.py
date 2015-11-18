"""
master pop entry
"""

from spinn_front_end_common.utilities import helpful_functions

# spynnaker imports
from spynnaker.pyNN.models.neural_properties.master_pop_table_generators\
    .abstract_master_pop_table_factory import AbstractMasterPopTableFactory

from pacman.model.partitionable_graph.abstract_partitionable_vertex\
    import AbstractPartitionableVertex

# general imports
import logging
import numpy
import sys
import math

logger = logging.getLogger(__name__)


class _MasterPopEntry(object):
    """
    interal class that contains a master pop entry
    """

    MASTER_POP_ENTRY_SIZE_BYTES = 12
    MASTER_POP_ENTRY_SIZE_WORDS = 3

    def __init__(self, routing_key, mask, address, row_length):
        self._routing_key = routing_key
        self._mask = mask
        self._address = address
        self._row_length = row_length

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
    def address(self):
        """
        :return: the memory addres that this master pop entry points at
        (synaptic matrix)
        """
        return self._address

    @property
    def row_length(self):
        """
        :return: the length of each row in the synaptic matrix that this
        master pop entry points at.
        """
        return self._row_length


class MasterPopTableAsBinarySearch(AbstractMasterPopTableFactory):
    """
    binary search master pop class.
    """

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)
        self._entries = None

    def initialise_table(self, spec, master_population_table_region):
        """
        initilises the master pop data strucutre

        :param spec: the dsg writer
        :param master_population_table_region: the region in memory that the
        master pop table will be written in
        :return:
        """
        self._entries = list()

    def extract_synaptic_matrix_data_location(
            self, incoming_key_combo, master_pop_base_mem_address, txrx,
            chip_x, chip_y):

        # get entries in master pop
        n_entries = helpful_functions.read_data(
            chip_x, chip_y, master_pop_base_mem_address, 4, "<I", txrx)
        n_bytes = (n_entries *
                   _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES)

        # read in master pop structure
        full_data = txrx.read_memory(
            chip_x, chip_y, master_pop_base_mem_address + 4, n_bytes)

        # convert into a numpy array
        master_pop_structure = numpy.frombuffer(
            dtype='uint8', buffer=full_data).view(dtype='<u4')

        entries = list()
        for index in range(0, n_bytes / 4, 3):
            key = master_pop_structure[index]
            mask = master_pop_structure[index + 1]
            address_and_row_length = master_pop_structure[index + 2]
            entries.append(_MasterPopEntry(
                key, mask, address_and_row_length >> 8,
                address_and_row_length & 0xFF))

        entry = self._locate_entry(entries, incoming_key_combo)

        max_row_size = entry.row_length
        return max_row_size, entry.address * 4

    def _locate_entry(self, entries, key):
        """ searches the binary tree structure for the correct entry.

        :param key: the key to search the master pop table for a given entry
        from
        :return the entry for this given key
        :rtype: _MasterPopEntry
        """
        imin = 0
        imax = len(entries)

        while imin < imax:
            imid = (imax + imin) / 2
            entry = entries[imid]
            if key & entry.mask == entry.routing_key:
                return entry
            if key > entry.routing_key:
                imin = imid + 1
            else:
                imax = imid
        raise Exception("Entry not found for key {}".format(key))

    def get_master_population_table_size(self, vertex_slice, in_edges):
        """

        :param vertex_slice:the slice of the partitionable vertex that the
        partitioned vertex will be holding
        :param in_edges: the in coming edges for the partitioned vertex this
        master pop is asosicated with.
        :return: the size the master pop table will take in sdram (in bytes)
        """

        # Entry for each sub-edge - but don't know the subedges yet, so
        # assume multiple entries for each edge
        n_subvertices = 0
        for in_edge in in_edges:

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
            n_subvertices += int(math.ceil(
                float(in_edge.pre_vertex.n_atoms) / float(max_atoms)))

        return (n_subvertices * 2 *
                _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES) + 4

    def get_allowed_row_length(self, row_length):
        """

        :param row_length: the row elngth being considered
        :return: the row length avilable
        """
        if row_length > 255:
            raise Exception("Only rows of up to 255 entries are allowed")
        return row_length

    def get_next_allowed_address(self, next_address):
        """

        :param next_address: ???????
        :return: ????????
        """
        return next_address

    def update_master_population_table(
            self, spec, block_start_addr, row_length, keys_and_masks,
            master_pop_table_region):
        """
        adds a entry in the binary search to deal with the synapatic matrix
        :param spec: the writer for dsg
        :param block_start_addr: where the synpatic matrix block starts
        :param row_length: how long in bytes each synpatic entry is
        :param keys_and_masks: the keys and masks for this master pop entry
        :param master_pop_table_region: the region id for the master pop
        :return: None
        """
        key_and_mask = keys_and_masks[0]
        self._entries.append(_MasterPopEntry(
            key_and_mask.key, key_and_mask.mask,
            block_start_addr / 4, row_length))

    def finish_master_pop_table(self, spec, master_pop_table_region):
        """
        completes any operations required after all entrieres have been added.
        :param spec: the writer for the dsg
        :param master_pop_table_region: the region to which the master pop
        resides in
        :return: None
        """

        # locate the number of entries to be written to the master pop
        n_entries = len(self._entries)
        spec.switch_write_focus(region=master_pop_table_region)

        # write no entries first so that the tree can be read in easily.
        spec.write_value(n_entries)

        # sort out entries based off key_combo
        self._entries = sorted(
            self._entries,
            key=lambda pop_table_entry: pop_table_entry.routing_key)

        # add each entry
        for pop_entry in self._entries:
            spec.write_value(pop_entry.routing_key)
            spec.write_value(pop_entry.mask)
            spec.write_value((pop_entry.address << 8) | pop_entry.row_length)

    def get_edge_constraints(self):
        """
        returns any constraints placed on the edges because of having this
        master pop table implimented in the cores.
        :return:
        """
        return list()
