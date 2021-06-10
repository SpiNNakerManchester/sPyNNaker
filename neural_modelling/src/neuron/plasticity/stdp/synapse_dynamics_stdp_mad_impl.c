/*
 * Copyright (c) 2017-2019 The University of Manchester
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
//! \brief STDP core implementation
//!
//! "mad" for "Mapping and Debugging"?
// Spinn_common includes
#include <static-assert.h>

// sPyNNaker neural modelling includes
#include <neuron/synapses.h>

// Plasticity includes
#include "maths.h"
#include "post_events.h"

#include "weight_dependence/weight.h"
#include "timing_dependence/timing.h"
#include <debug.h>
#include <utils.h>
#include <neuron/plasticity/synapse_dynamics.h>
#include <stddef.h>

//! ::synapse_index_bits + number of synapse type bits
static uint32_t synapse_type_index_bits;
//! Number of bits to hold the neuron index
static uint32_t synapse_index_bits;
//! Mask to extract the neuron index (has ::synapse_index_bits bits set)
static uint32_t synapse_index_mask;
//! Mask to extract the type and index (has ::synapse_type_index_bits bits set)
static uint32_t synapse_type_index_mask;
//! ::synapse_delay_index_type_bits + number of bits to encode delay
static uint32_t synapse_delay_index_type_bits;
//! Mask to extract the synapse type
static uint32_t synapse_type_mask;

//! The type of configuration parameters in SDRAM (written by host)
typedef struct stdp_params {
    //! The back-propagation delay, in basic simulation timesteps
    uint32_t backprop_delay;
} stdp_params;

//! Configuration parameters
static stdp_params params;

//! Count of pre-synaptic events relevant to plastic processing
uint32_t num_plastic_pre_synaptic_events = 0;
//! Count of times that the plastic math became saturated
uint32_t plastic_saturation_count = 0;

//---------------------------------------
// Macros
//---------------------------------------
//! \brief The plastic control words used by Morrison synapses store an axonal
//! delay in the upper 3 bits.
//!
//! Assuming a maximum of 16 delay slots, this is all that is required as:
//!
//! 1. Dendritic + Axonal <= 15
//! 2. Dendritic >= Axonal
//!
//! Therefore:
//!
//! * Maximum value of dendritic delay is 15 (with axonal delay of 0)
//!    - It requires 4 bits
//! * Maximum value of axonal delay is 7 (with dendritic delay of 8)
//!    - It requires 3 bits
//!
//! ```
//! |        Axonal delay       |  Dendritic delay   |       Type        |      Index         |
//! |---------------------------|--------------------|-------------------|--------------------|
//! | SYNAPSE_AXONAL_DELAY_BITS | SYNAPSE_DELAY_BITS | SYNAPSE_TYPE_BITS | SYNAPSE_INDEX_BITS |
//! |                           |                    |        SYNAPSE_TYPE_INDEX_BITS         |
//! |---------------------------|--------------------|----------------------------------------|
//! ```
#ifndef SYNAPSE_AXONAL_DELAY_BITS
#define SYNAPSE_AXONAL_DELAY_BITS 3
#endif

//! Mask for extracting ::SYNAPSE_AXONAL_DELAY_BITS bits
#define SYNAPSE_AXONAL_DELAY_MASK \
    ((1 << SYNAPSE_AXONAL_DELAY_BITS) - 1)

//---------------------------------------
// Structures
//---------------------------------------
//! \brief The type of history data of pre-events
//!
//! This data is stored in SDRAM in the plastic part of the synaptic matrix
typedef struct {
    //! The event time
    uint32_t prev_time;
    //! The event trace
    pre_trace_t prev_trace;
} pre_event_history_t;

//! \brief The history data of post-events
post_event_history_t *post_event_history;

//! The format of the plastic data region of a synaptic row
struct synapse_row_plastic_data_t {
    //! The pre-event history
    pre_event_history_t history;
    //! The per-synapse information
    plastic_synapse_t synapses[];
};

/* PRIVATE FUNCTIONS */

// Mark a value as possibly unused while not using any instructions, guaranteed
#ifndef __use
#define __use(x)    do { (void) (x); } while (0)
#endif

