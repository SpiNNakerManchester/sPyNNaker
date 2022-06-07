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
import math
import numpy
import ctypes
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.exceptions import (
    SynapseRowTooBigException, SynapticConfigurationException)
from spynnaker.pyNN.utilities.constants import POP_TABLE_MAX_ROW_LENGTH
from spynnaker.pyNN.utilities.bit_field_utilities import BIT_IN_A_WORD

# Scale factor for an address; allows more addresses to be represented, but
# means addresses have to be aligned to these offsets
_ADDRESS_SCALE = 16

# A padding byte
_PADDING_BYTE = 0xDD

# Bits in a byte
_BITS_PER_BYTES = 8

# ctypes stores the number of bits in a bitfield in the top 16 bits
_CTYPES_N_BITS_SHIFT = 16


def _n_bits(field):
    """ Get the number of bits in a field (ctypes doesn't do this)

    :param _ctypes.CField field: a ctype field from a structure
    :return: the number of bits
    :rtype: int
    """
    # ctypes stores the number of bits in a bitfield in the top 16 bits;
    # if it isn't a bitfield, this is 0
    n_bits = field.size >> _CTYPES_N_BITS_SHIFT
    if n_bits:
        return n_bits

    # If it isn't a bitfield, the number of bits is the field size (which is
    # then in bytes) multiplied by 8 (bits in a byte)
    return _BITS_PER_BYTES * field.size


def _make_array(ctype, n_items):
    """ Make an array of ctype items; done separately as the syntax is a
        little odd!

    :param _ctypes.PyCSimpleType ctype: A ctype
    :param int n_items: The number of items in the array
    :return: a ctype array
    :rtype: _ctypes.PyCArrayType
    """
    array_type = ctype * n_items
    return array_type()


class _MasterPopEntryCType(ctypes.LittleEndianStructure):
    """ A Master Population Table Entry; matches the C struct
    """
    _fields_ = [
        # The key to match against the incoming message
        ("key", ctypes.c_uint32),
        # The mask to select the relevant bits of key for matching
        ("mask", ctypes.c_uint32),
        # The index into address_list for this entry
        ("start", ctypes.c_uint32, 15),
        # Flag to indicate if an extra_info struct is present
        ("extra_info_flag", ctypes.c_uint32, 1),
        # The number of entries in ::address_list for this entry
        ("count", ctypes.c_uint32, 16),
        # The mask to apply to the key once shifted get the core index
        ("core_mask", ctypes.c_uint32, 16),
        # The shift to apply to the key to get the core part (0-31)
        ("mask_shift", ctypes.c_uint32, 16),
        # The number of neurons per core (up to 2048)
        ("n_neurons", ctypes.c_uint32, 16),
        # The number of words required for n_neurons
        ("n_words", ctypes.c_uint32, 16)
    ]


# Maximum start position in the address list
_MAX_ADDRESS_START = (1 << _n_bits(_MasterPopEntryCType.start)) - 1
# Maximum count of address list entries for a single pop table entry
_MAX_ADDRESS_COUNT = (1 << _n_bits(_MasterPopEntryCType.count)) - 1

# The maximum n_neurons value
_MAX_N_NEURONS = (1 << _n_bits(_MasterPopEntryCType.n_neurons)) - 1
# Maximum core mask (i.e. number of cores)
_MAX_CORE_MASK = (1 << _n_bits(_MasterPopEntryCType.core_mask)) - 1


class _AddressListEntryCType(ctypes.LittleEndianStructure):
    """ An Address and Row Length structure; matches the C struct
    """
    _fields_ = [
        # the length of the row
        ("row_length", ctypes.c_uint32, 8),
        # the address
        ("address", ctypes.c_uint32, 24)
    ]


# An invalid address in the address and row length list
_INVALID_ADDDRESS = (1 << _n_bits(_AddressListEntryCType.address)) - 1
# Address is 23 bits, but maximum value means invalid
_MAX_ADDRESS = (1 << _n_bits(_AddressListEntryCType.address)) - 2

# Sizes of structs
_MASTER_POP_ENTRY_SIZE_BYTES = ctypes.sizeof(_MasterPopEntryCType)
_ADDRESS_LIST_ENTRY_SIZE_BYTES = ctypes.sizeof(_AddressListEntryCType)

# Base size - 2 words for size of table and address list
_BASE_SIZE_BYTES = 8

# Number of times to multiply for delays
_DELAY_SCALE = 2

# A ctypes pointer to a uint32
_UINT32_PTR = ctypes.POINTER(ctypes.c_uint32)


