# Copyright (c) 2017-2019 The University of Manchester
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

import logging
import struct
import numpy
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD, \
    SARK_PER_MALLOC_SDRAM_USAGE
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, ProjectionMachineEdge)
from spynnaker.pyNN.exceptions import (
    SynapseRowTooBigException, SynapticConfigurationException)

logger = logging.getLogger(__name__)
_TWO_WORDS = struct.Struct("<II")
#: Number of words in a master population table entry
_MASTER_POP_ENTRY_SIZE_WORDS = 3
_MASTER_POP_ENTRY_SIZE_BYTES = _MASTER_POP_ENTRY_SIZE_WORDS * BYTES_PER_WORD
#: Number of words in the address list
_ADDRESS_LIST_ENTRY_SIZE_WORDS = 1
_ADDRESS_LIST_ENTRY_SIZE_BYTES = (
    _ADDRESS_LIST_ENTRY_SIZE_WORDS * BYTES_PER_WORD)
# Switched ordering of count and start as numpy will switch them back
# when asked for view("<4")
_MASTER_POP_ENTRY_DTYPE = [
    ("key", "<u4"), ("mask", "<u4"), ("start", "<u2"), ("count", "<u2")]

_ADDRESS_LIST_DTYPE = "<u4"

# top bit of the 32 bit number
_SINGLE_BIT_FLAG_BIT = 0x80000000
_ROW_LENGTH_MASK = 0xFF
_ADDRESS_MASK = 0x7FFFFF00
_ADDRESS_SCALE = 16
_ADDRESS_SCALED_SHIFT = 8 - 4


class _MasterPopEntry(object):
    """ Internal class that contains a master population table entry
    """
    __slots__ = [
        "__addresses_and_row_lengths",
        "__mask",
        "__routing_key"]

    def __init__(self, routing_key, mask):
        """
        :param int routing_key:
        :param int mask:
        """
        self.__routing_key = routing_key
        self.__mask = mask
        self.__addresses_and_row_lengths = list()

    def append(self, address, row_length, is_single):
        index = len(self.__addresses_and_row_lengths)
        self.__addresses_and_row_lengths.append(
            (address, row_length, is_single))
        return index

    @property
    def routing_key(self):
        """
        :return: the key combo of this entry
        :rtype: int
        """
        return self.__routing_key

    @property
    def mask(self):
        """
        :return: the mask of the key for this master pop entry
        :rtype: int
        """
        return self.__mask

    @property
    def addresses_and_row_lengths(self):
        """
        :return: the memory address that this master pop entry points at\
            (synaptic matrix)
        :rtype: list(tuple(int,int,bool))
        """
        return self.__addresses_and_row_lengths


