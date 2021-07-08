/*
 * Copyright (c) 2021 The University of Manchester
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

#include "local_only.h"
#include "local_only/local_only_impl.h"
#include <debug.h>
#include <circular_buffer.h>
#include <spin1_api.h>

struct local_only_config {
    uint32_t log_n_neurons;
    uint32_t log_n_synapse_types;
    uint32_t log_max_delay;
    uint32_t input_buffer_size;
    uint32_t clear_input_buffer;
};

static struct local_only_config config;

static circular_buffer input_buffer;

static uint16_t *ring_buffers;

static volatile bool process_loop_running = false;

static uint32_t n_spikes_received = 0;

static uint32_t max_spikes_received = 0;

static uint32_t n_spikes_dropped = 0;

static uint32_t max_input_buffer_size = 0;

uint32_t synapse_delay_mask;

uint32_t synapse_type_index_bits;

uint32_t synapse_index_bits;

static inline void run_next_process_loop(void) {
    if (spin1_trigger_user_event(0, 0)) {
        process_loop_running = true;
    }
}

static inline void update_max_input_buffer(void) {
    uint32_t sz = circular_buffer_size(input_buffer);
    if (sz > max_input_buffer_size) {
        max_input_buffer_size = sz;
    }
}

void mc_rcv_callback(uint key, UNUSED uint unused) {
    n_spikes_received += 1;
    if (circular_buffer_add(input_buffer, key)) {
        update_max_input_buffer();
        if (!process_loop_running) {
            run_next_process_loop();
        }
    }
}

void mc_rcv_payload_callback(uint key, uint n_spikes) {
    bool added = false;
    for (uint32_t i = n_spikes; i > 0; i--) {
        added |= circular_buffer_add(input_buffer, key);
    }
    if (added) {
        update_max_input_buffer();
        if (!process_loop_running) {
            run_next_process_loop();
        }
    }
}

void process_callback(UNUSED uint unused0, UNUSED uint unused1) {
    uint32_t spike;
    uint32_t cspr = spin1_int_disable();
    while (process_loop_running && circular_buffer_get_next(input_buffer, &spike)) {
        spin1_mode_restore(cspr);
        // TODO: Call local-only-impl
        cspr = spin1_int_disable();
    }
    process_loop_running = false;
    spin1_mode_restore(cspr);
}

bool local_only_initialise(void *local_only_addr, void *local_only_params_addr,
        uint16_t **ring_buffers_ptr) {

    // Set up the implementation
    if (!local_only_impl_initialise(local_only_params_addr)) {
        return false;
    }

    // Copy the config
    struct local_only_config *sdram_config = local_only_addr;
    config = *sdram_config;

    // Make some buffers
    synapse_type_index_bits = config.log_n_neurons + config.log_n_synapse_types;
    synapse_index_bits = config.log_n_neurons;
    uint32_t synapse_delay_bits = config.log_max_delay;
    synapse_delay_mask = (1 << synapse_delay_bits) - 1;

    uint32_t n_ring_buffer_bits =
            config.log_n_neurons + config.log_n_synapse_types + synapse_delay_bits;
    uint32_t ring_buffer_size = 1 << (n_ring_buffer_bits);

    ring_buffers = spin1_malloc(ring_buffer_size * sizeof(uint16_t));
    if (ring_buffers == NULL) {
        log_error("Could not allocate %u entries for ring buffers",
                ring_buffer_size);
        return false;
    }
    for (uint32_t i = 0; i < ring_buffer_size; i++) {
        ring_buffers[i] = 0;
    }
    *ring_buffers_ptr = ring_buffers;

    spin1_callback_on(MC_PACKET_RECEIVED, mc_rcv_callback, -1);
    spin1_callback_on(MCPL_PACKET_RECEIVED, mc_rcv_payload_callback, -1);
    spin1_callback_on(USER_EVENT, process_callback, 0);

    return true;
}

void local_only_clear_input(UNUSED uint32_t time) {
    uint32_t cspr = spin1_int_disable();
    if (n_spikes_received > max_spikes_received) {
        max_spikes_received = n_spikes_received;
    }
    n_spikes_received = 0;
    uint32_t n_spikes_left = circular_buffer_size(input_buffer);
    n_spikes_dropped += n_spikes_left;
    if (config.clear_input_buffer) {
        circular_buffer_clear(input_buffer);
    }
    spin1_mode_restore(cspr);
}

void local_only_store_provenance(struct local_only_provenance *prov) {
    prov->max_spikes_received_per_timestep = max_spikes_received;
    prov->n_spikes_dropped = n_spikes_dropped;
    prov->n_spikes_lost_from_input = circular_buffer_get_n_buffer_overflows(input_buffer);
    prov->max_input_buffer_size = max_input_buffer_size;
}
