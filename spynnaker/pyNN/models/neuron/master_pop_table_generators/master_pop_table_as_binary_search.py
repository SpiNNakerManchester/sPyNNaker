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
import struct
import numpy
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neural_projections import (
    ProjectionApplicationEdge, ProjectionMachineEdge)
from spynnaker.pyNN.exceptions import (
    SynapseRowTooBigException, SynapticConfigurationException)
from .abstract_master_pop_table_factory import AbstractMasterPopTableFactory

logger = logging.getLogger(__name__)
_TWO_WORDS = struct.Struct("<II")

# "single" flag is top bit of the 32 bit number
_SINGLE_BIT_FLAG_BIT = 0x80000000
# Row length is 1-256 (with subtraction of 1)
_ROW_LENGTH_MASK = 0xFF
# Address is 23 bits, but scaled by a factor of 16
_ADDRESS_MASK = 0x7FFFFF
_ADDRESS_MASK_SHIFTED = 0x7FFFFF00
_ADDRESS_SCALE = 16
# The address is shifted by 8, but also multiplied by 16 so this shift will
# undo both
_ADDRESS_SCALED_SHIFT = 8 - 4
# Shift of addresses within the address and row length field
_ADDRESS_SHIFT = 8
# The shift of n_neurons in the n_neurons_and_core_shift field
_N_NEURONS_SHIFT = 5
# An invalid entry in the address and row length list
_INVALID_ADDDRESS_AND_ROW_LENGTH = 0xFFFFFFFF

# DTypes of the structs
_MASTER_POP_ENTRY_DTYPE = [
    ("key", "<u4"), ("mask", "<u4"), ("start", "<u2"), ("count", "<u2"),
    ("core_mask", "<u2"), ("n_neurons_and_core_shift", "<u2")]
_ADDRESS_LIST_DTYPE = "<u4"

_MASTER_POP_ENTRY_SIZE_BYTES = numpy.dtype(_MASTER_POP_ENTRY_DTYPE).itemsize
_ADDRESS_LIST_ENTRY_SIZE_BYTES = numpy.dtype(_ADDRESS_LIST_DTYPE).itemsize


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
        "_core_mask",
        # Where in the key that the core id is held
        "_core_shift",
        # The number of neurons on every core except the last
        "_n_neurons"]

    def __init__(self, routing_key, mask, core_mask, core_shift, n_neurons):
        self.__routing_key = routing_key
        self.__mask = mask
        self._core_mask = core_mask
        self._core_shift = core_shift
        self._n_neurons = n_neurons
        self.__addresses_and_row_lengths = list()

    def append(self, address, row_length, is_single):
        index = len(self.__addresses_and_row_lengths)
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

    def write_to_table(self, entry, address_list, start):
        entry["key"] = self.__routing_key
        entry["mask"] = self.__mask
        entry["start"] = start
        count = len(self.__addresses_and_row_lengths)
        entry["count"] = count
        entry["core_mask"] = self._core_mask
        entry["n_neurons_and_core_shift"] = (
            (self._n_neurons << _N_NEURONS_SHIFT) | self._core_shift)
        for j, (address, row_length, is_single, is_valid) in enumerate(
                self.__addresses_and_row_lengths):
            if not is_valid:
                address_list[start + j] = _INVALID_ADDDRESS_AND_ROW_LENGTH
            else:
                single_bit = _SINGLE_BIT_FLAG_BIT if is_single else 0
                address_list[start + j] = (
                    single_bit |
                    ((address & _ADDRESS_MASK) << _ADDRESS_SHIFT) |
                    (row_length & _ROW_LENGTH_MASK))
        return count


