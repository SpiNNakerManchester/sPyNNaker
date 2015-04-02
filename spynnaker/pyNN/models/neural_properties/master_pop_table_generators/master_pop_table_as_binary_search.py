from spynnaker.pyNN.models.neural_properties.master_pop_table_generators\
    .abstract_master_pop_table_factory import AbstractMasterPopTableFactory

from pacman.model.partitionable_graph.abstract_partitionable_vertex\
    import AbstractPartitionableVertex

import logging
import numpy
import sys
import math
logger = logging.getLogger(__name__)


class _MasterPopEntry(object):

    MASTER_POP_ENTRY_SIZE_BYTES = 12
    MASTER_POP_ENTRY_SIZE_WORDS = 3

    def __init__(self, key_combo, mask, address, row_length):
        self._key_combo = key_combo
        self._mask = mask
        self._address = address
        self._row_length = row_length

    @property
    def key_combo(self):
        return self._key_combo

    @property
    def mask(self):
        return self._mask

    @property
    def address(self):
        return self._address

    @property
    def row_length(self):
        return self._row_length


class MasterPopTableAsBinarySearch(AbstractMasterPopTableFactory):

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)
        self._entries = None

    def initialise_table(self, spec, master_population_table_region):
        """

        :param spec:
        :param master_population_table_region:
        :return:
        """
        self._entries = list()

    def extract_synaptic_matrix_data_location(
            self, incoming_key_combo, master_pop_base_mem_address, txrx,
            chip_x, chip_y):

        if self._entries is None:

            # get entries in master pop
            n_entries = txrx.read_memory(chip_x, chip_y,
                                         master_pop_base_mem_address, 4)[0]
            n_bytes = (n_entries *
                       _MasterPopEntry.MASTER_POP_ENTRY_SIZE_BYTES)

            # read in master pop structure
            master_pop_structure = txrx.read_memory(
                chip_x, chip_y, master_pop_base_mem_address + 4, n_bytes)
            full_data = bytearray()
            for data in master_pop_structure:
                full_data.extend(data)

            # convert into a numpy array
            master_pop_structure = numpy.frombuffer(
                dtype='uint8', buffer=full_data).view(dtype='<u4')[0]

            self._entries = list()
            for index in range(0, n_bytes / 4, 3):
                key = master_pop_structure[index]
                mask = master_pop_structure[index + 1]
                address_and_row_length = master_pop_structure[index + 2]
                self._entries.append(_MasterPopEntry(
                    key, mask, address_and_row_length >> 8,
                    address_and_row_length & 0xFF))
                print key, mask, address_and_row_length

        entry = self._locate_entry(incoming_key_combo)

        max_row_size = entry.row_length
        return max_row_size, entry.address * 4

    def _locate_entry(self, key):
        """ searches the binary tree structure for the correct entry.

        :param key:
        """
        imin = 0
        imax = len(self._entries)

        while (imin < imax):
            imid = (imax + imin) / 2
            entry = self._entries[imid]
            if key & entry.mask == entry.key_combo:
                return entry
            if key > entry.key_combo:
                imin = imid + 1
            else:
                imax = imid
        raise Exception("Entry not found for key {}".format(key))

    def get_master_population_table_size(self, vertex_slice, in_edges):
        """

        :param vertex_slice:
        :param in_edges:
        :return:
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

        :param row_length:
        :return:
        """
        if row_length > 255:
            raise Exception("Only rows of up to 255 entries are allowed")
        return row_length

    def get_next_allowed_address(self, next_address):
        """

        :param next_address:
        :return:
        """
        return next_address

    def update_master_population_table(
            self, spec, block_start_addr, row_length, keys_and_masks,
            master_pop_table_region):
        key_and_mask = keys_and_masks[0]
        self._entries.append(_MasterPopEntry(
            key_and_mask.key, key_and_mask.mask,
            block_start_addr / 4, row_length))

    def finish_master_pop_table(self, spec, master_pop_table_region):

        # locate the number of entries to be written to the master pop
        n_entries = len(self._entries)
        spec.switch_write_focus(region=master_pop_table_region)

        # write no entries first so that the tree can be read in easily.
        spec.write_value(n_entries)

        # sort out entries based off key_combo
        self._entries = sorted(
            self._entries,
            key=lambda pop_table_entry: pop_table_entry.key_combo)

        # add each entry
        for pop_entry in self._entries:
            spec.write_value(pop_entry.key_combo)
            spec.write_value(pop_entry.mask)
            spec.write_value((pop_entry.address << 8) | pop_entry.row_length)

    def get_edge_constraints(self):
        return list()
