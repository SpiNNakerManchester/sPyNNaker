/*! \file
 *  \brief This file contains the main functions for a playback spike generator.
 *
 *
 */

#include "../../common/recording.h"

#include <bit_field.h>
#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <string.h>

#define APPLICATION_MAGIC_NUMBER 0xAC2

//! container to point to a specific point in SDRAM for a given block of spikes
//! that have to be transmitted at a given time-step. The memory address is a
//! relative pointer from the start of the spike_data region.
typedef struct spike_block_t {
    uint32_t timestep;
    uint32_t block_offset_words;
} spike_block_t;

//! spike source array state machine
typedef enum state_e {
    e_state_inactive, e_state_dma_in_progress, e_state_spike_block_in_buffer,
} state_e;

//! spike source array region ids in human readable form
typedef enum region{
	system, block_index, spike_data, spike_histroy,
}region;

//! what each position in the block index region actually represent in terms of
//! data (each is a word)
typedef enum block_index_parameters{
	transmission_key, n_sources_to_simulate, num_spike_blocks_to_transmit,
	size_of_data_in_block_region,
}block_index_parameters;

// Globals
static spike_block_t *spike_blocks = NULL;
static uint32_t num_spike_blocks = 0;
static uint32_t current_spike_block_index = 0;
static uint32_t key = 0;
static uint32_t n_sources = 0;
static uint32_t recording_flags = 0;
// TODO could likely be removed and use the timer count from the timer callback
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

//! \locates the absolute memory address in SDRAM given the data structure which
//! contains the relative position from the start of the spike data region.
//! \param[in] *spike_block A pointer to a spike block strut to which the
//! Absolute memory address is wanted
//! \return the absolute memory address in SDRAM of the spike block strut.
static inline address_t get_spike_block_start_address(
        const spike_block_t *spike_block) {
    return spike_vector_region_start + spike_block->block_offset_words;
}

//! \takes the memory address of the block index region and interprets the data
//! written in the region from the configuration process.
//! \param[in] address The absolute memory address of the block index region
//! \return boolean of True if it successfully reads the block index region.
//! Otherwise returns False
static bool read_block_index_region(address_t address) {

    log_info("read_parameters: starting");

    key = address[transmission_key];
    log_info("\tkey = %08x", key);

    n_sources = address[n_sources_to_simulate];
    num_spike_blocks = address[num_spike_blocks_to_transmit];

    // Convert number of neurons to required number of blocks
    // **NOTE** in floating point terms this is ceil(num_neurons / 32)
    const uint32_t neurons_to_blocks_shift = 5;
    const uint32_t neurons_to_blocks_remainder =
        (1 << neurons_to_blocks_shift) - 1;
    spike_vector_words = n_sources >> neurons_to_blocks_shift;
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
    memcpy(spike_blocks, &address[size_of_data_in_block_region],
    	   num_spike_blocks * sizeof(spike_block_t));

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

//! \takes the memory address of the spike data region and interprets the data
//! written in the region from the configuration process.
//! \param[in] address The absolute memory address of the spike data region
//! \return boolean of True if it successfully reads the block index region.
//! Otherwise returns False
static bool read_spike_vector_region(address_t address) {
    log_info("read_spike_vector_region: starting");

    // assign the base address, for future indirections for ease of access
    spike_vector_region_start = address;
    log_info("\tStart address = %08x", spike_vector_region_start);

    log_info("read_spike_vector_region: completed successfully");
    return true;
}

//! \Initialises the model by reading in the regions and checking recording
//! data.
//! \param[in] *timer_period a pointer for the memory address where the timer
//! period should be stored during the function.
//! \return boolean of True if it successfully read all the regions and set up
//! all its internal data structures. Otherwise returns False
static bool initialize(uint32_t *timer_period) {
    log_info("Initialise: started");

    // Get the address this core's DTCM data starts at from SDRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(address)) {
        return false;
    }

    // Get the timing details
    if (!simulation_read_timing_details(
            data_specification_get_region(system, address),
            APPLICATION_MAGIC_NUMBER,
            timer_period, &simulation_ticks)) {
        return false;
    }

    // Get the recording information
    uint32_t spike_history_region_size;
    recording_read_region_sizes(
            &data_specification_get_region(system, address)
			[RECORDING_POSITION_IN_REGION],
			&recording_flags, &spike_history_region_size, NULL, NULL);
    if (recording_is_channel_enabled(
            recording_flags, e_recording_channel_spike_history)) {
        if (!recording_initialse_channel(
                data_specification_get_region(spike_histroy, address),
                e_recording_channel_spike_history, spike_history_region_size)) {
            return false;
        }
    }

    // Setup regions that specify spike source array data
    if (!read_block_index_region(
    		data_specification_get_region(block_index, address))) {
        return false;
    }

    if (!read_spike_vector_region(
    		data_specification_get_region(spike_data, address))) {
        return false;
    }

    // If we have any spike blocks and the 1st spike block should be sent at
    // the 1st time step
    if ((num_spike_blocks > 0) && (spike_blocks[0].timestep == 0)) {

        // Synchronously copy block into dma buffer
        memcpy(dma_buffer, get_spike_block_start_address(&spike_blocks[0]),
               spike_vector_bytes);

        // Set state to reflect that there is data already in the buffer
        state = e_state_spike_block_in_buffer;
    }

    log_info("Initialise: completed successfully");

    return true;
}

//! \The callback used when a DMA interrupt is set off. The result of this is
//! to change the state in the state machine.
//! \param[in] completed_id the id allocated to the dma. This is a value of
//! how many dma's have been requested
//! \param[in] tag The tag set by the DMA request (used for identification)
//! \return None
void spike_source_dma_callback(uint completed_id, uint tag) {
    use(completed_id);

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

//! \The callback used when a timer tic interrupt is set off. The result of
//! this is to transmit any spikes that need to be sent at this timer tic,
//! update any recording, and update the state machine's states.
//! If the timer tic is set to the end time, this method will call the
//! spin1api stop command to allow clean exit of the executable.
//! \param[in] timer_count the number of times this call back has been
//! executed since start of simulation
//! \param[in] unused for consistency sake of the API always returning two
//! parameters, this parameter has no semantics currently and thus is set to 0
//! \return None
void timer_callback(uint timer_count, uint unused) {
    use(timer_count);
    use(unused);
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
                    if (bit_field_test(dma_buffer, i)) {
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
                recording_record(e_recording_channel_spike_history, dma_buffer,
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
            recording_record(e_recording_channel_spike_history, empty_buffer,
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

//! \The only entry point for this model. it initialises the model, sets up the
//! Interrupts for the DMA and Timer tic and calls the spin1api for running.
void c_main(void) {

    // Load DTCM data
    uint32_t timer_period;

    if(!initialize(&timer_period)){
    	 rt_error(RTE_SWERR);
    }

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