//---------------------------------------
//! \brief Synapse update loop core
//! \param[in] time: The current time
//! \param[in] last_pre_time: The time of the last previous pre-event
//! \param[in] last_pre_trace: The last previous pre-trace
//! \param[in] new_pre_trace: The new pre-trace
//! \param[in] delay_dendritic: The dendritic delay for the synapse
//! \param[in] delay_axonal: The axonal delay for the synapse
//! \param[in] current_state: The current state
//! \param[in] post_event_history: The history
//! \return The new basic state of the synapse
static inline final_state_t plasticity_update_synapse(
        const uint32_t time,
        const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
        const pre_trace_t new_pre_trace, const uint32_t delay_dendritic,
        const uint32_t delay_axonal, update_state_t current_state,
        const post_event_history_t *post_event_history) {
    // Apply axonal delay to time of last presynaptic spike
    const uint32_t delayed_last_pre_time = last_pre_time + delay_axonal;

    // Get the post-synaptic window of events to be processed
    const uint32_t window_begin_time =
            (delayed_last_pre_time >= delay_dendritic)
            ? (delayed_last_pre_time - delay_dendritic) : 0;
    const uint32_t delayed_pre_time = time + delay_axonal;
    const uint32_t window_end_time =
            (delayed_pre_time >= delay_dendritic)
            ? (delayed_pre_time - delay_dendritic) : 0;
    post_event_window_t post_window = post_events_get_window_delayed(
            post_event_history, window_begin_time, window_end_time);

    log_debug("\tPerforming deferred synapse update at time:%u", time);
    log_debug("\t\tbegin_time:%u, end_time:%u - prev_time:%u (valid %u), num_events:%u",
            window_begin_time, window_end_time, post_window.prev_time,
            post_window.prev_time_valid, post_window.num_events);

#if LOG_LEVEL >= LOG_DEBUG
    print_event_history(post_event_history);
    print_delayed_window_events(post_event_history, window_begin_time,
            window_end_time, delay_dendritic);
#endif

    // Process events in post-synaptic window
    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time = *post_window.next_time + delay_dendritic;

        log_debug("\t\tApplying post-synaptic event at delayed time:%u, pre:%u\n",
                delayed_post_time, delayed_last_pre_time);

        // Apply spike to state
        current_state = timing_apply_post_spike(
                delayed_post_time, *post_window.next_trace, delayed_last_pre_time,
                last_pre_trace, post_window.prev_time, post_window.prev_trace,
                current_state);

        // Go onto next event
        post_window = post_events_next(post_window);
    }

    // Apply spike to state only if there has been a post spike ever
    if (post_window.prev_time_valid) {
        const uint32_t delayed_last_post = post_window.prev_time + delay_dendritic;
        log_debug("\t\tApplying pre-synaptic event at time:%u last post time:%u\n",
                delayed_pre_time, delayed_last_post);
        current_state = timing_apply_pre_spike(
                delayed_pre_time, new_pre_trace, delayed_last_pre_time, last_pre_trace,
                delayed_last_post, post_window.prev_trace, current_state);
    }

    // Return final synaptic word and weight
    return synapse_structure_get_final_state(current_state);
}

//---------------------------------------
// Synaptic row plastic-region implementation
//---------------------------------------