class MasterPopTableAsBinarySearch(AbstractMasterPopTableFactory):
    """ Master population table, implemented as binary search master.
    """
    __slots__ = [
        "__entries",
        "__n_addresses",
        "__n_single_entries"]

    def __init__(self):
        self.__entries = None
        self.__n_addresses = 0
        self.__n_single_entries = None

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
            (n_vertices * 2 * _MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * 2 * _ADDRESS_LIST_ENTRY_SIZE_BYTES) +
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
            (n_vertices * 2 * _MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * 2 * _ADDRESS_LIST_ENTRY_SIZE_BYTES) +
            8)

    def get_allowed_row_length(self, row_length):
        """
        :param row_length: the row length being considered
        :return: the row length available
        """
        if (row_length - 1) & _ROW_LENGTH_MASK != (row_length - 1):
            raise SynapseRowTooBigException(
                256, "Only rows of up to 256 entries are allowed")
        return row_length

    def get_next_allowed_address(self, next_address):
        """
        :param next_address: The next address that would be used
        :return: The next address that can be used following next_address
        """
        addr_scaled = (next_address + (_ADDRESS_SCALE - 1)) // _ADDRESS_SCALE
        if addr_scaled > 0x7FFFFF:
            raise SynapticConfigurationException(
                "Address {} is out of range for this population table!".format(
                    hex(next_address)))
        return addr_scaled * _ADDRESS_SCALE

    def initialise_table(self, spec, master_population_table_region):
        """ Initialise the master pop data structure

        :param spec: the DSG writer
        :param master_population_table_region: \
            the region in memory that the master pop table will be written in
        :rtype: None
        """
        self.__entries = dict()
        self.__n_addresses = 0
        self.__n_single_entries = 0

    @overrides(AbstractMasterPopTableFactory.update_master_population_table)
    def update_master_population_table(
            self, spec, block_start_addr, row_length, key_and_mask,
            core_mask, core_shift, n_neurons,
            master_pop_table_region, is_single=False):
        # pylint: disable=too-many-arguments
        if key_and_mask.key not in self.__entries:
            self.__entries[key_and_mask.key] = _MasterPopEntry(
                key_and_mask.key, key_and_mask.mask, core_mask, core_shift,
                n_neurons)

        # if not single, scale the address
        start_addr = block_start_addr
        if not is_single:
            if block_start_addr % _ADDRESS_SCALE != 0:
                raise SynapticConfigurationException(
                    "Address {} is not compatible with this table",
                    block_start_addr)
            start_addr = block_start_addr // _ADDRESS_SCALE
            if start_addr & _ADDRESS_MASK != start_addr:
                raise SynapticConfigurationException(
                    "Address {} is too big for this table", block_start_addr)
        if (row_length - 1) & _ROW_LENGTH_MASK != (row_length - 1):
            raise SynapticConfigurationException(
                "Row length {} is outside of allowed range for this table",
                row_length)
        index = self.__entries[key_and_mask.key].append(
            start_addr, row_length - 1, is_single)
        self.__n_addresses += 1

        return index

    @overrides(AbstractMasterPopTableFactory.add_invalid_entry)
    def add_invalid_entry(
            self, spec, key_and_mask, core_mask, core_shift, n_neurons,
            master_pop_table_region):
        if key_and_mask.key not in self.__entries:
            self.__entries[key_and_mask.key] = _MasterPopEntry(
                key_and_mask.key, key_and_mask.mask, core_mask, core_shift,
                n_neurons)
        index = self.__entries[key_and_mask.key].append_invalid()
        self.__n_addresses += 1

        return index

    @overrides(AbstractMasterPopTableFactory.finish_master_pop_table)
    def finish_master_pop_table(self, spec, master_pop_table_region):
        spec.switch_write_focus(region=master_pop_table_region)

        # sort entries by key
        entries = sorted(
            self.__entries.values(),
            key=lambda entry: entry.routing_key)

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
            table_entry = pop_table[i]
            start += entry.write_to_table(table_entry, address_list, start)

        # Write the arrays
        spec.write_array(pop_table.view("<u4"))
        spec.write_array(address_list)

        self.__entries.clear()
        del self.__entries
        self.__entries = None
        self.__n_addresses = 0

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
            n_entries * _MASTER_POP_ENTRY_SIZE_BYTES)
        n_address_bytes = (
            n_addresses * _ADDRESS_LIST_ENTRY_SIZE_BYTES)

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
            if address_and_row_length == _INVALID_ADDDRESS_AND_ROW_LENGTH:
                addresses.append((0, 0, 0))
            else:
                is_single = (address_and_row_length & _SINGLE_BIT_FLAG_BIT) > 0
                address = address_and_row_length & _ADDRESS_MASK_SHIFTED
                row_length = (address_and_row_length & _ROW_LENGTH_MASK)
                if is_single:
                    address = address >> _ADDRESS_SHIFT
                else:
                    address = address >> _ADDRESS_SCALED_SHIFT

                addresses.append((row_length + 1, address, is_single))
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
