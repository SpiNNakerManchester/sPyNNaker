
# pacman imports
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_field_constraint import \
    KeyAllocatorFixedFieldConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_mask_constraint import KeyAllocatorFixedMaskConstraint
from pacman.utilities.utility_objs.field import Field

# spynnaker imports
from spynnaker.pyNN.models.neuron.master_pop_table_generators.\
    abstract_master_pop_table_factory import AbstractMasterPopTableFactory
from spynnaker.pyNN import exceptions

# spinn front end common imports
from spinn_front_end_common.utilities import helpful_functions

# dsg imports
from data_specification.enums.data_type import DataType


# general imports
import logging
import math


logger = logging.getLogger(__name__)

# Fixed row sizes allowed in this table
ROW_LEN_TABLE_ENTRIES = [0, 1, 8, 16, 32, 64, 128, 256]
ROW_LEN_TABLE_SIZE = 4 * len(ROW_LEN_TABLE_ENTRIES)

# Table size is fixed to 8 x 8 board size
X_CHIPS = 8
Y_CHIPS = 8
CORES_PER_CHIP = 18
MASTER_POPULATION_ENTRIES = (X_CHIPS * Y_CHIPS * CORES_PER_CHIP)


def get_x_from_key(key):
    """

    :param key:
    :return:
    """
    return key >> 24


def get_y_from_key(key):
    """

    :param key:
    :return:
    """
    return (key >> 16) & 0xFF


def get_p_from_key(key):
    """

    :param key:
    :return:
    """
    return (key >> 11) & 0x1F


def get_nid_from_key(key):
    """

    :param key:
    :return:
    """
    return key & 0x7FF


def get_key_from_coords(chipX, chipY, chipP):
    """

    :param chipX:
    :param chipY:
    :param chipP:
    :return:
    """
    return chipX << 24 | chipY << 16 | chipP << 11


def get_mpt_sb_mem_addrs_from_coords(x, y, p):
    """

    :param x:
    :param y:
    :param p:
    :return:
    """
    # two bytes per entry
    return (p + (18 * y) + (18 * 8 * x)) * 2