def _to_numpy(array):
    """ Convert a ctypes array to a numpy array of uint32

    Note: no data copying is done; it is pure type conversion.  Editing
    the returned array will result in changes to the original.

    :param _ctypes.PyCArrayType array: The array to convert
    :rtype: numpy.ndarray
    """
    # Nothing to do if the array is 0 sized
    if not len(array):
        return numpy.zeros(0, dtype="uint32")

    uint32_array = ctypes.cast(array, _UINT32_PTR)
    n_words = (len(array) * ctypes.sizeof(array[0])) // BYTES_PER_WORD
    return numpy.ctypeslib.as_array(uint32_array, (n_words,))


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
        """
        :param int routing_key: The key to match for this entry
        :param int mask: The mask to match for this entry
        :param int core_mask:
            The part of the routing_key where the core id is held
        :param int core_shift: Where in the routing_key the core_id is held
        :param int n_neurons:
            The number of neurons on each core, except the last
        """
        self.__routing_key = routing_key
        self.__mask = mask
        self.__core_mask = core_mask
        self.__core_shift = core_shift
        self.__n_neurons = n_neurons
        self.__addresses_and_row_lengths = list()

    def append(self, address, row_length):
        """ Add a synaptic matrix pointer to the entry

        :param int address: The address of the synaptic matrix
        :param int row_length: The length of each row in the matrix
        :return: The index of the pointer within the entry
        :rtype: int
        """
        index = len(self.__addresses_and_row_lengths)
        if index > _MAX_ADDRESS_COUNT:
            raise SynapticConfigurationException(
                "{} connections for the same source key (maximum {})".format(
                    index, _MAX_ADDRESS_COUNT))
        self.__addresses_and_row_lengths.append(
            (address, row_length, True))
        return index

    def append_invalid(self):
        """ Add an invalid marker to the entry; used to ensure index alignment
            between multiple entries when necessary

        :return: The index of the marker within the entry
        :rtype: int
        """
        index = len(self.__addresses_and_row_lengths)
        self.__addresses_and_row_lengths.append((0, 0, False))
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
        :return: the mask of the key for this entry
        :rtype: int
        """
        return self.__mask

    @property
    def core_mask(self):
        """
        :return: the mask of the key once shifted to get the source core ID
        :rtype: int
        """
        return self.__core_mask

    @property
    def core_shift(self):
        """
        :return: the shift of the key to get the source core ID
        :rtype: int
        """
        return self.__core_shift

    @property
    def n_neurons(self):
        """
        :return: the number of neurons per source core
        :rtype: int
        """
        return self.__n_neurons

    @property
    def addresses_and_row_lengths(self):
        """
        :return: the memory address that this master pop entry points at
            (synaptic matrix)
        :rtype: list(tuple(int,int,bool,bool))
        """
        return self.__addresses_and_row_lengths

    def write_to_table(self, entry, address_list, start):
        """ Write entries to the master population table

        :param _MasterPopEntryCType entry: The entry to write to
        :param _AddressListEntryCType_Array address_list:
            The address_list to write to
        :param int start:
            The index of the entry of the address list to start at
        :return: The number of entries written to the address list
        :rtype: int
        """
        entry.key = self.__routing_key
        entry.mask = self.__mask
        entry.start = start
        count = len(self.__addresses_and_row_lengths)
        entry.count = count

        # Mark where the next entry starts and the number added; this might
        # change if there is extra info
        next_addr = start
        n_entries = count

        # If there is a core mask, add a special entry for it
        if self.__core_mask != 0:
            entry.extra_info_flag = True
            entry.core_mask = self.__core_mask
            entry.n_words = int(math.ceil(
                self.__n_neurons / BIT_IN_A_WORD))
            entry.n_neurons = self.__n_neurons
            entry.mask_shift = self.__core_shift
        else:
            entry.extra_info_flag = False
            entry.core_mask = 0
            entry.n_words = 0
            entry.n_neurons = 0
            entry.mask_shift = 0

        for j, (address, row_length, is_valid) in enumerate(
                self.__addresses_and_row_lengths):
            address_entry = address_list[next_addr + j]
            if not is_valid:
                address_entry.address = _INVALID_ADDDRESS
            else:
                address_entry.row_length = row_length
                address_entry.address = address
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
    def get_master_population_table_size(incoming_projections):
        """ Get the size of the master population table in SDRAM.

        :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
            The projections arriving at the vertex that are to be handled by
            this table
        :return: the size the master pop table will take in SDRAM (in bytes)
        :rtype: int
        """
        # There will be an address list entry for each incoming projection
        n_entries = len(incoming_projections)

        # Count the pre-machine-vertices
        n_vertices = 0
        seen_edges = set()
        for proj in incoming_projections:
            # pylint: disable=protected-access
            in_edge = proj._projection_edge

            # Each projection with a delay will have an additional entry
            if in_edge.n_delay_stages:
                n_entries += 1

            # If we haven't seen this edge before, add it in
            if in_edge not in seen_edges:
                seen_edges.add(in_edge)
                # Each pre-vertex has a master pop entry
                n_vertices += 1
                if in_edge.n_delay_stages:
                    n_vertices += 1

        return (
            _BASE_SIZE_BYTES +
            (n_vertices * _MASTER_POP_ENTRY_SIZE_BYTES) +
            (n_entries * _ADDRESS_LIST_ENTRY_SIZE_BYTES))

    @staticmethod
    def get_allowed_row_length(row_length):
        """ Get the next allowed row length

        :param int row_length: the row length being considered
        :return: the row length available
        :rtype: int
        :raises SynapseRowTooBigException: If the row won't fit
        """

        if row_length > POP_TABLE_MAX_ROW_LENGTH:
            raise SynapseRowTooBigException(
                POP_TABLE_MAX_ROW_LENGTH,
                "Only rows of up to {} entries are allowed".format(
                    POP_TABLE_MAX_ROW_LENGTH))
        return row_length

    @staticmethod
    def get_next_allowed_address(next_address):
        """ Get the next allowed address.

        :param int next_address: The next address that would be used
        :return: The next address that can be used following next_address
        :rtype: int
        :raises ~spynnaker.pyNN.exceptions.SynapticConfigurationException:
            if the address is out of range
        """
        addr_scaled = (next_address + (_ADDRESS_SCALE - 1)) // _ADDRESS_SCALE
        if addr_scaled > _MAX_ADDRESS:
            raise SynapticConfigurationException(
                "Address {} is out of range for this population table!".format(
                    hex(addr_scaled * _ADDRESS_SCALE)))
        return addr_scaled * _ADDRESS_SCALE

    def initialise_table(self):
        """ Initialise the master pop data structure.
        """
        self.__entries = dict()
        self.__n_addresses = 0

    def add_application_entry(
            self, block_start_addr, row_length, key_and_mask, core_mask,
            core_shift, n_neurons):
        """ Add an entry for an application-edge to the population table.

        :param int block_start_addr: where the synaptic matrix block starts
        :param int row_length: how long in words each row is
        :param ~pacman.model.routing_info.BaseKeyAndMask key_and_mask:
            the key and mask for this master pop entry
        :param int core_mask:
            Mask for the part of the key that identifies the core
        :param int core_shift: The shift of the mask to get to the core_mask
        :param int n_neurons:
            The number of neurons in each machine vertex (bar the last)
        :return: The index of the entry, to be used to retrieve it
        :rtype: int
        :raises ~spynnaker.pyNN.exceptions.SynapticConfigurationException:
            If a bad address is used.
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

        return self.__update_master_population_table(
            block_start_addr, row_length, key_and_mask, core_mask, core_shift,
            n_neurons)

    def __update_master_population_table(
            self, block_start_addr, row_length, key_and_mask, core_mask,
            core_shift, n_neurons):
        """ Add an entry in the binary search to deal with the synaptic matrix

        :param int block_start_addr: where the synaptic matrix block starts
        :param int row_length: how long in words each row is
        :param ~pacman.model.routing_info.BaseKeyAndMask key_and_mask:
            the key and mask for this master pop entry
        :param int core_mask:
            Mask for the part of the key that identifies the core
        :param int core_shift: The shift of the mask to get to the core_mask
        :param int n_neurons:
            The number of neurons in each machine vertex (bar the last)
        :return: The index of the entry, to be used to retrieve it
        :rtype: int
        :raises ~spynnaker.pyNN.exceptions.SynapticConfigurationException:
            If a bad address is used.
        """
        # if not single, scale the address
        if block_start_addr % _ADDRESS_SCALE != 0:
            raise SynapticConfigurationException(
                "Address {} is not compatible with this table".format(
                    block_start_addr))
        start_addr = block_start_addr // _ADDRESS_SCALE
        if start_addr > _MAX_ADDRESS:
            raise SynapticConfigurationException(
                "Address {} is too big for this table".format(
                    block_start_addr))
        row_length = self.get_allowed_row_length(row_length)

        entry = self.__add_entry(
            key_and_mask, core_mask, core_shift, n_neurons)
        index = entry.append(start_addr, row_length - 1)
        self.__n_addresses += 1
        return index

    def add_invalid_application_entry(
            self, key_and_mask, core_mask=0, core_shift=0, n_neurons=0):
        """ Add an entry to the table from an application vertex that doesn't
            point to anywhere.  Used to keep indices in synchronisation between
            e.g. normal and delay entries and between entries on different
            cores.

        :param ~pacman.model.routing_info.BaseKeyAndMask key_and_mask:
            a key_and_mask object used as part of describing
            an edge that will require being received to be stored in the
            master pop table; the whole edge will become multiple calls to
            this function
        :param int core_mask:
            Mask for the part of the key that identifies the core
        :param int core_shift: The shift of the mask to get to the core_mask
        :param int n_neurons:
            The number of neurons in each machine vertex (bar the last)
        :return: The index of the added entry
        :rtype: int
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
        return self.__add_invalid_entry(
            key_and_mask, core_mask, core_shift, n_neurons)

    def __add_invalid_entry(
            self, key_and_mask, core_mask, core_shift, n_neurons):
        """ Add an entry to the table that doesn't point to anywhere.  Used
            to keep indices in synchronisation between e.g. normal and delay
            entries and between entries on different cores.

        :param ~pacman.model.routing_info.BaseKeyAndMask key_and_mask:
            a key_and_mask object used as part of describing
            an edge that will require being received to be stored in the
            master pop table; the whole edge will become multiple calls to
            this function
        :param int core_mask:
            Mask for the part of the key that identifies the core
        :param int core_shift: The shift of the mask to get to the core_mask
        :param int n_neurons:
            The number of neurons in each machine vertex (bar the last)
        :return: The index of the added entry
        :rtype: int
        """
        entry = self.__add_entry(
            key_and_mask, core_mask, core_shift, n_neurons)
        index = entry.append_invalid()
        self.__n_addresses += 1
        return index

    def __add_entry(self, key_and_mask, core_mask, core_shift, n_neurons):
        if self.__n_addresses >= _MAX_ADDRESS_START:
            raise SynapticConfigurationException(
                "The table already contains {} entries;"
                " adding another is too many".format(self.__n_addresses))
        if key_and_mask.key not in self.__entries:
            entry = _MasterPopEntry(
                key_and_mask.key, key_and_mask.mask, core_mask, core_shift,
                n_neurons)
            self.__entries[key_and_mask.key] = entry
            return entry
        entry = self.__entries[key_and_mask.key]
        if (key_and_mask.mask != entry.mask or
                core_mask != entry.core_mask or
                core_shift != entry.core_shift or
                n_neurons != entry.n_neurons):
            raise SynapticConfigurationException(
                "Existing entry for key {} doesn't match one being added:"
                " Existing mask: {} core_mask: {} core_shift: {}"
                " n_neurons: {}"
                " Adding mask: {} core_mask: {} core_shift: {}"
                " n_neurons: {}".format(
                    key_and_mask.key, entry.mask, entry.core_mask,
                    entry.core_shift, entry.n_neurons, key_and_mask.mask,
                    core_mask, core_shift, n_neurons))
        return entry

    def get_pop_table_data(self):
        """ Get the master pop table data as a numpy array

        :rtype: ~numpy.ndarray
        """
        # sort entries by key
        entries = sorted(
            self.__entries.values(),
            key=lambda a_entry: a_entry.routing_key)
        n_entries = len(entries)
        data = [numpy.array([n_entries, self.__n_addresses], dtype="uint32")]
        # Generate the table and list as arrays
        pop_table = _make_array(_MasterPopEntryCType, n_entries)
        address_list = _make_array(_AddressListEntryCType, self.__n_addresses)
        start = 0
        for i, entry in enumerate(entries):
            start += entry.write_to_table(pop_table[i], address_list, start)

        # Add the arrays
        data.append(_to_numpy(pop_table))
        data.append(_to_numpy(address_list))
        return numpy.concatenate(data)

    @property
    def max_n_neurons_per_core(self):
        """ The maximum number of neurons per core supported when a core-mask\
            is > 0.

        :rtype: int
        """
        return _MAX_N_NEURONS

    @property
    def max_core_mask(self):
        """ The maximum core mask supported when n_neurons is > 0; this is the\
            maximum number of cores that can be supported in a joined mask.

        :rtype: int
        """
        return _MAX_CORE_MASK

    @property
    def max_index(self):
        """ The maximum index of a synaptic connection

        :rtype: int
        """
        return _MAX_ADDRESS_COUNT