void synapse_dynamics_print_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_data,
        synapse_row_fixed_part_t *fixed_region,
        REAL *min_weights) {
    __use(plastic_region_data);
    __use(fixed_region);
    __use(min_weights);

#if LOG_LEVEL >= LOG_DEBUG
    // Extract separate arrays of weights (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    const plastic_synapse_t *plastic_words = plastic_region_data->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    size_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    log_debug("Plastic region %u synapses\n", plastic_synapse);

    // Loop through plastic synapses
    for (uint32_t i = 0; i < plastic_synapse; i++) {
        // Get next control word (auto incrementing control word)
        uint32_t control_word = *control_words++;
        uint32_t synapse_type = synapse_row_sparse_type(
                control_word, synapse_index_bits, synapse_type_mask);

        // Get weight
        update_state_t update_state = synapse_structure_get_update_state(
                *plastic_words++, synapse_type);
        final_state_t final_state = synapse_structure_get_final_state(
                update_state);
        weight_t weight = synapse_structure_get_final_weight(final_state);

        log_debug("%08x [%3d: (w: %5u (=", control_word, i, weight);
        synapses_print_weight(weight, min_weights[synapse_type]);
        log_debug("nA) d: %2u, %s, n = %3u)] - {%08x %08x}\n",
            synapse_row_sparse_delay(control_word, synapse_type_index_bits),
            synapse_types_get_type_char(synapse_type),
            synapse_row_sparse_index(control_word, synapse_index_mask),
            SYNAPSE_DELAY_MASK, synapse_type_index_bits);
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}

//---------------------------------------
//! \brief Get the axonal delay
//! \param[in] x: The packed plastic synapse control word
//! \return the axonal delay
static inline index_t sparse_axonal_delay(uint32_t x) {
#if 1
    // No axonal delay, ever
    __use(x);
    return 0;
#else
    return (x >> synapse_delay_index_type_bits) & SYNAPSE_AXONAL_DELAY_MASK;
#endif
}

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        REAL *min_weights) {
    stdp_params *sdram_params = (stdp_params *) address;
    spin1_memcpy(&params, sdram_params, sizeof(stdp_params));
    address = (address_t) &sdram_params[1];

    // Load timing dependence data
    address_t weight_region_address = timing_initialise(address);
    if (address == NULL) {
        return false;
    }

    // Load weight dependence data
    address_t weight_result = weight_initialise(
            weight_region_address, n_synapse_types, min_weights);
    if (weight_result == NULL) {
        return false;
    }

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        return false;
    }

    uint32_t n_neurons_power_2 = n_neurons;
    uint32_t log_n_neurons = 1;
    if (n_neurons != 1) {
        if (!is_power_of_2(n_neurons)) {
            n_neurons_power_2 = next_power_of_2(n_neurons);
        }
        log_n_neurons = ilog_2(n_neurons_power_2);
    }

    uint32_t n_synapse_types_power_2 = n_synapse_types;
    uint32_t log_n_synapse_types = 1;
    if (n_synapse_types != 1) {
        if (!is_power_of_2(n_synapse_types)) {
            n_synapse_types_power_2 = next_power_of_2(n_synapse_types);
        }
        log_n_synapse_types = ilog_2(n_synapse_types_power_2);
    }

    synapse_type_index_bits = log_n_neurons + log_n_synapse_types;
    synapse_type_index_mask = (1 << synapse_type_index_bits) - 1;
    synapse_index_bits = log_n_neurons;
    synapse_index_mask = (1 << synapse_index_bits) - 1;
    synapse_delay_index_type_bits =
            SYNAPSE_DELAY_BITS + synapse_type_index_bits;
    synapse_type_mask = (1 << log_n_synapse_types) - 1;
    return true;
}

bool synapse_dynamics_process_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_address,
        synapse_row_fixed_part_t *fixed_region,
        weight_t *ring_buffers, uint32_t time) {
    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    plastic_synapse_t *plastic_words = plastic_region_address->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    size_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    num_plastic_pre_synaptic_events += plastic_synapse;

    // Get last pre-synaptic event from event history
    const uint32_t last_pre_time = plastic_region_address->history.prev_time;
    const pre_trace_t last_pre_trace = plastic_region_address->history.prev_trace;

    // Update pre-synaptic trace
    log_debug("Adding pre-synaptic event to trace at time:%u", time);
    plastic_region_address->history.prev_time = time;
    plastic_region_address->history.prev_trace =
            timing_add_pre_spike(time, last_pre_time, last_pre_trace);

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {
        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        // Extract control-word components
        // **NOTE** cunningly, control word is just the same as lower
        // 16-bits of 32-bit fixed synapse so same functions can be used
        uint32_t delay_axonal = sparse_axonal_delay(control_word);
        uint32_t delay_dendritic = synapse_row_sparse_delay(
                control_word, synapse_type_index_bits);
        uint32_t type = synapse_row_sparse_type(
                control_word, synapse_index_bits, synapse_type_mask);
        uint32_t index =
                synapse_row_sparse_index(control_word, synapse_index_mask);
        uint32_t type_index = synapse_row_sparse_type_index(
                control_word, synapse_type_index_mask);

        // Create update state from the plastic synaptic word
        update_state_t current_state =
                synapse_structure_get_update_state(*plastic_words, type);

        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
                delay_axonal + delay_dendritic + time, type_index,
                synapse_type_index_bits);

        // Update the synapse state
        uint32_t post_delay = delay_dendritic;
        if (!params.backprop_delay) {
            post_delay = 0;
        }
        final_state_t final_state = plasticity_update_synapse(
                time, last_pre_time, last_pre_trace,
                plastic_region_address->history.prev_trace,
                post_delay, delay_axonal, current_state,
                &post_event_history[index]);

        // Add weight to ring-buffer entry
        // **NOTE** Dave suspects that this could be a
        // potential location for overflow

        uint32_t accumulation = ring_buffers[ring_buffer_index] +
                synapse_structure_get_final_weight(final_state);

        uint32_t sat_test = accumulation & 0x10000;
        if (sat_test) {
            accumulation = sat_test - 1;
            plastic_saturation_count++;
        }

        ring_buffers[ring_buffer_index] = accumulation;

        // Write back updated synaptic word to plastic region
        *plastic_words++ =
                synapse_structure_get_final_synaptic_word(final_state);
    }
    return true;
}

