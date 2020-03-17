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
import math
import numpy
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.exceptions import (
    SynapseRowTooBigException, SynapticConfigurationException)
from spynnaker.pyNN.utilities.constants import POPULATION_BASED_REGIONS,\
    POP_TABLE_MAX_ROW_LENGTH

logger = logging.getLogger(__name__)
# "single" flag is top bit of the 32 bit number
_SINGLE_BIT_FLAG_BIT = 0x80000000
# Row length is 1-256 (with subtraction of 1)
_ROW_LENGTH_MASK = POP_TABLE_MAX_ROW_LENGTH - 1
# Address is 23 bits, but scaled by a factor of 16
_ADDRESS_MASK = 0x7FFFFF
# Scale factor for an address
_ADDRESS_SCALE = 16
# Shift of addresses within the address and row length field
_ADDRESS_SHIFT = 8
# The shift of n_neurons in the n_neurons_and_core_shift field
_N_NEURONS_SHIFT = 5
# Maximum number of neurons supported per core (= 11-bits of neurons)
_MAX_N_NEURONS = (2 ** 11) - 1
# Maximum core mask (i.e. number of cores) (=16-bits of mask)
_MAX_CORE_MASK = 0xFFFF
# An invalid entry in the address and row length list
_INVALID_ADDDRESS_AND_ROW_LENGTH = 0xFFFFFFFF
# Flag of extra info at the start of the address list
_EXTRA_INFO_FLAG = 0x8000
# Mask to get the start of the address list
_START_MASK = 0x7FFF
# Maximum start position in the address list
_MAX_ADDRESS_START = _START_MASK
# Maximum count of address list entries for a single pop table entry
_MAX_ADDRESS_COUNT = 0xFFFF
# DTypes of the structs
_MASTER_POP_ENTRY_DTYPE = [
    ("key", "<u4"), ("mask", "<u4"),
    ("start_and_flag", "<u2"), ("count", "<u2")]
_ADDRESS_DTYPE = "<u4"
_EXTRA_INFO_DTYPE = [
    ("core_mask", "<u2"), ("n_neurons_and_core_shift", "<u2")]
# Sizes of structs
_MASTER_POP_ENTRY_SIZE_BYTES = numpy.dtype(_MASTER_POP_ENTRY_DTYPE).itemsize
_ADDRESS_LIST_ENTRY_SIZE_BYTES = numpy.dtype(_ADDRESS_DTYPE).itemsize
_EXTRA_INFO_ENTRY_SIZE_BYTES = numpy.dtype(_EXTRA_INFO_DTYPE).itemsize
# Base size - 2 words for size of table and address list
_BASE_SIZE_BYTES = 8
# Over-scale of estimate for safety
_OVERSCALE = 2


class _MasterPopEntry(object):
    """ Internal class that contains a master population table entry
    """
    __slots__ = [
        "__addresses_and_row_lengths",
        # The mask to match this entry on
        "__mask",
        # The routing key to match this entry on
        "__routing_key",
        # The part of the key where the core id is held after shifting (below)
        "__core_mask",
        # Where in the key that the core id is held
        "__core_shift",
        # The number of neurons on every core except the last
        "__n_neurons"]

    def __init__(self, routing_key, mask, core_mask, core_shift, n_neurons):
        self.__routing_key = routing_key
        self.__mask = mask
        self.__core_mask = core_mask
        self.__core_shift = core_shift
        self.__n_neurons = n_neurons
        self.__addresses_and_row_lengths = list()

    def append(self, address, row_length, is_single):
        index = len(self.__addresses_and_row_lengths)
        if index > _MAX_ADDRESS_COUNT:
            raise SynapticConfigurationException(
                "{} connections for the same source key (maximum {})".format(
                    index, _MAX_ADDRESS_COUNT))
        self.__addresses_and_row_lengths.append(
            (address, row_length, is_single, True))
        return index

    def append_invalid(self):
        index = len(self.__addresses_and_row_lengths)
        self.__addresses_and_row_lengths.append((0, 0, 0, False))
        return index

    @property
    def routing_key(self):
        """
        :return: the key combo of this entry
        """
        return self.__routing_key

    @property
    def mask(self):
        """
        :return: the mask of the key for this master pop entry
        """
        return self.__mask

    @property
    def addresses_and_row_lengths(self):
        """
        :return: the memory address that this master pop entry points at\
            (synaptic matrix)
        """
        return self.__addresses_and_row_lengths

    def write_to_table(self, entry, address_list, start):
        """ Write entries to the master population table

        :param entry: The entry to write to
        :param address_list: The address_list to write to
        :param start: The index of the entry of the address list to start at
        :return: The number of entries written to the address list
        """
        entry["key"] = self.__routing_key
        entry["mask"] = self.__mask
        entry["start_and_flag"] = start
        count = len(self.__addresses_and_row_lengths)
        entry["count"] = count
        next_addr = start
        n_entries = count
        # If there is a core mask, add a special entry for it
        if self.__core_mask != 0:
            entry["start_and_flag"] |= _EXTRA_INFO_FLAG
            extra_info = numpy.zeros(1, dtype=_EXTRA_INFO_DTYPE)
            extra_info["core_mask"] = self.__core_mask
            extra_info["n_neurons_and_core_shift"] = (
                (self.__n_neurons << _N_NEURONS_SHIFT) | self.__core_shift)
            address_list[start] = extra_info.view(_ADDRESS_DTYPE)[0]
            next_addr += 1
            n_entries += 1

        for j, (address, row_length, is_single, is_valid) in enumerate(
                self.__addresses_and_row_lengths):
            if not is_valid:
                address_list[next_addr + j] = _INVALID_ADDDRESS_AND_ROW_LENGTH
            else:
                single_bit = _SINGLE_BIT_FLAG_BIT if is_single else 0
                address_list[next_addr + j] = (
                    single_bit |
                    ((address & _ADDRESS_MASK) << _ADDRESS_SHIFT) |
                    (row_length & _ROW_LENGTH_MASK))
        return n_entries


