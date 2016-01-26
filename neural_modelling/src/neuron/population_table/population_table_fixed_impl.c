#include "population_table.h"
#include "../synapse_row.h"
#include <debug.h>
#include <string.h>

#define MASTER_POPULATION_MAX 1152
#define ROW_SIZE_TABLE_MAX 8

static uint16_t master_population_table[MASTER_POPULATION_MAX];
static address_t synaptic_rows_base_address;
static uint32_t row_size_table[ROW_SIZE_TABLE_MAX];

static inline void _print_master_population_table() {
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("master_population\n");
    log_debug("------------------------------------------\n");
    for (uint32_t i = 0; i < MASTER_POPULATION_MAX; i++) {
        uint32_t entry = (uint32_t) (master_population_table[i]);
        uint32_t row_table_entry = entry & 0x7;
        if (row_table_entry != 0) {
            log_debug("index %d, entry: %4u (13 bits = %04x), size = %3u\n",
                      i, entry, entry >> 3, row_size_table[row_table_entry]);
        }
    }
    log_debug("------------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}

static inline void _print_row_size_table() {
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("row_size_table\n");
    log_debug("------------------------------------------\n");
    for (uint32_t i = 0; i < ROW_SIZE_TABLE_MAX; i++) {
        log_debug("  index %2u, size = %3u\n", i, row_size_table[i]);
    }
    log_debug("------------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}

static inline uint32_t _get_table_index(key_t x, key_t y, key_t p) {
    return (((x << 3) + y) * 18 + p);
}

bool population_table_initialise(address_t table_address,
                                 address_t synapse_rows_address,
                                 uint32_t *row_max_n_words) {
    log_info("population_table_initialise: starting");
    // Copy the master population table
    log_debug("reading master pop table from address 0x%.8x", table_address);
    memcpy(master_population_table, table_address,
           MASTER_POPULATION_MAX * sizeof(uint16_t));

    // Store the base address
    log_debug("the stored synaptic matrix base address is located at: 0x%.8x",
              synapse_rows_address);
    synaptic_rows_base_address = synapse_rows_address;

    // Copy the row size table
    log_debug("reading row length table of %d bytes from mem address 0x%.8x",
              ROW_SIZE_TABLE_MAX * sizeof(uint32_t),
              table_address + ((MASTER_POPULATION_MAX * sizeof(uint16_t)) / 4));
    memcpy(row_size_table,
           table_address + ((MASTER_POPULATION_MAX * sizeof(uint16_t)) / 4),
           ROW_SIZE_TABLE_MAX * sizeof(uint32_t));

    // The the maximum number of words to be the entry at the end of the
    // row size table
    *row_max_n_words = row_size_table[ROW_SIZE_TABLE_MAX - 1]
                       + N_SYNAPSE_ROW_HEADER_WORDS;

    log_info("population_table_initialise: completed successfully");
    _print_master_population_table();
    _print_row_size_table();

    return true;
}

//! \helpful method for converting a key with the field ranges of:
//! [x][y][p][n] where x, y and p represent the x,y and p coordinate of the
//! core that transmitted the spike and n represents the atom id which that
//! core has spiked with.
//! \param[in] k The key that needs translating
//! \return the x field of the key (assuming the key is in the format
//! described above)
static inline key_t _key_x(key_t k) {
    return (k >> 24);
}

//! \helpful method for converting a key with the field ranges of:
//! [x][y][p][n] where x, y and p represent the x,y and p coordinate of the
//! core that transmitted the spike and n represents the atom id which that
//! core has spiked with.
//! \param[in] k The key that needs translating
//! \return the y field of the key (assuming the key is in the format
//! described above)
static inline key_t _key_y(key_t k) {
    return ((k >> 16) & 0xFF);
}

//! \helpful method for converting a key with the field ranges of:
//! [x][y][p][n] where x, y and p represent the x,y and p coordinate of the
//! core that transmitted the spike and n represents the atom id which that
//! core has spiked with.
//! \param[in] k The key that needs translating
//! \return the p field of the key (assuming the key is in the format
//! described above)
static inline key_t _key_p(key_t k) {
    return ((k >> 11) & 0x1F);
}

//! \helpful method for converting a key with the field ranges of:
//! [x][y][p][n] where x, y and p represent the x,y and p coordinate of the
//! core that transmitted the spike and n represents the atom id which that
//! core has spiked with.
//! \param[in] k The key that needs translating
//! \return the n field of the key (assuming the key is in the format
//! described above)
static inline key_t _key_n(key_t k) {
    return k & 0x7FF;
}

bool population_table_get_first_address(
        spike_t spike, address_t* row_address, size_t* n_bytes_to_transfer) {

    uint32_t table_index = _get_table_index(_key_x(spike), _key_y(spike),
                                            _key_p(spike));
    uint32_t neuron_id = _key_n(spike);

    check((table_index < MASTER_POPULATION_MAX),
          "0 <= population_id (%u) < %u", table_index,
          MASTER_POPULATION_MAX);

    uint32_t entry = (uint32_t) (master_population_table[table_index]);

    // Lowest 3 bits are row size table index
    uint32_t row_size_index = entry & 0x7;

    // Remaining 13 bits are the 1K offset address in the synapse rows
    uint32_t address_offset = entry >> 3;

    log_debug("spike = %08x, table_index = %u, row_size_index = %u,"
              " address_offset = %u, neuron_id = %u",
              spike, table_index, row_size_index, address_offset, neuron_id);

    // If the row size is 0, there is no entry
    if (row_size_index == 0) {
        log_debug(
            "spike %u (= %x): population not found in master population table",
            spike, spike);
        return false;
    }

    // Convert row size to bytes
    // **THINK** this is dependent on synaptic row format so could be
    // dependent on implementation
    uint32_t num_synaptic_words = row_size_table[row_size_index];
    *n_bytes_to_transfer = (num_synaptic_words + N_SYNAPSE_ROW_HEADER_WORDS)
                           * sizeof(uint32_t);

    // Extra 3 words for the synaptic row header
    uint32_t stride = (num_synaptic_words + N_SYNAPSE_ROW_HEADER_WORDS);
    uint32_t neuron_offset = neuron_id * stride * sizeof(uint32_t);

    // **NOTE** 1024 converts from kilobyte offset to byte offset
    uint32_t population_offset = address_offset * 1024;

    log_debug("stride = %u, neuron offset = %u, population offset = %u,"
              " base = %08x, size = %u", stride, neuron_offset,
              population_offset, synaptic_rows_base_address,
              *n_bytes_to_transfer);

    *row_address = (uint32_t*) ((uint32_t) synaptic_rows_base_address
                                + population_offset
                                + neuron_offset);
    return true;
}

bool population_table_get_next_address(
        address_t* row_address, size_t* n_bytes_to_transfer) {

    // We assume there is only one row in this representation
    return false;
}
