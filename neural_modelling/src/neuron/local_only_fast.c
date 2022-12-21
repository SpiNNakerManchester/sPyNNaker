/*
 * Copyright (c) 2021-2022 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

//! \file
//! \brief Implements the "local-only" handling of synapses, that is the
//!        processing of spikes without the use of transfers from SDRAM

#include <debug.h>
#include "local_only_fast.h"
#include "local_only/local_only_impl.h"
#include "dma_common.h"
#include "synapse_row.h"
#include <circular_buffer.h>
#include <recording.h>
#include <spin1_api.h>

//: The configuration of the local only model
struct local_only_config {
	//! Log_2 of the number of neurons
    uint32_t log_n_neurons;
    //! Log_2 of the number of synapse types
    uint32_t log_n_synapse_types;
    //! Log_2 of the maximum delay supported
    uint32_t log_max_delay;
    //! The size to reserve for the input buffer of spikes
    uint32_t input_buffer_size;
    //! Whether to clear the input buffer
    uint32_t clear_input_buffer;
    //! Special key for update, or 0xFFFFFFFF if not used
    uint32_t update_key;
    //! Special mask for update, or 0 if not used
    uint32_t update_mask;
};

//! A local copy of the configuration
static struct local_only_config config;

//! The input buffer for spikes received
static circular_buffer input_buffer;

//! Ring buffers to add weights to on spike processing
static uint16_t *ring_buffers;

//! The number of spikes received in total in the last time step
static uint32_t n_spikes_received = 0;

//! The maximum number of spikes received in any time step
static uint32_t max_spikes_received = 0;

//! The number of spikes discarded in total during the run
static uint32_t n_spikes_dropped = 0;

//! The maximum size of the input buffer during the run
static uint32_t max_input_buffer_size = 0;

//! The local time step counter
static uint32_t local_time;

//! Where synaptic input is to be written
static struct sdram_config sdram_inputs;

//! The time taken to transfer inputs to SDRAM
static uint32_t clocks_to_transfer;

//! The mask to get the synaptic delay from a "synapse"
uint32_t synapse_delay_mask;

//! The number of bits used by the synapse type and post-neuron index
uint32_t synapse_type_index_bits;

//! The number of bits used by just the post-neuron index
uint32_t synapse_index_bits;

//! The region where packets-per-timestep are stored
uint32_t p_per_ts_region;

//! The number of packets received this time step for recording
static struct {
    uint32_t time;
    uint32_t packets_this_time_step;
} p_per_ts_struct;

//! \brief Update the maximum size of the input buffer
static inline void update_max_input_buffer(void) {
    uint32_t sz = circular_buffer_size(input_buffer);
    if (sz > max_input_buffer_size) {
        max_input_buffer_size = sz;
    }
}

//! \brief Multicast packet without payload received callback
//! \param[in] key The key received
//! \param[in] unused Should be 0
void mc_rcv_callback(uint key, UNUSED uint unused) {
    n_spikes_received += 1;

    // If there is space in the buffer, add the packet, update the counters
    if (circular_buffer_add(input_buffer, key)) {
        update_max_input_buffer();
    }
}

//! \brief Multicast packet with payload received callback
//! \param[in] key The key received
//! \param[in] n_spikes The payload; the number of times to repeat the key
void mc_rcv_payload_callback(uint key, uint n_spikes) {

	if ((key & config.update_mask) == config.update_key) {
		local_only_impl_update(key, n_spikes);
		return;
	}

    n_spikes_received += 1;

    // Check of any one spike can be added to the circular buffer
    bool added = false;
    for (uint32_t i = n_spikes; i > 0; i--) {
        added |= circular_buffer_add(input_buffer, key);
    }

    // If any spikes were added, update the buffer maximum
    if (added) {
        update_max_input_buffer();
    }
}

//! \brief Determine if this is the end of the time step
//! \return True if end of time step
static inline bool is_end_of_time_step(void) {
    return tc[T2_COUNT] == 0;
}

//! \brief Clear end of time step so it can be detected again
static inline void clear_end_of_time_step(void) {
    tc[T2_INT_CLR] = 1;
}

//! \brief Transfer the front of the ring buffers to SDRAM to be read by the
//!        neuron core at the next time step.
//! \param[in] time The current time step being executed.
static inline void transfer_buffers(uint32_t time) {
    uint32_t first_ring_buffer = synapse_row_get_first_ring_buffer_index(
            time + 1, synapse_type_index_bits, synapse_delay_mask);
    log_debug("Writing %d bytes to 0x%08x from ring buffer %d at 0x%08x",
             sdram_inputs.size_in_bytes, sdram_inputs.address, first_ring_buffer,
             &ring_buffers[first_ring_buffer]);
    do_fast_dma_write(&ring_buffers[first_ring_buffer], sdram_inputs.address,
            sdram_inputs.size_in_bytes);
}


//! \brief Measure how long it takes to transfer buffers
static inline void measure_transfer_time(void) {
    // Measure the time to do an upload to know when to schedule the timer
    tc[T2_LOAD] = 0xFFFFFFFF;
    tc[T2_CONTROL] = 0x82;
    transfer_buffers(0);
    wait_for_dma_to_complete();
    clocks_to_transfer = (0xFFFFFFFF - tc[T2_COUNT])
            + sdram_inputs.time_for_transfer_overhead;
    tc[T2_CONTROL] = 0;
    log_info("Transfer of %u bytes to 0x%08x took %u cycles",
            sdram_inputs.size_in_bytes, sdram_inputs.address, clocks_to_transfer);
}

void local_only_clear_input(uint32_t time) {
    local_time = time;
    if (n_spikes_received > max_spikes_received) {
        max_spikes_received = n_spikes_received;
    }
    p_per_ts_struct.packets_this_time_step = n_spikes_received;
    p_per_ts_struct.time = time;
    recording_record(p_per_ts_region, &p_per_ts_struct, sizeof(p_per_ts_struct));
    n_spikes_received = 0;
    uint32_t n_spikes_left = circular_buffer_size(input_buffer);
    n_spikes_dropped += n_spikes_left;
    if (config.clear_input_buffer) {
        circular_buffer_clear(input_buffer);
    }
}

//! \brief Prepare the start of a time step
//! \param[in] time The time step being executed
//! \return Whether we should proceed or not
static inline bool prepare_timestep(uint32_t time) {
    uint32_t cspr = spin1_int_disable();

    // We do this here rather than during init, as it should have similar
    // contention to the expected time of execution
    if (clocks_to_transfer == 0) {
        measure_transfer_time();
    }

    // Start timer2 to tell us when to stop
    uint32_t timer = tc[T1_COUNT];
    if (timer < clocks_to_transfer) {
        return false;
    }
    uint32_t time_until_stop = timer - clocks_to_transfer;
    tc[T2_CONTROL] = 0;
    tc[T2_LOAD] = time_until_stop;
    tc[T2_CONTROL] = 0xe3;

    log_debug("Start of time step %d, timer = %d, loading with %d",
            time, timer, time_until_stop);

    // Store recording data from last time step
    local_only_clear_input(time);

    spin1_mode_restore(cspr);
    return true;
}

static inline void process_end_of_time_step(uint32_t time) {
    // Stop interrupt processing
    uint32_t cspr = spin1_int_disable();

    // Start transferring buffer data for next time step
    transfer_buffers(time);
    wait_for_dma_to_complete();

    spin1_mode_restore(cspr);
}

//! \brief User callback; performs spike processing loop
void local_only_fast_processing_loop(uint time) {
    uint32_t spike = 0;

    // Prepare for the start
	if (!prepare_timestep(time)) {
		process_end_of_time_step(time);
		return;
	}

	while (true) {
		while (!is_end_of_time_step() && !circular_buffer_get_next(input_buffer, &spike)) {
			// This doesn't wait for interrupt currently because there isn't
			// a way to have a T2 interrupt without a callback function, and
			// a callback function is too slow!  This is therefore a busy wait.
			// wait_for_interrupt();
		}

		// If the timer has gone off, that takes precedence
		if (is_end_of_time_step()) {
			clear_end_of_time_step();
			process_end_of_time_step(time);
			return;
		}

		// Process the spike using the specific local-only implementation
		local_only_impl_process_spike(time, spike, ring_buffers);
	}
}

// -----------------------------------------
// Implementations of interface (see local_only.h file for details)

bool local_only_initialise(void *local_only_addr, void *local_only_params_addr,
		struct sdram_config sdram_inputs_param,
        uint32_t n_rec_regions_used, uint16_t **ring_buffers_ptr) {

    // Set up the implementation
    if (!local_only_impl_initialise(local_only_params_addr)) {
        return false;
    }

    // Copy the config
    struct local_only_config *sdram_config = local_only_addr;
    config = *sdram_config;

    input_buffer = circular_buffer_initialize(config.input_buffer_size);
    if (input_buffer == NULL) {
        log_error("Error setting up input buffer of size %u",
                config.input_buffer_size);
        return false;
    }
    log_info("Created input buffer with %u entries", config.input_buffer_size);

    // Make some buffers
    synapse_type_index_bits = config.log_n_neurons + config.log_n_synapse_types;
    synapse_index_bits = config.log_n_neurons;
    uint32_t synapse_delay_bits = config.log_max_delay;
    synapse_delay_mask = (1 << synapse_delay_bits) - 1;
    log_info("synapse_index_bits = %u, synapse_type_index_bits = %u, "
            "synapse_delay_mask = %u", synapse_index_bits, synapse_type_index_bits,
            synapse_delay_bits);

    uint32_t n_ring_buffer_bits = synapse_type_index_bits + synapse_delay_bits;
    uint32_t ring_buffer_size = 1 << (n_ring_buffer_bits);

    ring_buffers = spin1_malloc(ring_buffer_size * sizeof(uint16_t));
    if (ring_buffers == NULL) {
        log_error("Could not allocate %u entries for ring buffers",
                ring_buffer_size);
        return false;
    }
    log_info("Created ring buffer with %u entries at 0x%08x",
            ring_buffer_size, ring_buffers);
    for (uint32_t i = 0; i < ring_buffer_size; i++) {
        ring_buffers[i] = 0;
    }
    *ring_buffers_ptr = ring_buffers;

    p_per_ts_region = n_rec_regions_used;

    sdram_inputs = sdram_inputs_param;
    // Wipe the inputs using word writes
	for (uint32_t i = 0; i < (sdram_inputs.size_in_bytes >> 2); i++) {
		sdram_inputs.address[i] = 0;
	}

    spin1_callback_on(MC_PACKET_RECEIVED, mc_rcv_callback, -1);
    spin1_callback_on(MCPL_PACKET_RECEIVED, mc_rcv_payload_callback, -1);

    return true;
}

void local_only_store_provenance(struct local_only_provenance *prov) {
    prov->max_spikes_received_per_timestep = max_spikes_received;
    prov->n_spikes_dropped = n_spikes_dropped;
    prov->n_spikes_lost_from_input = circular_buffer_get_n_buffer_overflows(input_buffer);
    prov->max_input_buffer_size = max_input_buffer_size;
}
