/*
 * Copyright (c) 2021 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Implements the "local-only" handling of synapses, that is the
//!        processing of spikes without the use of transfers from SDRAM

#include "local_only.h"
#include "local_only/local_only_impl.h"
#include <debug.h>
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
};

//! A local copy of the configuration
static struct local_only_config config;

//! The input buffer for spikes received
static circular_buffer input_buffer;

//! Ring buffers to add weights to on spike processing
static uint16_t *ring_buffers;

//! Whether the loop of processing is currently running
//! (if not, it needs to be restarted on the next spike received)
static volatile bool process_loop_running = false;

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

//! \brief Start the process loop
static inline void run_next_process_loop(void) {
    if (spin1_trigger_user_event(local_time, 0)) {
        process_loop_running = true;
    }
}

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

        // Start the loop running if not already
        if (!process_loop_running) {
            run_next_process_loop();
        }
    }
}

//! \brief Multicast packet with payload received callback
//! \param[in] key The key received
//! \param[in] n_spikes The payload; the number of times to repeat the key
void mc_rcv_payload_callback(uint key, uint n_spikes) {
    n_spikes_received += 1;

    // Check of any one spike can be added to the circular buffer
    bool added = false;
    for (uint32_t i = n_spikes; i > 0; i--) {
        added |= circular_buffer_add(input_buffer, key);
    }

    // If any spikes were added, update the buffer maximum
    if (added) {
        update_max_input_buffer();

        // Start the loop running if not already
        if (!process_loop_running) {
            run_next_process_loop();
        }
    }
}

//! \brief User callback; performs spike processing loop
void process_callback(uint time, UNUSED uint unused1) {
    uint32_t spike;
    uint32_t cspr = spin1_int_disable();

    // While there is a spike to process, pull it out of the buffer
    while (process_loop_running && circular_buffer_get_next(input_buffer, &spike)) {
        spin1_mode_restore(cspr);

        // Process the spike using the specific local-only implementation
        local_only_impl_process_spike(time, spike, ring_buffers);
        cspr = spin1_int_disable();
    }
    process_loop_running = false;
    spin1_mode_restore(cspr);
}

// -----------------------------------------
// Implementations of interface (see local_only.h file for details)

bool local_only_initialise(void *local_only_addr, void *local_only_params_addr,
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

    spin1_callback_on(MC_PACKET_RECEIVED, mc_rcv_callback, -1);
    spin1_callback_on(MCPL_PACKET_RECEIVED, mc_rcv_payload_callback, -1);
    spin1_callback_on(USER_EVENT, process_callback, 0);

    return true;
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

void local_only_store_provenance(struct local_only_provenance *prov) {
    prov->max_spikes_received_per_timestep = max_spikes_received;
    prov->n_spikes_dropped = n_spikes_dropped;
    prov->n_spikes_lost_from_input = circular_buffer_get_n_buffer_overflows(input_buffer);
    prov->max_input_buffer_size = max_input_buffer_size;
}
