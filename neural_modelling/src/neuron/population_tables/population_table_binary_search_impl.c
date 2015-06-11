#include "population_table.h"
#include "../synapse_row.h"
#include <debug.h>
#include <string.h>

typedef struct master_population_table_entry {
    uint32_t key;
    uint32_t mask;
    uint32_t address_and_row_length;
} master_population_table_entry;

static master_population_table_entry *master_population_table;
static uint32_t master_population_table_length;
static address_t synaptic_rows_base_address;

static inline uint32_t _get_address(master_population_table_entry entry) {

    // The address is in words and is the top 24-bits, so this downshifts by
    // 8 and then multiplies by 4 (= upshifts by 2) = downshift by 6
    return entry.address_and_row_length >> 6;
}

static inline uint32_t _get_row_length(master_population_table_entry entry) {
    return entry.address_and_row_length & 0xFF;
}

static inline uint32_t _get_neuron_id(master_population_table_entry entry,
                                      spike_t spike) {
    return spike & ~entry.mask;
}

static inline void _print_master_population_table() {
    log_info("master_population\n");
    log_info("------------------------------------------\n");
    for (uint32_t i = 0; i < master_population_table_length; i++) {
        master_population_table_entry entry = master_population_table[i];
        log_info("index %d, key: 0x%.8x, mask: 0x%.8x, address: 0x%.8x,"
                  " row_length: %u\n", i, entry.key, entry.mask,
                  _get_address(entry), _get_row_length(entry));
    }
    log_info("------------------------------------------\n");
}

//! \brief initiliser for master pop sturcutres. checks magic numbers and
//! that the strucutre is well formed.
//! \param[in] table_address the address in SDRAM where the master pop structure
//!            starts
//! \param[in] synapse_rows_address the address in SDRAM where synpase rows
//!            start
//! \param[in] row_max_n_words the max size a sybnapse row can be in words
//! \return true if the initialiser is valid false otherwise
bool population_table_initialise(
        address_t table_address, address_t synapse_rows_address,
        uint32_t *row_max_n_words) {

    log_info("population_table_binary_search_initialise: started");
    master_population_table_length = table_address[0];
    uint32_t n_bytes = master_population_table_length *
                       sizeof(master_population_table_entry);
    master_population_table = spin1_malloc(n_bytes);


    // Copy the master population table
    log_debug("reading master pop table from address 0x%.8x",
              &(table_address[1]));
    memcpy(master_population_table, &(table_address[1]), n_bytes);

    // Store the base address
    log_debug("the stored synaptic matrix base address is located at: 0x%.8x",
              synapse_rows_address);
    synaptic_rows_base_address = synapse_rows_address;

    *row_max_n_words = 0xFF + N_SYNAPSE_ROW_HEADER_WORDS;

    _print_master_population_table();
    log_info("population_table_binary_search_initialise: "
             "completed successfully");
    return true;
}

bool population_table_get_address(spike_t spike, address_t* row_address,
                                  size_t* n_bytes_to_transfer) {
    uint32_t imin = 0;
    uint32_t imax = master_population_table_length;

    while (imin < imax) {

        int imid = (imax + imin) >> 1;
        master_population_table_entry entry = master_population_table[imid];
        if ((spike & entry.mask) == entry.key) {
            uint32_t block_address = _get_address(entry) +
                                     (uint32_t) synaptic_rows_base_address;
            uint32_t row_length = _get_row_length(entry);
            uint32_t neuron_id = _get_neuron_id(entry, spike);
            uint32_t stride = (row_length + N_SYNAPSE_ROW_HEADER_WORDS);
            uint32_t neuron_offset = neuron_id * stride * sizeof(uint32_t);
            if (row_length == 0) {
                log_debug(
                    "spike %u (= %x): population found in master population"
                    "table but row length is 0",
                    spike, spike);
                return false;
            }
            *row_address = (address_t) (block_address + neuron_offset);
            *n_bytes_to_transfer = stride * sizeof(uint32_t);
            log_debug("spike = %08x, entry_index = %u, block_address = 0x%.8x,"
                      "row_length = %u, row_address = 0x%.8x, n_bytes = %u",
                      spike, imid, block_address, row_length, *row_address,
                      *n_bytes_to_transfer);
            return true;
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

