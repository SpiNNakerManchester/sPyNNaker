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

////! ::synapse_index_bits + number of synapse type bits
//static uint32_t synapse_type_index_bits;
////! Number of bits to hold the neuron index
//static uint32_t synapse_index_bits;
////! Mask to extract the neuron index (has ::synapse_index_bits bits set)
//static uint32_t synapse_index_mask;
////! Mask to extract the type and index (has ::synapse_type_index_bits bits set)
//static uint32_t synapse_type_index_mask;
////! ::synapse_delay_index_type_bits + number of bits to encode delay
//static uint32_t synapse_delay_index_type_bits;
////! Mask to extract the synapse type
//static uint32_t synapse_type_mask;

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
// The plastic control words used by Morrison synapses store an axonal delay
// in the upper 3 bits.
// Assuming a maximum of 16 delay slots, this is all that is required as:
//
// 1) Dendritic + Axonal <= 15
// 2) Dendritic >= Axonal
//
// Therefore:
//
// * Maximum value of dendritic delay is 15 (with axonal delay of 0)
//    - It requires 4 bits
// * Maximum value of axonal delay is 7 (with dendritic delay of 8)
//    - It requires 3 bits
//
// |        Axonal delay       |  Dendritic delay   |       Type        |      Index         |
// |---------------------------|--------------------|-------------------|--------------------|
// | SYNAPSE_AXONAL_DELAY_BITS | SYNAPSE_DELAY_BITS | SYNAPSE_TYPE_BITS | SYNAPSE_INDEX_BITS |
// |                           |                    |        SYNAPSE_TYPE_INDEX_BITS         |
// |---------------------------|--------------------|----------------------------------------|
#ifndef SYNAPSE_AXONAL_DELAY_BITS
#define SYNAPSE_AXONAL_DELAY_BITS 3
#endif

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
// Synaptic row plastic-region implementation
//---------------------------------------

void synapse_dynamics_print_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_data,
        synapse_row_fixed_part_t *fixed_region,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    __use(plastic_region_data);
    __use(fixed_region);
    __use(ring_buffer_to_input_buffer_left_shifts);

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
        synapses_print_weight(
                weight, ring_buffer_to_input_buffer_left_shifts[synapse_type]);
        log_debug("nA) d: %2u, %s, n = %3u)] - {%08x %08x}\n",
                synapse_row_sparse_delay(control_word, synapse_type_index_bits, synapse_delay_mask),
                synapse_types_get_type_char(synapse_type),
                synapse_row_sparse_index(control_word, synapse_index_mask),
                synapse_delay_mask, synapse_type_index_bits);
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}

bool synapse_dynamics_stdp_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts);

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    stdp_params *sdram_params = (stdp_params *) address;
    spin1_memcpy(&params, sdram_params, sizeof(stdp_params));
    address = (address_t) &sdram_params[1];

    // Call the stdp initialise function
    bool stdp_result = synapse_dynamics_stdp_initialise(
    		address, n_neurons, n_synapse_types,
			ring_buffer_to_input_buffer_left_shifts);
    if (!stdp_result) {
        return false;
    }

    return true;
}

void synapse_dynamics_stdp_process_plastic_synapse(
        uint32_t control_word, uint32_t last_pre_time, pre_trace_t last_pre_trace,
		pre_trace_t prev_trace, weight_t *ring_buffers, uint32_t time,
		plastic_synapse_t* plastic_words);

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

        synapse_dynamics_stdp_process_plastic_synapse(
        		control_word, last_pre_time, last_pre_trace,
				plastic_region_address->history.prev_trace, ring_buffers, time, plastic_words);

    }
    return true;
}

void synapse_dynamics_process_neuromodulator_event(
        uint32_t time, int32_t concentration, uint32_t neuron_index,
        uint32_t synapse_type);

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
    synapse_row_plastic_data_t *plastic_data = (void *)
            synapse_row_plastic_region(row);
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
            *delay = synapse_row_sparse_delay(control_word, synapse_type_index_bits,
                    synapse_delay_mask);
            *synapse_type = synapse_row_sparse_type(
                    control_word, synapse_index_bits, synapse_type_mask);
            return true;
        }
    }

    return false;
}

bool synapse_dynamics_remove_neuron(uint32_t offset, synaptic_row_t row) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    synapse_row_plastic_data_t *plastic_data = (void *)
            synapse_row_plastic_region(row);
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

//! packing all of the information into the required plastic control word
static inline control_t control_conversion(
        uint32_t id, uint32_t delay, uint32_t type) {
    control_t new_control =
            (delay & ((1 << synapse_delay_bits) - 1)) << synapse_type_index_bits;
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

uint32_t synapse_dynamics_n_connections_in_row(synapse_row_fixed_part_t *fixed) {
    return synapse_row_num_plastic_controls(fixed);
}