class MasterPopTableAs2dArray(AbstractMasterPopTableFactory):

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)

    def initialise_table(self, spec, master_population_table_region):
        """

        :param spec:
        :param master_population_table_region:
        :return:
        """
        # Zero all entries in the Master Population Table so that all unused
        # entries are assumed empty:
        spec.switch_write_focus(region=master_population_table_region)
        my_repeat_reg = 4
        spec.set_register_value(register_id=my_repeat_reg,
                                data=MASTER_POPULATION_ENTRIES)
        spec.write_value(data=0, repeats_register=my_repeat_reg,
                         data_type=DataType.UINT16)

        spec.comment("\nWriting Row Length Translation Table:\n")
        for entry in ROW_LEN_TABLE_ENTRIES:
            spec.write_value(data=entry)

    def extract_synaptic_matrix_data_location(
            self, incoming_key, master_pop_base_mem_address, txrx, chip_x,
            chip_y):
        """

        :param incoming_key:
        :param master_pop_base_mem_address:
        :param txrx:
        :param chip_x:
        :param chip_y:
        :return:
        """

        # locate address of the synaptic block
        pre_x = get_x_from_key(incoming_key)
        pre_y = get_y_from_key(incoming_key)
        pre_p = get_p_from_key(incoming_key)
        table_slot_addr = self._get_table_address_from_coords(
            pre_x, pre_y, pre_p)
        master_table_pop_entry_address = (table_slot_addr +
                                          master_pop_base_mem_address)

        # read in entry
        master_pop_entry = helpful_functions.read_data(
            chip_x, chip_y, master_table_pop_entry_address, 2, "<H", txrx)

        synaptic_block_base_address = master_pop_entry >> 3  # in kilobytes

        # convert synaptic_block_base_address into bytes from kilobytes
        synaptic_block_base_address_offset = synaptic_block_base_address << 10
        max_row_length_index = master_pop_entry & 0x7

        # retrieve the max row length
        max_row_length = ROW_LEN_TABLE_ENTRIES[max_row_length_index]
        return [(max_row_length, synaptic_block_base_address_offset)]

    def get_master_population_table_size(self, vertex_slice, in_edges):
        """

        :param vertex_slice:
        :param in_edges:
        :return:
        """
        # 2 bytes per entry + row length table
        return (2 * MASTER_POPULATION_ENTRIES) + ROW_LEN_TABLE_SIZE

    def get_allowed_row_length(self, row_length):
        """

        :param row_length:
        :return:
        """

        # Can even the largest valid entry accommodate the given synaptic row?
        if row_length > ROW_LEN_TABLE_ENTRIES[-1]:
            raise exceptions.SynapticBlockGenerationException(
                "Max row length too long -"
                " wanted length %d, but max length permitted is %d."
                % (row_length, ROW_LEN_TABLE_ENTRIES[-1])
            )

        # Search up the list until we find one entry big enough:
        for i in range(len(ROW_LEN_TABLE_ENTRIES)):
            if row_length <= ROW_LEN_TABLE_ENTRIES[i]:

                # This row length is big enough. Choose it and exit:
                return ROW_LEN_TABLE_ENTRIES[i]
        raise Exception("Should not get here!")

    def _get_row_length_table_index(self, row_length):
        """

        :param row_length:
        :return:
        """
        for i in range(len(ROW_LEN_TABLE_ENTRIES)):
            if row_length <= ROW_LEN_TABLE_ENTRIES[i]:
                return i
        raise Exception("Should not get here!")

    def get_next_allowed_address(self, next_address):
        """

        :param next_address:
        :return:
        """

        # Addresses should be 1K offset
        if (next_address & 0x3FF) != 0:

            return (next_address & 0xFFFFFC00) + 0x400
        return next_address

    def _get_table_address_from_coords(self, x, y, p):
        """

        :param x:
        :param y:
        :param p:
        :return:
        """
        return (p + (18 * y) + (18 * 8 * x)) * 2

    def update_master_population_table(
            self, spec, block_start_addr, row_length, keys_and_masks,
            master_pop_table_region, is_single=False):
        """
        Writes an entry in the Master Population Table for the newly
        created synaptic block.
        An entry in the table is a 16-bit value, with the following structure:
        Bits [2:0]  Row length information. This value (from 0->7)
                    indicates the maximum number of synapses in this
                    block. It is translated in the row length translation
                    table by the executing code each time the table is
                    accessed, to calculate offsets.
        Bits [15:3] Address within the synaptic matrix region of the
                    start of the block. This is 1K bytes aligned, so
                    the true value is found by shifting left by 7 bits
                    then adding the start address of the memory region.
        :param spec:
        :param block_start_addr:
        :param row_length:
        :param keys_and_masks:
        :param mask:
        :param master_pop_table_region:
        :param is_single True if this is a single synapse, False otherwise
        :return:
        """
        # Which core has this projection arrived from?
        key = keys_and_masks[0].key
        x = get_x_from_key(key)
        y = get_y_from_key(key)
        p = get_p_from_key(key)

        # Calculate the index into the master pynn_population.py table for
        # a projection from the given core:
        table_slot_addr = self._get_table_address_from_coords(x, y, p)
        row_index = self._get_row_length_table_index(row_length)

        # What is the write address in the table for this index?
        spec.comment("\nUpdate entry in master pynn_population.py table for "
                     "incoming connection from {}, {}, {}:\n".format(x, y, p))

        # Process start address (align to 1K boundary then shift right by 10
        # and left by 3 (i.e. 7) to make it the top 13-bits of the field):
        if (block_start_addr & 0x3FF) != 0:
            raise exceptions.SynapticBlockGenerationException(
                "Synaptic Block start address is not aligned to a 1K boundary")
        assert(block_start_addr < math.pow(2, 32))

        # moves by 7 to tack on at the end the row_length information
        # which resides in the last 3 bits
        entry_addr_field = block_start_addr >> 7

        # Assembly entry:
        new_entry = entry_addr_field | row_index

        # Write entry:
        spec.switch_write_focus(region=master_pop_table_region)
        spec.set_write_pointer(address=table_slot_addr)
        spec.write_value(data=new_entry, data_type=DataType.INT16)

    def finish_master_pop_table(self, spec, master_pop_table_region):
        """

        :param spec:
        :param master_pop_table_region:
        :return:
        """
        pass

    def get_edge_constraints(self):
        """

        :return:
        """

        # This allocator requires each edge to have keys of the form
        # |8 bits >= 0 and <= 7|8 bits >= 0 and <= 7|5 bits >= 0 and <= 17|
        # |11 remaining bits|
        # This is because this table was designed for a 48-chip board
        constraints = list()
        fields = list()
        fields.append(Field(0, 7, 0xFF000000))
        fields.append(Field(0, 7, 0x00FF0000))
        fields.append(Field(0, 17, 0x0000F800))
        constraints.append(KeyAllocatorFixedMaskConstraint(0xFFFFF800))
        constraints.append(KeyAllocatorFixedFieldConstraint(fields))
        return constraints
