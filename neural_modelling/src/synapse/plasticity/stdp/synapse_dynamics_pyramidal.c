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

// Spinn_common includes
#include "static-assert.h"

// sPyNNaker neural modelling includes
#include <synapse/synapses.h>

// Plasticity includes
#include "maths.h"
#include "post_events_rate_pyramidal.h"

#include "weight_dependence/weight.h"
#include "timing_dependence/timing.h"
#include <debug.h>
#include <utils.h>
#include <synapse/plasticity/synapse_dynamics.h>
#include <round.h>

#include <common/rate_generator.h>

#define DMA_TAG_READ_POST_BUFFER 2

static uint32_t synapse_type_index_bits;
static uint32_t synapse_index_bits;
static uint32_t synapse_index_mask;
static uint32_t synapse_type_index_mask;
static uint32_t synapse_delay_index_type_bits;
static uint32_t synapse_type_mask;

uint32_t num_plastic_pre_synaptic_events = 0;
uint32_t plastic_saturation_count = 0;

static uint32_t post_events_size;

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
typedef struct {

    REAL prev_time;

} pre_event_history_t;

post_event_history_t *post_event_history;

//SDRAM address for postsynaptic buffers
post_event_history_t *post_event_region;

/* PRIVATE FUNCTIONS */

//---------------------------------------
// Synapse update loop
//---------------------------------------
static inline final_state_t plasticity_update_basal_synapse(
        uint32_t time,
        const REAL last_pre_time,
        update_state_t current_state,
        const post_event_history_t *post_event_value) {

    //io_printf(IO_BUF, "basal update\n");

    //Apply Urbanczik-Senn Formula
    current_state = timing_apply_rate(
                        current_state, post_event_value->vb_diff, last_pre_time);


    // Return final synaptic word and weight
    return synapse_structure_get_final_state(current_state);
}

static inline final_state_t plasticity_update_apical_synapse(
        uint32_t time,
        const REAL last_pre_time,
        update_state_t current_state,
        const post_event_history_t *post_event_value) {

    //io_printf(IO_BUF, "apical update\n");

    //Apply Urbanczik-Senn Formula
    current_state = timing_apply_rate(
                        current_state, post_event_value->va_diff, last_pre_time);

    // Return final synaptic word and weight
    return synapse_structure_get_final_state(current_state);
}

//---------------------------------------
// Synaptic row plastic-region implementation
//---------------------------------------
static inline plastic_synapse_t* plastic_synapses(
        address_t plastic_region_address) {

    return (plastic_synapse_t *)
            &plastic_region_address[1];
}

//---------------------------------------
static inline pre_event_history_t *plastic_event_history(
        address_t plastic_region_address) {
    return (pre_event_history_t *) &plastic_region_address[0];
}

void synapse_dynamics_print_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(plastic_region_address);
    use(fixed_region_address);
    use(ring_buffer_to_input_buffer_left_shifts);

#if LOG_LEVEL >= LOG_DEBUG
    // Extract separate arrays of weights (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    plastic_synapse_t *plastic_words = plastic_synapses(plastic_region_address);
    const control_t *control_words =
            synapse_row_plastic_controls(fixed_region_address);
    size_t plastic_synapse =
            synapse_row_num_plastic_controls(fixed_region_address);

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
                synapse_row_sparse_delay(control_word, synapse_type_index_bits),
                synapse_types_get_type_char(synapse_type),
                synapse_row_sparse_index(control_word, synapse_index_mask),
                SYNAPSE_DELAY_MASK, synapse_type_index_bits);
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}

//---------------------------------------
static inline index_t sparse_axonal_delay(uint32_t x) {
#if 1
    use(x);
    return 0;
#else
    return (x >> synapse_delay_index_type_bits) & SYNAPSE_AXONAL_DELAY_MASK;
#endif
}

address_t synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts, bool *has_plastic_synapses) {
    // Load timing dependence data
    address_t weight_region_address = timing_initialise(address);
    if (address == NULL) {
        return NULL;
    }

    // Load weight dependence data
    address_t weight_result = weight_initialise(
            weight_region_address, n_synapse_types,
            ring_buffer_to_input_buffer_left_shifts);
    if (weight_result == NULL) {
        return NULL;
    }

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        return NULL;
    }

    // Used for DMA read
    post_events_size = n_neurons * sizeof(post_event_history_t);

    uint32_t n_neurons_power_2 = n_neurons;
    uint32_t log_n_neurons = 1;
    if (n_neurons != 1) {
        if (!is_power_of_2(n_neurons)) {
            n_neurons_power_2 = next_power_of_2(n_neurons);
        }
        log_n_neurons = ilog_2(n_neurons_power_2);
    }

    uint32_t n_synapse_types_power_2 = n_synapse_types;
    if (!is_power_of_2(n_synapse_types)) {
        n_synapse_types_power_2 = next_power_of_2(n_synapse_types);
    }
    uint32_t log_n_synapse_types = ilog_2(n_synapse_types_power_2);

    synapse_type_index_bits = log_n_neurons + log_n_synapse_types;
    synapse_type_index_mask = (1 << synapse_type_index_bits) - 1;
    synapse_index_bits = log_n_neurons;
    synapse_index_mask = (1 << synapse_index_bits) - 1;
    synapse_delay_index_type_bits =
            SYNAPSE_DELAY_BITS + synapse_type_index_bits;
    synapse_type_mask = (1 << log_n_synapse_types) - 1;

    *has_plastic_synapses = true;

    return weight_result;
}