class MasterPopTableAsBinarySearch(object):
    """ Master population table, implemented as binary search master.
    """
    __slots__ = [
        "__entries",
        "__n_addresses"]

    def __init__(self):
        self.__entries = None
        self.__n_addresses = 0

    @staticmethod
    def get_master_population_table_size(in_edges):
        """ Get the size of the master population table in SDRAM

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
                vertex = in_edge.pre_vertex
                max_atoms = float(min(vertex.get_max_atoms_per_core(),
                                      vertex.n_atoms))

                # Get the number of likely vertices
                n_edge_vertices = int(math.ceil(vertex.n_atoms / max_atoms))
                n_vertices += n_edge_vertices
                n_entries += (
                    n_edge_vertices * len(in_edge.synapse_information))

        # Multiply by 2 to get an upper bound
        return (
            _BASE_SIZE_BYTES
            (n_vertices * _OVERSCALE * _MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_vertices * _OVERSCALE * _EXTRA_INFO_ENTRY_SIZE_BYTES) +
            (n_entries * _OVERSCALE * _ADDRESS_LIST_ENTRY_SIZE_BYTES))

    def get_allowed_row_length(self, row_length):
        """
        :param row_length: the row length being considered
        :return: the row length available
        """

        if row_length > POP_TABLE_MAX_ROW_LENGTH:
            raise SynapseRowTooBigException(
                POP_TABLE_MAX_ROW_LENGTH,
                "Only rows of up to {} entries are allowed".format(
                    POP_TABLE_MAX_ROW_LENGTH))
        return row_length

    def get_next_allowed_address(self, next_address):
        """
        :param next_address: The next address that would be used
        :return: The next address that can be used following next_address
        """
        addr_scaled = (next_address + (_ADDRESS_SCALE - 1)) // _ADDRESS_SCALE
        if addr_scaled > _ADDRESS_MASK:
            raise SynapticConfigurationException(
                "Address {} is out of range for this population table!".format(
                    hex(addr_scaled * _ADDRESS_SCALE)))
        return addr_scaled * _ADDRESS_SCALE

    def initialise_table(self):
        """ Initialise the master pop data structure.

        :rtype: None
        """
        self.__entries = dict()
        self.__n_addresses = 0

    def update_master_population_table(
            self, block_start_addr, row_length, key_and_mask, core_mask,
            core_shift, n_neurons, is_single=False):
        """ Add an entry in the binary search to deal with the synaptic matrix

        :param block_start_addr: where the synaptic matrix block starts
        :param row_length: how long in words each row is
        :param key_and_mask: the key and mask for this master pop entry
        :type key_and_mask: \
            :py:class:`pacman.model.routing_info.BaseKeyAndMask`
        :param core_mask: Mask for the part of the key that identifies the core
        :param core_shift: The shift of the mask to get to the core_mask
        :param n_neurons: \
            The number of neurons in each machine vertex (bar the last)
        :param is_single: \
            Flag that states if the entry is a direct entry for a single row.
        :return: The index of the entry, to be used to retrieve it
        :rtype: int
        :raises SynapticConfigurationException: If a bad address is used.
        """
        # If there are too many neurons per core, fail
        if n_neurons > _MAX_N_NEURONS:
            raise SynapticConfigurationException(
                "The parameter n_neurons of {} is too big (maximum {})".format(
                    n_neurons, _MAX_N_NEURONS))

        # If the core mask is too big, fail
        if core_mask > _MAX_CORE_MASK:
            raise SynapticConfigurationException(
                "The core mask of {} is too big (maximum {})".format(
                    core_mask, _MAX_CORE_MASK))

        # pylint: disable=too-many-arguments, arguments-differ
        if key_and_mask.key not in self.__entries:
            if self.__n_addresses > _MAX_ADDRESS_START:
                raise SynapticConfigurationException(
                    "The table already contains {} entries;"
                    " adding another is too many".format(self.__n_addresses))
            self.__entries[key_and_mask.key] = _MasterPopEntry(
                key_and_mask.key, key_and_mask.mask, core_mask, core_shift,
                n_neurons)
            # Need to add an extra "address" for the extra_info if needed
            if core_mask != 0:
                self.__n_addresses += 1

        # if not single, scale the address
        start_addr = block_start_addr
        if not is_single:
            if block_start_addr % _ADDRESS_SCALE != 0:
                raise SynapticConfigurationException(
                    "Address {} is not compatible with this table".format(
                        block_start_addr))
            start_addr = block_start_addr // _ADDRESS_SCALE
            if start_addr & _ADDRESS_MASK != start_addr:
                raise SynapticConfigurationException(
                    "Address {} is too big for this table".format(
                        block_start_addr))
        row_length = self.get_allowed_row_length(row_length)
        index = self.__entries[key_and_mask.key].append(
            start_addr, row_length - 1, is_single)
        self.__n_addresses += 1
        return index

    def add_invalid_entry(
            self, key_and_mask, core_mask=0, core_shift=0, n_neurons=0):
        """ Add an entry to the table that doesn't point to anywhere.  Used\
            to keep indices in synchronisation between e.g. normal and delay\
            entries and between entries on different cores

        :param key_and_mask: a key_and_mask object used as part of describing\
            an edge that will require being received to be stored in the\
            master pop table; the whole edge will become multiple calls to\
            this function
        :type key_and_mask: \
            :py:class:`pacman.model.routing_info.BaseKeyAndMask`
        :param core_mask: Mask for the part of the key that identifies the core
        :param core_shift: The shift of the mask to get to the core_mask
        :param n_neurons: \
            The number of neurons in each machine vertex (bar the last)
        """
        if key_and_mask.key not in self.__entries:
            self.__entries[key_and_mask.key] = _MasterPopEntry(
                key_and_mask.key, key_and_mask.mask, core_mask, core_shift,
                n_neurons)
            # Need to add an extra "address" for the extra_info if needed
            if core_mask != 0:
                self.__n_addresses += 1
        index = self.__entries[key_and_mask.key].append_invalid()
        self.__n_addresses += 1
        return index

    def finish_master_pop_table(self, spec, master_pop_table_region):
        """ Complete the master pop table in the data specification.

        :param spec: the data specification to write the master pop entry to
        :param master_pop_table_region: \
            the region to which the master pop table is being stored
        """
        # sort entries by key
        entries = sorted(
            self.__entries.values(),
            key=lambda entry: entry.routing_key)
        n_entries = len(entries)

        # reserve space and switch
        master_pop_table_sz = (
            _BASE_SIZE_BYTES +
            n_entries * _MASTER_POP_ENTRY_SIZE_BYTES +
            self.__n_addresses * _ADDRESS_LIST_ENTRY_SIZE_BYTES)
        spec.reserve_memory_region(
            region=POPULATION_BASED_REGIONS.POPULATION_TABLE.value,
            size=master_pop_table_sz, label='PopTable')
        spec.switch_write_focus(region=master_pop_table_region)

        # write no master pop entries and the address list size
        spec.write_value(n_entries)
        spec.write_value(self.__n_addresses)

        # Generate the table and list as arrays
        pop_table = numpy.zeros(n_entries, dtype=_MASTER_POP_ENTRY_DTYPE)
        address_list = numpy.zeros(self.__n_addresses, dtype=_ADDRESS_DTYPE)
        start = 0
        for i, entry in enumerate(entries):
            table_entry = pop_table[i]
            start += entry.write_to_table(table_entry, address_list, start)

        # Write the arrays
        spec.write_array(pop_table.view("<u4"))
        spec.write_array(address_list)

        self.__entries.clear()
        del self.__entries
        self.__entries = None
        self.__n_addresses = 0

    def get_edge_constraints(self):
        """ Gets the constraints for this table on edges coming in to a vertex.

        :return: a list of constraints
        :rtype: list(:py:class:`pacman.model.constraints.AbstractConstraint`)
        """
        return list()

    @property
    def max_n_neurons_per_core(self):
        """ The maximum number of neurons per core supported when a core-mask\
            is > 0.
        """
        return _MAX_N_NEURONS

    @property
    def max_core_mask(self):
        """ The maximum core mask supported when n_neurons is > 0; this is the\
            maximum number of cores that can be supported in a joined mask
        """
        return _MAX_CORE_MASK

    @property
    def max_index(self):
        """ The maximum index of a synaptic connection
        """
        return _MAX_ADDRESS_COUNT
