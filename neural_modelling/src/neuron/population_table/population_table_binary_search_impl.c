#include "population_table.h"
#include "../synapse_row.h"
#include <debug.h>
#include <string.h>

typedef struct master_population_table_entry {
    uint32_t key;
    uint32_t mask;
    uint16_t start;
    uint16_t count;
} master_population_table_entry;

typedef uint32_t address_and_row_length;

static master_population_table_entry *master_population_table;
static uint32_t master_population_table_length;
static address_and_row_length *address_list;
static address_t synaptic_rows_base_address;
static address_t direct_rows_base_address;

static uint32_t last_neuron_id = 0;
static uint16_t next_item = 0;
static uint16_t items_to_go = 0;

static inline uint32_t _get_direct_address(address_and_row_length entry) {

    // Direct row address is just the direct address bit
    return (entry & 0x7FFFFF00) >> 8;
}

static inline uint32_t _get_address(address_and_row_length entry) {

    // The address is in words and is the top 23-bits but 1, so this down
    // shifts by 8 and then multiplies by 4 (= up shifts by 2) = down shift by 6
    // with the given mask 0x7FFFFF00 to fully remove the row length
    // NOTE: The mask can be removed given the machine spec says it
    // hard-codes the bottom 2 bits to zero anyhow. BUT BAD CODE PRACTICE
    return (entry & 0x7FFFFF00) >> 6;
}

static inline uint32_t _get_row_length(address_and_row_length entry) {
    return entry & 0xFF;
}

static inline uint32_t _is_single(address_and_row_length entry) {
    return entry & 0x80000000;
}

static inline uint32_t _get_neuron_id(
        master_population_table_entry entry, spike_t spike) {
    return spike & ~entry.mask;
}

static inline void _print_master_population_table() {
    log_info("master_population\n");
    log_info("------------------------------------------\n");
    for (uint32_t i = 0; i < master_population_table_length; i++) {
        master_population_table_entry entry = master_population_table[i];
        for (uint16_t j = entry.start; j < (entry.start + entry.count); j++) {
            log_info(
                "index (%d, %d), key: 0x%.8x, mask: 0x%.8x, address: 0x%.8x,"
                " row_length: %u\n", i, j, entry.key, entry.mask,
                _get_address(address_list[j]),
                _get_row_length(address_list[j]));
        }
    }
    log_info("------------------------------------------\n");
}

bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        address_t direct_rows_address, uint32_t *row_max_n_words) {
    log_info("population_table_initialise: starting");

    master_population_table_length = table_address[0];
    log_info("master pop table length is %d\n", master_population_table_length);
    log_info(
        "master pop table entry size is %d\n",
        sizeof(master_population_table_entry));
    uint32_t n_master_pop_bytes =
        master_population_table_length * sizeof(master_population_table_entry);
    uint32_t n_master_pop_words = n_master_pop_bytes >> 2;
    log_info("pop table size is %d\n", n_master_pop_bytes);

    // only try to malloc if there's stuff to malloc.
    if (n_master_pop_bytes != 0){
        master_population_table = (master_population_table_entry *)
            spin1_malloc(n_master_pop_bytes);
        if (master_population_table == NULL) {
            log_error("Could not allocate master population table");
            return false;
        }
    }

    uint32_t address_list_length = table_address[1];
    uint32_t n_address_list_bytes =
        address_list_length * sizeof(address_and_row_length);

    // only try to malloc if there's stuff to malloc.
    if (n_address_list_bytes != 0){
        address_list = (address_and_row_length *)
            spin1_malloc(n_address_list_bytes);
        if (address_list == NULL) {
            log_error("Could not allocate master population address list");
            return false;
        }
    }

    log_info(
        "pop table size: %u (%u bytes)", master_population_table_length,
        n_master_pop_bytes);
    log_info(
        "address list size: %u (%u bytes)", address_list_length,
        n_address_list_bytes);

    // Copy the master population table
    memcpy(master_population_table, &(table_address[2]), n_master_pop_bytes);
    memcpy(
        address_list, &(table_address[2 + n_master_pop_words]),
        n_address_list_bytes);

    // Store the base address
    log_info(
        "the stored synaptic matrix base address is located at: 0x%08x",
        synapse_rows_address);
    log_info(
        "the direct synaptic matrix base address is located at: 0x%08x",
        direct_rows_address);
    synaptic_rows_base_address = synapse_rows_address;
    direct_rows_base_address = direct_rows_address;

    *row_max_n_words = 0xFF + N_SYNAPSE_ROW_HEADER_WORDS;

    _print_master_population_table();
    return true;
}

bool population_table_get_first_address(
        spike_t spike, address_t* row_address, size_t* n_bytes_to_transfer) {
    uint32_t imin = 0;
    uint32_t imax = master_population_table_length;

    while (imin < imax) {

        int imid = (imax + imin) >> 1;
        master_population_table_entry entry = master_population_table[imid];
        if ((spike & entry.mask) == entry.key) {
            if (entry.count == 0) {
                log_debug(
                    "spike %u (= %x): population found in master population"
                    "table but count is 0");
            }

            last_neuron_id = _get_neuron_id(entry, spike);
            next_item = entry.start;
            items_to_go = entry.count;

            log_debug(
                "spike = %08x, entry_index = %u, start = %u, count = %u",
                spike, imid, next_item, items_to_go);

            return population_table_get_next_address(
                row_address, n_bytes_to_transfer);
        } else if (entry.key < spike) {

            // Entry must be in upper part of the table
            imin = imid + 1;
        } else {

            // Entry must be in lower part of the table
            imax = imid;
        }
    }
    log_debug(
        "spike %u (= %x): population not found in master population table",
        spike, spike);
    return false;
}

bool population_table_get_next_address(
        address_t* row_address, size_t* n_bytes_to_transfer) {

    // If there are no more items in the list, return false
    if (items_to_go <= 0) {
        return false;
    }

    address_and_row_length item = address_list[next_item];

    // If the row is a direct row, indicate this by specifying the
    // n_bytes_to_transfer is 0
    if (_is_single(item)) {
        *row_address = (address_t) (
            _get_direct_address(item) + (uint32_t) direct_rows_base_address +
            (last_neuron_id * sizeof(uint32_t)));
        *n_bytes_to_transfer = 0;
    } else {

        uint32_t block_address =
            _get_address(item) + (uint32_t) synaptic_rows_base_address;
        uint32_t row_length = _get_row_length(item);
        uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);
        uint32_t neuron_offset = last_neuron_id * stride * sizeof(uint32_t);

        *row_address = (address_t) (block_address + neuron_offset);
        *n_bytes_to_transfer = stride * sizeof(uint32_t);
        log_debug("neuron_id = %u, block_address = 0x%.8x,"
                  "row_length = %u, row_address = 0x%.8x, n_bytes = %u",
                  last_neuron_id, block_address, row_length, *row_address,
                  *n_bytes_to_transfer);
    }

    next_item += 1;
    items_to_go -= 1;

    return true;
}