// Converts a rate to an input
static inline input_t convert_rate_to_input(uint32_t rate) {
    union {
        uint32_t input_type;
        s1615 output_type;
    } converter;

    converter.input_type = (rate);

    return converter.output_type;
}

bool synapse_dynamics_process_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        REAL *ring_buffers, uint32_t time, uint32_t rate) {
    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    // plastic_synapse_t is same type as weight_t, which is accum!
    register plastic_synapse_t *plastic_words =
            plastic_synapses(plastic_region_address);
    const control_t *control_words =
            synapse_row_plastic_controls(fixed_region_address);
    register size_t plastic_synapse =
            synapse_row_num_plastic_controls(fixed_region_address);

    num_plastic_pre_synaptic_events += plastic_synapse;

    // Get event history from synaptic row
    pre_event_history_t *event_history =
            plastic_event_history(plastic_region_address);

    // Get last pre-synaptic rate from event history
    const REAL last_pre_rate = event_history->prev_time;
    //const pre_trace_t last_pre_trace = event_history->prev_trace;

    //io_printf(IO_BUF, "t %d prev %k\n", time, last_pre_rate);

    register REAL real_rate = out_rate(convert_rate_to_input(rate));

    //io_printf(IO_BUF, "plast rate %k\n", real_rate);

    // Update pre-synaptic trace
    log_debug("Adding pre-synaptic event to trace at time:%u", time);
    event_history->prev_time = real_rate;
    //event_history->prev_trace =
    //        timing_add_pre_spike(time, last_pre_time, last_pre_trace);

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {
        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        // Synapse type
        uint32_t type = synapse_row_sparse_type(
                control_word, synapse_index_bits);
        // Neuron index
        uint32_t index =
                synapse_row_sparse_index(control_word, synapse_index_mask);

        //io_printf(IO_BUF, "index %d\n", index);

        //io_printf(IO_BUF, "plast in row %k\n", *plastic_words);
        
        // Create update state from the plastic synaptic word
        update_state_t current_state =
                synapse_structure_get_update_state(*plastic_words, 0);

        //  Determine the type of synapse ans update the state
        // Type = 2 is apical inh, type = 1 basal exc

        final_state_t final_state;

        if (type == 2) {

            final_state = plasticity_update_apical_synapse(
                    time, last_pre_rate, current_state, &post_event_history[index]);
        }
        else if (type == 1) {

            final_state = plasticity_update_basal_synapse(
                    time, last_pre_rate, current_state, &post_event_history[index]);
        }
        // LP: THIS CHECK MIGHT BE REMOVED IF WE DECIDE TO CHANGE THE SYNAPSE TYPES
        else {

            log_error("Error: Trying to update the state of a non-plastic synapse");
            return false;
        }

        // Avoid the mul when input rate = 0
        if(real_rate) {

            // EDIT THIS TO BE *plastic_words ONCE THE WEIGHT UPDATE IS ADAPTED
            REAL curr_weight = synapse_structure_get_final_weight(final_state);

            // Add the current rate contribution with the new rate
            // REAL accumulation = ring_buffers[index] +
            //         MULT_ROUND_STOCHASTIC_ACCUM(real_rate, curr_weight);

            // Update the old rate contribution with the new weight
            //accumulation += MULT_ROUND_STOCHASTIC_ACCUM((curr_weight - old_weight), last_pre_rate);

    //        uint64_t sat_test = accumulation & 0x100000000;
    //        if (sat_test) {
    //            accumulation = sat_test - 1;
    //            plastic_saturation_count++;
    //        }

            //io_printf(IO_BUF, "right shift %d\n", weight_get_shift(current_state));
    //        io_printf(IO_BUF, "weight %k, rate %k\n", synapses_convert_weight_to_input(
    //                        synapse_structure_get_final_weight(final_state),
    //                        weight_get_shift(current_state)), real_rate);
            //io_printf(IO_BUF, "adding %k ", accumulation);

            // ring_buffers[index] = accumulation;
            ring_buffers[index] =
                sat_accum_sum(ring_buffers[index],
                              MULT_ROUND_STOCHASTIC_ACCUM(real_rate, curr_weight));

        }

        //io_printf(IO_BUF, "plast acc %k index %d\n", accumulation, ring_buffer_index);

        //io_printf(IO_BUF, "weight %k\n", synapse_structure_get_final_weight(final_state));

        // Write back updated synaptic word to plastic region REMOVE THIS WHEN WEIGHT UPDATE IS ADAPTED
        *plastic_words++ =
                synapse_structure_get_final_synaptic_word(final_state);
    }
    return true;
}

