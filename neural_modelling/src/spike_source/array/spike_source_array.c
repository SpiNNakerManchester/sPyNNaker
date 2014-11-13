#include "../../common/key_conversion.h"
#include "../../common/recording.h"

#include <bit_field.h>
#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
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
static uint32_t key = 0;
static uint32_t n_sources = 0;
static uint32_t recording_flags = 0;
static uint32_t time;
static uint32_t simulation_ticks = 0;

// How many bytes make up a spike vector
static uint32_t spike_vector_bytes = 0;
static uint32_t spike_vector_words = 0;

// Where does the region of SDRAM containing spike vectors begin
static address_t spike_vector_region_start = NULL;

// DTCM-allocated buffer, bit-vectors of outgoing spikes are made into
static uint32_t *dma_buffer = NULL;
static uint32_t *empty_buffer = NULL;
static state_e state = e_state_inactive;

static inline address_t get_spike_block_start_address(
        const spike_block_t *spike_block) {
    return spike_vector_region_start + spike_block->block_offset_words;
}

static bool read_parameters(address_t address) {

    log_info("read_parameters: starting");

    key = address[0];
    log_info("\tkey = %08x, (x: %u, y: %u) proc: %u", key,
            key_x(key), key_y(key), key_p(key));

    n_sources = address[1];
    num_spike_blocks = address[2];

    // Convert number of neurons to required number of blocks
    // **NOTE** in floating point terms this is ceil(num_neurons / 32)
    const uint32_t neurons_to_blocks_shift = 5;
    const uint32_t neurons_to_blocks_remainder =
            (1 << neurons_to_blocks_shift) - 1;
    spike_vector_words = n_sources >> 5;
    if ((n_sources & neurons_to_blocks_remainder) != 0) {
        spike_vector_words++;
    }

    // Convert this to bytes
    spike_vector_bytes = spike_vector_words * sizeof(uint32_t);

    log_info("\tnum spike sources = %u, spike vector words = %u,"
            " spike vector bytes = %u, num spike blocks = %u",
            n_sources, spike_vector_words, spike_vector_bytes,
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
    empty_buffer = (uint32_t*) spin1_malloc(spike_vector_bytes);
    if (empty_buffer == NULL) {
        log_error("Failed to allocate empty buffer");
        return false;
    }
    clear_bit_field(empty_buffer, spike_vector_words);


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

static bool initialize(uint32_t *timer_period) {
    log_info("initialize: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    uint32_t version;
    if (!data_specification_read_header(address, &version)) {
        return false;
    }

    // Get the timing details
    if (!simulation_read_timing_details(
            data_specification_get_region(0, address),
            APPLICATION_MAGIC_NUMBER,
            timer_period, &simulation_ticks)) {
        return false;
    }

    // Get the recording information
    uint32_t spike_history_region_size;
    recording_read_region_sizes(
            &data_specification_get_region(0, address)[3], &recording_flags,
            &spike_history_region_size, NULL, NULL);
    if (recording_is_channel_enabled(
            recording_flags, e_recording_channel_spike_history)) {
        recording_initialze_channel(
                data_specification_get_region(3, address),
                e_recording_channel_spike_history, spike_history_region_size);
    }

    // Setup regions that specify spike source array data
    if (!read_parameters(data_specification_get_region(1, address))) {
        return false;
    }

    if (!read_spike_vector_region(data_specification_get_region(2, address))) {
        return false;
    }

    // If we have any spike blocks and the 1st spike block should be sent at
    // the 1st timestep
    if ((num_spike_blocks > 0) && (spike_blocks[0].timestep == 0)) {

        // Synchronously copy block into dma buffer
        memcpy(dma_buffer, get_spike_block_start_address(&spike_blocks[0]),
                spike_vector_bytes);

        // Set state to reflect that there is data already in the buffer
        state = e_state_spike_block_in_buffer;
    }

    log_info("initialize: completed successfully");

    return true;
}

void spike_source_dma_callback(uint unused, uint tag) {
    use(unused);

    if (tag != 0) {
        sentinel("tag (%d) = 0", tag);
    }

    if (state != e_state_dma_in_progress) {
        sentinel("state (%u) = %u", state, e_state_dma_in_progress);
    }

    log_debug("DMA transfer complete");

    // Set state to reflect that the spike block is now in the buffer
    state = e_state_spike_block_in_buffer;
}

void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    time++;

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (simulation_ticks != UINT32_MAX && time >= simulation_ticks) {
        log_info("Simulation complete.\n");

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        recording_finalise();
        spin1_exit(0);
    }

    // If a spike block has been transferred ready for this tick
    if ((current_spike_block_index < num_spike_blocks)
            && (state != e_state_inactive)) {

        // If there is data in the buffer
        if (state == e_state_spike_block_in_buffer) {

            if (nonempty_bit_field(dma_buffer, spike_vector_words)) {

                for (index_t i = 0; i < n_sources; i++) {
                    if (bit_field_test(dma_buffer, i)){
                        log_debug("Sending spike packet %x", key | i);
                        spin1_send_mc_packet(key | i, 0, NO_PAYLOAD);
                        spin1_delay_us(1);
                    }
                }
            }

            // Go onto next spike block
            current_spike_block_index++;

            // Set state to inactive
            state = e_state_inactive;

            // If we should record the spike history, copy out-spikes to the
            // appropriate recording channel
            if (recording_is_channel_enabled(
                    recording_flags, e_recording_channel_spike_history)) {
                recording_record(
                        e_recording_channel_spike_history, dma_buffer,
                        spike_vector_bytes);
            }
        } else {

            // Otherwise error
            log_debug("ERROR: DMA hasn't completed in time for next tick");
        }
    } else {
        // If we should record the spike history, copy out-spikes to the
        // appropriate recording channel
        if (recording_is_channel_enabled(
                recording_flags, e_recording_channel_spike_history)) {
            recording_record(
                    e_recording_channel_spike_history, empty_buffer,
                    spike_vector_bytes);
        }
    }

    // If there are spike blocks remaining to be processed and there are no
    // outstanding DMAs
    if ((current_spike_block_index < num_spike_blocks)
            && (state == e_state_inactive)) {

        // If the next spike block should be sent at the NEXT tick
        spike_block_t *next_spike_block =
                &spike_blocks[current_spike_block_index];

        if (next_spike_block->timestep == (time + 1)) {

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

// Entry point
void c_main(void) {

    // Load DTCM data
    uint32_t timer_period;
    initialize(&timer_period);

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(TIMER_TICK, timer_callback, 2);
    spin1_callback_on(DMA_TRANSFER_DONE, spike_source_dma_callback, 0);

    log_info("Starting");
    simulation_run();
}