class MasterPopTableAsBinarySearch(object):
    """ Master population table, implemented as binary search master.
    """
    __slots__ = [
        "__entries",
        "__n_addresses",
        "__n_single_entries",
        "__edge_constraints"]

    MAX_ROW_LENGTH = 255
    UPPER_BOUND_FUDGE = 2
    TOP_MEMORY_POINT = 0x7FFFFF

    MAX_ROW_LENGTH_ERROR_MSG = (
        "Only rows of up to {} entries are allowed".format(MAX_ROW_LENGTH))

    OUT_OF_RANGE_ERROR_MESSAGE = (
        "Address {} is out of range for this population table!")

    def __init__(self):
        self.__entries = None
        self.__n_addresses = 0
        self.__n_single_entries = None
        self.__edge_constraints = list()

    def get_master_population_table_size(self, in_edges):
        """ Get the size of the master population table in SDRAM

        :param iterable(~pacman.model.graphs.application.ApplicationEdge)\
                in_edges:
            The edges arriving at the vertex that are to be handled by this
            table
        :return: the size the master pop table will take in SDRAM (in bytes)
        :rtype: int
        """

        # Entry for each edge - but don't know the edges yet, so
        # assume multiple entries for each edge
        n_vertices = 0
        n_entries = 0
        for in_edge in in_edges:
            if isinstance(in_edge, ProjectionApplicationEdge):
                slices, is_exact = (
                    in_edge.pre_vertex.splitter_object.get_out_going_slices())
                if is_exact:
                    n_vertices += len(slices)
                    n_entries += len(in_edge.synapse_information)
                else:
                    n_vertices += len(slices) * self.UPPER_BOUND_FUDGE
                    n_entries += (
                        len(in_edge.synapse_information) *
                        self.UPPER_BOUND_FUDGE)

        # Multiply by each specific constant
        return (
            (n_vertices * _MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * _ADDRESS_LIST_ENTRY_SIZE_BYTES) +
            SARK_PER_MALLOC_SDRAM_USAGE)

    def get_exact_master_population_table_size(self, vertex, machine_graph):
        """
        :param PopulationMachineVertex vertex:
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        :return: the size the master pop table will take in SDRAM (in bytes)
        :rtype: int
        """
        in_edges = machine_graph.get_edges_ending_at_vertex(vertex)

        n_vertices = len(in_edges)
        n_entries = sum(
            len(in_edge.app_edge.synapse_information)
            for in_edge in in_edges
            if isinstance(in_edge, ProjectionMachineEdge))

        # Multiply by each specific constant
        # TODO removing the fudge factor should be safe. but currently
        #      causes dse memory leave errors. needs reviewing
        return (
            (n_vertices * self.UPPER_BOUND_FUDGE *
             _MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * self.UPPER_BOUND_FUDGE *
             _ADDRESS_LIST_ENTRY_SIZE_BYTES) + SARK_PER_MALLOC_SDRAM_USAGE)

    def get_allowed_row_length(self, row_length):
        """
        :param int row_length: the row length being considered
        :return: the row length available
        :rtype: int
        :raises SynapseRowTooBigException: If the row won't fit
        """
        if row_length > self.MAX_ROW_LENGTH:
            raise SynapseRowTooBigException(
                self.MAX_ROW_LENGTH, self.MAX_ROW_LENGTH_ERROR_MSG)
        return row_length

    def get_next_allowed_address(self, next_address):
        """
        :param int next_address: The next address that would be used
        :return: The next address that can be used following next_address
        :rtype: int
        :raises SynapticConfigurationException: if the address is out of range
        """
        # How far is the address past an acceptable boundary?
        over = next_address % _ADDRESS_SCALE
        if over:
            next_address += _ADDRESS_SCALE - over
        if next_address // _ADDRESS_SCALE > self.TOP_MEMORY_POINT:
            raise SynapticConfigurationException(
                self.OUT_OF_RANGE_ERROR_MESSAGE.format(hex(next_address)))
        return next_address

    def initialise_table(self):
        """ Initialise the master pop data structure.

        :rtype: None
        """
        self.__entries = dict()
        self.__n_addresses = 0
        self.__n_single_entries = 0

    def update_master_population_table(
            self, block_start_addr, row_length, key_and_mask, is_single=False):
        """ Add an entry in the binary search to deal with the synaptic matrix

        :param int block_start_addr: where the synaptic matrix block starts
        :param int row_length: how long in bytes each synaptic entry is
        :param ~pacman.model.routing_info.BaseKeyAndMask key_and_mask:
            a key_and_mask object used as part of describing an edge that will
            require being received to be stored in the master pop table; the
            whole edge will become multiple calls to this function
        :param bool is_single:
            Flag that states if the entry is a direct entry for a single row.
        :return: The index of the entry, to be used to retrieve it
        :rtype: int
        """
        # pylint: disable=too-many-arguments, arguments-differ
        if key_and_mask.key not in self.__entries:
            self.__entries[key_and_mask.key] = _MasterPopEntry(
                key_and_mask.key, key_and_mask.mask)
        start_addr = block_start_addr

        # if single, don' t add to start address as its going in its own block
        if not is_single:
            start_addr = block_start_addr // _ADDRESS_SCALE
        index = self.__entries[key_and_mask.key].append(
            start_addr, row_length, is_single)
        self.__n_addresses += 1
        return index

    def finish_master_pop_table(self, spec, master_pop_table_region):
        """ Complete the master pop table in the data specification.

        :param ~data_specification.DataSpecificationGenerator spec:
            the data specification to write the master pop entry to
        :param int master_pop_table_region:
            the region to which the master pop table is being stored
        """
        spec.switch_write_focus(region=master_pop_table_region)

        # sort entries by key
        entries = sorted(
            self.__entries.values(),
            key=lambda a_entry: a_entry.routing_key)

        # write no master pop entries and the address list size
        n_entries = len(entries)
        spec.write_value(n_entries)
        spec.write_value(self.__n_addresses)

        # Generate the table and list as arrays
        pop_table = numpy.zeros(n_entries, dtype=_MASTER_POP_ENTRY_DTYPE)
        address_list = numpy.zeros(
            self.__n_addresses, dtype=_ADDRESS_LIST_DTYPE)
        start = 0
        for i, entry in enumerate(entries):
            start += self._make_pop_table_entry(
                entry, i, start, pop_table, address_list)

        # Write the arrays
        spec.write_array(pop_table.view("<u4"))
        spec.write_array(address_list)

        self.__entries.clear()
        del self.__entries
        self.__entries = None
        self.__n_addresses = 0

    @staticmethod
    def _make_pop_table_entry(entry, i, start, pop_table, address_list):
        """
        :param _MasterPopEntry entry:
        :param int i:
        :param int start:
        :param ~numpy.ndarray pop_table:
        :param ~numpy.ndarray address_list:
        :rtype: int
        """
        # pylint: disable=too-many-arguments
        pop_table[i]["key"] = entry.routing_key
        pop_table[i]["mask"] = entry.mask
        pop_table[i]["start"] = start
        count = len(entry.addresses_and_row_lengths)
        pop_table[i]["count"] = count
        for j, (address, row_length, is_single) in enumerate(
                entry.addresses_and_row_lengths):
            single_bit = _SINGLE_BIT_FLAG_BIT if is_single else 0
            address_list[start + j] = (
                (single_bit | (address & 0x7FFFFF) << 8) |
                (row_length & _ROW_LENGTH_MASK))
        return count

    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address, txrx,
            chip_x, chip_y):
        """
        :param int incoming_key:
            the source key which the synaptic matrix needs to be mapped to
        :param int master_pop_base_mem_address:
            the base address of the master pop
        :param ~spinnman.transceiver.Transceiver txrx: the transceiver object
        :param int chip_y: the y coordinate of the chip of this master pop
        :param int chip_x: the x coordinate of the chip of this master pop
        :return: the synaptic matrix memory position information;
            (row_length, location, is_single).
        :rtype: list(tuple(int, int, bool))
        """
        # pylint: disable=too-many-arguments, too-many-locals, arguments-differ

        # get entries in master pop
        n_entries, n_addresses = _TWO_WORDS.unpack(txrx.read_memory(
            chip_x, chip_y, master_pop_base_mem_address, _TWO_WORDS.size))
        n_entry_bytes = n_entries * _MASTER_POP_ENTRY_SIZE_BYTES
        n_address_bytes = n_addresses * _ADDRESS_LIST_ENTRY_SIZE_BYTES

        # read in master pop structure
        full_data = txrx.read_memory(
            chip_x, chip_y, master_pop_base_mem_address + _TWO_WORDS.size,
            n_entry_bytes + n_address_bytes)

        # convert into a numpy arrays
        entry_list = numpy.frombuffer(
            full_data, 'uint8', n_entry_bytes, 0).view(
                dtype=_MASTER_POP_ENTRY_DTYPE)
        address_list = numpy.frombuffer(
            full_data, 'uint8', n_address_bytes, n_entry_bytes).view(
                dtype=_ADDRESS_LIST_DTYPE)

        entry = self._locate_entry(entry_list, incoming_key)
        if entry is None:
            return []
        addresses = list()
        for i in range(entry["start"], entry["start"] + entry["count"]):
            address_and_row_length = address_list[i]
            is_single = (address_and_row_length & _SINGLE_BIT_FLAG_BIT) > 0
            address = address_and_row_length & _ADDRESS_MASK
            row_length = address_and_row_length & _ROW_LENGTH_MASK
            if is_single:
                address = address >> 8
            else:
                address = address >> _ADDRESS_SCALED_SHIFT

            addresses.append((row_length, address, is_single))
        return addresses

    @staticmethod
    def _locate_entry(entries, key):
        """ Search the binary tree structure for the correct entry.

        :param ~numpy.ndarray entries:
        :param int key:
            the key to search the master pop table for a given entry
        :return: the entry for this given key;
            dtype has keys: ``key``, ``mask``, ``start``, ``count``
        :rtype: ~numpy.ndarray
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

    def get_edge_constraints(self):
        """ Gets the constraints for this table on edges coming in to a vertex.

        :return: a list of constraints
        :rtype: list(~pacman.model.constraints.AbstractConstraint)
        """
        return self.__edge_constraints