void synapse_dynamics_process_post_synaptic_event(index_t neuron_index, REAL *rates) {

    // Add post-event
    post_event_history_t *history = &post_event_history[neuron_index];

    post_events_update(history, rates[0], rates[1]);
}

// Can we make this inline?
void synapse_dynamics_set_post_buffer_region(uint32_t tag) {

    post_event_region = sark_tag_ptr(tag, 0);
}

void synapse_dynamics_read_post_buffer() {

    spin1_dma_transfer(
        DMA_TAG_READ_POST_BUFFER, post_event_region,
        post_event_history, DMA_READ, post_events_size);
}

input_t synapse_dynamics_get_intrinsic_bias(
        uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
    return 0.0k;
}

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(void) {
    return num_plastic_pre_synaptic_events;
}

uint32_t synapse_dynamics_get_plastic_saturation_count(void) {
    return plastic_saturation_count;
}

#if SYNGEN_ENABLED == 1

//! \brief  Searches the synaptic row for the the connection with the
//!         specified post-synaptic ID
//! \param[in] id: the (core-local) ID of the neuron to search for in the
//! synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[out] sp_data: the address of a struct through which to return
//! weight, delay information
//! \return bool: was the search successful?
bool find_plastic_neuron_with_id(
        uint32_t id, address_t row, structural_plasticity_data_t *sp_data) {
    address_t fixed_region = synapse_row_fixed_region(row);
    address_t plastic_region_address = synapse_row_plastic_region(row);
    plastic_synapse_t *plastic_words =
            plastic_synapses(plastic_region_address);
    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);
    plastic_synapse_t weight;
    uint32_t delay;

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {
        // Get next control word (auto incrementing)
        weight = *plastic_words++;
        uint32_t control_word = *control_words++;

        // Check if index is the one I'm looking for
        delay = synapse_row_sparse_delay(control_word, synapse_type_index_bits);
        if (synapse_row_sparse_index(control_word, synapse_index_mask) == id) {
            sp_data->weight = weight;
            sp_data->offset =
                    synapse_row_num_plastic_controls(fixed_region)
                    - plastic_synapse;
            sp_data->delay = delay;
            return true;
        }
    }

    sp_data->weight = -1;
    sp_data->offset = -1;
    sp_data->delay  = -1;
    return false;
}

//! \brief  Remove the entry at the specified offset in the synaptic row
//! \param[in] offset: the offset in the row at which to remove the entry
//! \param[in] row: the core-local address of the synaptic row
//! \return bool: was the removal successful?
bool remove_plastic_neuron_at_offset(uint32_t offset, address_t row) {
    address_t fixed_region = synapse_row_fixed_region(row);
    plastic_synapse_t *plastic_words =
            plastic_synapses(synapse_row_plastic_region(row));
    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Delete weight at offset
    plastic_words[offset] =  plastic_words[plastic_synapse - 1];
    plastic_words[plastic_synapse - 1] = 0;

    // Delete control word at offset
    control_words[offset] = control_words[plastic_synapse - 1];
    control_words[plastic_synapse - 1] = 0;

    // Decrement FP
    fixed_region[1]--;

    return true;
}

//! ensuring the weight is of the correct type and size
static inline plastic_synapse_t weight_conversion(uint32_t weight) {
    return (plastic_synapse_t) (0xFFFF & weight);
}

//! packing all of the information into the required plastic control word
static inline control_t control_conversion(
        uint32_t id, uint32_t delay, uint32_t type) {
    control_t new_control =
            (delay & ((1 << SYNAPSE_DELAY_BITS) - 1)) << synapse_type_index_bits;
    new_control |= (type & ((1 << synapse_type_index_bits) - 1)) << synapse_index_bits;
    new_control |= id & ((1 << synapse_index_bits) - 1);
    return new_control;
}

//! \brief  Add a plastic entry in the synaptic row
//! \param[in] id: the (core-local) ID of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return bool: was the addition successful?
bool add_plastic_neuron_with_id(uint32_t id, address_t row,
        uint32_t weight, uint32_t delay, uint32_t type) {
    plastic_synapse_t new_weight = weight_conversion(weight);
    control_t new_control = control_conversion(id, delay, type);

    address_t fixed_region = synapse_row_fixed_region(row);
    plastic_synapse_t *plastic_words =
            plastic_synapses(synapse_row_plastic_region(row));
    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Add weight at offset
    plastic_words[plastic_synapse] = new_weight;

    // Add control word at offset
    control_words[plastic_synapse] = new_control;

    // Increment FP
    fixed_region[1]++;
    return true;
}
#endif