void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    log_debug("Adding post-synaptic event to trace at time:%u", time);

    // Add post-event
    post_event_history_t *history = &post_event_history[neuron_index];
    const uint32_t last_post_time = history->times[history->count_minus_one];
    const post_trace_t last_post_trace =
            history->traces[history->count_minus_one];
    post_events_add(time, history,
            timing_add_post_spike(time, last_post_time, last_post_trace));
}

input_t synapse_dynamics_get_intrinsic_bias(
        UNUSED uint32_t time, UNUSED index_t neuron_index) {
    return ZERO;
}

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(void) {
    return num_plastic_pre_synaptic_events;
}

uint32_t synapse_dynamics_get_plastic_saturation_count(void) {
    return plastic_saturation_count;
}

bool synapse_dynamics_find_neuron(
        uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay,
        uint32_t *offset, uint32_t *synapse_type) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    synapse_row_plastic_data_t *plastic_data = synapse_row_plastic_region(row);
    const plastic_synapse_t *plastic_words = plastic_data->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {
        // Take the weight anyway as this updates the plastic words
        *weight = synapse_structure_get_weight(*plastic_words++);

        // Check if index is the one I'm looking for
        uint32_t control_word = *control_words++;
        if (synapse_row_sparse_index(control_word, synapse_index_mask) == id) {
            *offset = synapse_row_num_plastic_controls(fixed_region) - plastic_synapse;
            *delay = synapse_row_sparse_delay(control_word, synapse_type_index_bits);
            *synapse_type = synapse_row_sparse_type(
                    control_word, synapse_index_bits, synapse_type_mask);
            return true;
        }
    }

    return false;
}

bool synapse_dynamics_remove_neuron(uint32_t offset, synaptic_row_t row){
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    synapse_row_plastic_data_t *plastic_data = synapse_row_plastic_region(row);
    plastic_synapse_t *plastic_words = plastic_data->synapses;
    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Delete weight at offset
    plastic_words[offset] =  plastic_words[plastic_synapse - 1];

    // Delete control word at offset
    control_words[offset] = control_words[plastic_synapse - 1];
    control_words[plastic_synapse - 1] = 0;

    // Decrement FP
    fixed_region->num_plastic--;

    return true;
}

//! \brief Pack all of the information into the required plastic control word
//! \param[in] id: The spike ID
//! \param[in] delay: The delay
//! \param[in] type: The synapse type
//! \return The encoded word
static inline control_t control_conversion(
        uint32_t id, uint32_t delay, uint32_t type) {
    control_t new_control =
            (delay & ((1 << SYNAPSE_DELAY_BITS) - 1)) << synapse_type_index_bits;
    new_control |= (type & ((1 << synapse_type_index_bits) - 1)) << synapse_index_bits;
    new_control |= id & ((1 << synapse_index_bits) - 1);
    return new_control;
}

bool synapse_dynamics_add_neuron(uint32_t id, synaptic_row_t row,
        weight_t weight, uint32_t delay, uint32_t type) {
    plastic_synapse_t new_weight = synapse_structure_create_synapse(weight);
    control_t new_control = control_conversion(id, delay, type);

    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    synapse_row_plastic_data_t *plastic_data = synapse_row_plastic_region(row);
    plastic_synapse_t *plastic_words = plastic_data->synapses;
    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Add weight at offset
    plastic_words[plastic_synapse] = new_weight;

    // Add control word at offset
    control_words[plastic_synapse] = new_control;

    // Increment FP
    fixed_region->num_plastic++;

    return true;
}

uint32_t synapse_dynamics_n_connections_in_row(
        synapse_row_fixed_part_t *fixed) {
    return synapse_row_num_plastic_controls(fixed);
}
