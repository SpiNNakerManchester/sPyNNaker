#include "../common/spike_source_impl.h"
#include "../../common/key_conversion.h"

#include <data_specification.h>
#include <debug.h>
#include <string.h>

#define APPLICATION_MAGIC_NUMBER 0xAC2

typedef struct spike_block_t {
    uint32_t timestep;
    uint32_t block_offset_words;
} spike_block_t;

typedef enum state_e {
    e_state_inactive, e_state_dma_in_progress, e_state_spike_block_in_buffer,
} state_e;

// Globals
static spike_block_t *spike_blocks = NULL;
static uint32_t num_spike_blocks = 0;
static uint32_t current_spike_block_index = 0;

// How many bytes make up a spike vector
static uint32_t spike_vector_bytes = 0;

// Where does the region of SDRAM containing spike vectors begin
static address_t spike_vector_region_start = NULL;

// DTCM-allocated buffer, bit-vectors of outgoing spikes are made into
static uint32_t *dma_buffer = NULL;
static state_e state = e_state_inactive;

static inline address_t get_spike_block_start_address(
        const spike_block_t *spike_block) {
    return spike_vector_region_start + spike_block->block_offset_words;
}

uint32_t spike_source_impl_get_application_id() {
    return APPLICATION_MAGIC_NUMBER;
}

uint32_t spike_source_impl_get_spike_recording_region_id() {
    return 3;
}

static bool read_parameters(
        address_t address, uint32_t* spike_source_key,
        uint32_t *spike_source_n_sources) {

    log_info("read_parameters: starting");

    *spike_source_key = address[0];
    log_info("\tkey = %08x, (x: %u, y: %u) proc: %u", *spike_source_key,
            key_x(*spike_source_key), key_y(*spike_source_key),
            key_p(*spike_source_key));

    *spike_source_n_sources = address[1];
    num_spike_blocks = address[2];

    // Convert number of neurons to required number of blocks
    // **NOTE** in floating point terms this is ceil(num_neurons / 32)
    const uint32_t neurons_to_blocks_shift = 5;
    const uint32_t neurons_to_blocks_remainder = (1 << neurons_to_blocks_shift)
            - 1;
    uint32_t spike_vector_words = *spike_source_n_sources >> 5;
    if ((*spike_source_n_sources & neurons_to_blocks_remainder) != 0) {
        spike_vector_words++;
    }

    // Convert this to bytes
    spike_vector_bytes = spike_vector_words * sizeof(uint32_t);

    log_info("\tnum spike sources = %u, spike vector words = %u,"
            " spike vector bytes = %u, num spike blocks = %u",
            *spike_source_n_sources, spike_vector_words, spike_vector_bytes,
            num_spike_blocks);

    // Allocate DTCM for array of spike blocks and copy block of data
    spike_blocks = (spike_block_t*) spin1_malloc(
            num_spike_blocks * sizeof(spike_block_t));
    if (spike_blocks == NULL) {
        log_error("Failed to allocated spike blocks");
        return false;
    }
    memcpy(spike_blocks, &address[3], num_spike_blocks * sizeof(spike_block_t));

    log_debug("\tSpike blocks:");
    for(uint32_t b = 0; b < num_spike_blocks; b++) {
        log_debug("\t\t%u - Timestep: %u Offset: %u", b,
                spike_blocks[b].timestep, spike_blocks[b].block_offset_words);
    }

    // Allocate correctly sized DMA buffer
    dma_buffer = (uint32_t*) spin1_malloc(spike_vector_bytes);
    if (dma_buffer == NULL) {
        log_error("Failed to allocate dma buffer");
        return false;
    }

    log_info("read_parameters: completed successfully");
    return true;
}

static bool read_spike_vector_region(address_t address) {
    log_info("read_spike_vector_region: starting");

    spike_vector_region_start = &address[0];
    log_info("\tStart address = %08x", spike_vector_region_start);

    log_info("read_spike_vector_region: completed successfully");
    return true;
}

bool spike_source_impl_initialize(
        address_t data_address, uint32_t *spike_source_key,
        uint32_t *spike_source_n_sources) {

    log_info("spike_source_impl_initialize: starting");

    // Setup regions that specify spike source array data
    if (!read_parameters(
            data_specification_get_region(1, data_address), spike_source_key,
            spike_source_n_sources))
        return false;

    if (!read_spike_vector_region(
            data_specification_get_region(2, data_address)))
        return false;

    // If we have any spike blocks and the 1st spike block should be sent at the 1st timestep
    if ((num_spike_blocks > 0) && (spike_blocks[0].timestep == 0)) {

        // Synchronously copy block into dma buffer
        memcpy(dma_buffer, get_spike_block_start_address(&spike_blocks[0]),
                spike_vector_bytes);

        // Set state to reflect that there is data already in the buffer
        state = e_state_spike_block_in_buffer;
    }

    log_info("spike_source_impl_initialize: completed successfully");

    return true;
}

void spike_source_impl_dma_callback(uint unused, uint tag) {
    use(unused);

    if (tag != 0) {
        sentinel("tag (%d) = 0", tag);
    }

    if (state != e_state_dma_in_progress) {
        sentinel("state (%u) = %u", state, e_state_dma_in_progress);
    }

    log_info("DMA transfer complete");

    // Set state to reflect that the spike block is now in the buffer
    state = e_state_spike_block_in_buffer;
}

void spike_source_impl_generate_spikes(uint32_t tick) {

    // If a spike block has been transferred ready for this tick
    if ((current_spike_block_index < num_spike_blocks)
            && (state != e_state_inactive)) {

        // If there is data in the buffer
        if (state == e_state_spike_block_in_buffer) {

            // Copy contents of DMA buffer into out spikes
            memcpy(out_spikes, dma_buffer, spike_vector_bytes);

            // Go onto next spike block
            current_spike_block_index++;

            // Set state to inactive
            state = e_state_inactive;
        } else {

            // Otherwise error
            log_info("ERROR: DMA hasn't completed in time for next tick");
        }
    }

    // If there are spike blocks remaining to be processed and there are no
    // outstanding DMAs
    if ((current_spike_block_index < num_spike_blocks)
            && (state == e_state_inactive)) {

        // If the next spike block should be sent at the NEXT tick
        spike_block_t *next_spike_block =
                &spike_blocks[current_spike_block_index];

        if (next_spike_block->timestep == (tick + 1)) {

            // Start a DMA transfer from the absolute address of the spike
            // block into buffer
            spin1_dma_transfer(
                    0, get_spike_block_start_address(next_spike_block),
                    dma_buffer, DMA_READ, spike_vector_bytes);

            // Set state to dma in progress
            state = e_state_dma_in_progress;
        }
    }
}
