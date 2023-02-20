/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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

//! The type of configuration parameters in SDRAM (written by host)
typedef struct stdp_params {
    //! The back-propagation delay, in basic simulation timesteps
    uint32_t backprop_delay;
} stdp_params;

typedef struct fixed_stdp_synapse {
    uint32_t delay_dendritic;
    uint32_t delay_axonal;
    uint32_t type;
    uint32_t index;
    uint32_t type_index;
    uint32_t ring_buffer_index;
} fixed_stdp_synapse;

//! Configuration parameters
static stdp_params params;

//! \brief The history data of post-events
static post_event_history_t *post_event_history;

//! Count of pre-synaptic events relevant to plastic processing
static uint32_t num_plastic_pre_synaptic_events = 0;

//! Count of times that the plastic math became saturated
static uint32_t plastic_saturation_count = 0;

/* PRIVATE FUNCTIONS */

// Mark a value as possibly unused while not using any instructions, guaranteed
#ifndef __use
#define __use(x)    do { (void) (x); } while (0)
#endif

static inline bool synapse_dynamics_stdp_init(
        address_t *address, stdp_params *params, uint32_t n_synapse_types,
        REAL *min_weights) {

    // Load parameters
    stdp_params *sdram_params = (stdp_params *) *address;
    spin1_memcpy(params, sdram_params, sizeof(stdp_params));

    // Load timing dependence data
    address_t weight_region_address = timing_initialise(
            (address_t) &sdram_params[1]);
    if (weight_region_address == NULL) {
        return false;
    }

    // Load weight dependence data
    address_t weight_result = weight_initialise(
            weight_region_address, n_synapse_types, min_weights);
    if (weight_result == NULL) {
        return false;
    }

    // Update address to after the region just read
    *address = weight_result;
    return true;
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

static inline fixed_stdp_synapse synapse_dynamics_stdp_get_fixed(
        uint32_t control_word, uint32_t time, uint32_t colour_delay) {
    // Extract control-word components
    // **NOTE** cunningly, control word is just the same as lower
    // 16-bits of 32-bit fixed synapse so same functions can be used
    uint32_t delay_dendritic = synapse_row_sparse_delay(control_word,
            synapse_type_index_bits, synapse_delay_mask);
    uint32_t delay_axonal = 0;  //sparse_axonal_delay(control_word);
    uint32_t type_index = synapse_row_sparse_type_index(control_word,
            synapse_type_index_mask);
    return (fixed_stdp_synapse) {
       .delay_dendritic = delay_dendritic,
       .delay_axonal = delay_axonal,
       .type = synapse_row_sparse_type(
                control_word, synapse_index_bits, synapse_type_mask),
       .index = synapse_row_sparse_index(
                control_word, synapse_index_mask),
       .type_index = type_index,
       .ring_buffer_index = synapse_row_get_ring_buffer_index_combined(
                (delay_axonal + delay_dendritic + time) - colour_delay, type_index,
                synapse_type_index_bits, synapse_delay_mask)
    };
}

static inline void synapse_dynamics_stdp_update_ring_buffers(
        weight_t *ring_buffers, fixed_stdp_synapse s, int32_t weight) {
    uint32_t accumulation = ring_buffers[s.ring_buffer_index] + weight;

    uint32_t sat_test = accumulation & 0x10000;
    if (sat_test) {
        accumulation = sat_test - 1;
        plastic_saturation_count++;
    }

    ring_buffers[s.ring_buffer_index] = accumulation;
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

uint32_t synapse_dynamics_n_connections_in_row(synapse_row_fixed_part_t *fixed) {
    return synapse_row_num_plastic_controls(fixed);
}
