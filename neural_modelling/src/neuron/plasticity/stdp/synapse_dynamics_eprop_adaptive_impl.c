/*
 * Copyright (c) 2019 The University of Manchester
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

// Spinn_common includes
#include "static-assert.h"

// sPyNNaker neural modelling includes
#include <neuron/synapses.h>

// Plasticity includes
#include "maths.h"
#include "post_events.h"
#include "synapse_dynamics_stdp_common.h"

//---------------------------------------
// Structures
//---------------------------------------
//! The format of the plastic data region of a synaptic row
struct synapse_row_plastic_data_t {
    //! The pre-event history
    pre_event_history_t history;
    //! The per-synapse information
    plastic_synapse_t synapses[];
};

// TODO: make work with stdp common? (is this even really STDP?)

#include <neuron/models/neuron_model_eprop_adaptive_impl.h>

extern neuron_t *neuron_array;

extern uint32_t neuron_impl_neurons_in_partition;

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

uint32_t RECURRENT_SYNAPSE_OFFSET = 100;

//---------------------------------------
// Synaptic row plastic-region implementation
//---------------------------------------
static inline plastic_synapse_t* plastic_synapses(
        address_t plastic_region_address) {
    const uint32_t pre_event_history_size_words =
            sizeof(pre_event_history_t) / sizeof(uint32_t);
    static_assert(
            pre_event_history_size_words * sizeof(uint32_t) == sizeof(pre_event_history_t),
            "Size of pre_event_history_t structure should be a multiple"
            " of 32-bit words");

    return (plastic_synapse_t *)
            &plastic_region_address[pre_event_history_size_words];
}

//---------------------------------------
static inline pre_event_history_t *plastic_event_history(
        address_t plastic_region_address) {
    return (pre_event_history_t *) &plastic_region_address[0];
}

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
                synapse_row_sparse_delay(
                		control_word, synapse_type_index_bits, synapse_delay_mask),
                synapse_types_get_type_char(synapse_type),
                synapse_row_sparse_index(control_word, synapse_index_mask),
                synapse_delay_mask, synapse_type_index_bits);
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

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    if (!synapse_dynamics_stdp_init(&address, &params, n_synapse_types,
                ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        return false;
    }

    return true;
}

static inline final_state_t eprop_plasticity_update(
		update_state_t current_state, REAL delta_w) {

	int32_t delta_w_int = (int32_t) roundk(delta_w, 15);
	// TODO: THIS NEEDS UPDATING TO APPROPRIATE SCALING (?)

    if (delta_w){ // TODO: This should probably be delta_w_int
        if (delta_w_int < 0){
            current_state = weight_one_term_apply_depression(
            		current_state, delta_w_int << 3);
        } else {
            current_state = weight_one_term_apply_potentiation(
            		current_state, delta_w_int << 3);
        }
    }

	// Calculate regularisation error
	REAL reg_error = neuron_array[0].core_target_rate - (
			neuron_array[0].core_pop_rate / neuron_impl_neurons_in_partition);
	// this needs swapping for an inverse multiply - too expensive to do divide
	// on every spike

    // Return final synaptic word and weight
    return synapse_structure_get_final_state(current_state, reg_error);
}

bool synapse_dynamics_process_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_address,
		synapse_row_fixed_part_t *fixed_region,
        weight_t *ring_buffers, uint32_t time, uint32_t colour_delay,
		bool *write_back) {
    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    plastic_synapse_t *plastic_words = plastic_region_address->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    size_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    num_plastic_pre_synaptic_events += plastic_synapse;

    // Could maybe have a single z_bar for the entire synaptic row and
    // update it once here for all synaptic words?

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {
        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        // Extract control-word components
        // **NOTE** cunningly, control word is just the same as lower
        // 16-bits of 32-bit fixed synapse so same functions can be used
        uint32_t delay = 1;
        uint32_t syn_ind_from_delay = synapse_row_sparse_delay(
        		control_word, synapse_type_index_bits, synapse_delay_mask);

        uint32_t type = synapse_row_sparse_type(
                control_word, synapse_index_bits, synapse_type_mask);
        uint32_t index =
                synapse_row_sparse_index(control_word, synapse_index_mask);
        uint32_t type_index = synapse_row_sparse_type_index(
                control_word, synapse_type_index_mask);

        uint32_t neuron_ind = synapse_row_sparse_index(
        		control_word, synapse_index_mask);

        // For low pass filter of incoming spike train on this synapse
        // Use postsynaptic neuron index to access neuron struct,

        if (type==1) {
        	// this is a recurrent synapse: add 100 to index to
        	// correct array location
        	syn_ind_from_delay += RECURRENT_SYNAPSE_OFFSET;
        }

        // Create update state from the plastic synaptic word
        update_state_t current_state =
                synapse_structure_get_update_state(*plastic_words, type);

        neuron_t *neuron = &neuron_array[neuron_ind];
        neuron->syn_state[syn_ind_from_delay].z_bar_inp = 1024.0k;
        // !!!! TODO: Check what units this is in - same as weight? !!!!

        // Perform weight update: only if batch time has elapsed
    	final_state_t final_state;
    	if (neuron->syn_state[syn_ind_from_delay].update_ready <= 0){
    		// enough time has elapsed - perform weight update
    		if (PRINT_PLASTICITY){
    			io_printf(IO_BUF, "update_ready=0\n");
    		}

            // Go through typical weight update process to clip to limits
    		final_state = eprop_plasticity_update(current_state,
        		neuron->syn_state[syn_ind_from_delay].delta_w);

    		// reset delta_w as weight change has now been applied
    		neuron->syn_state[syn_ind_from_delay].delta_w = 0.0k;

    		// reset update_ready counter based on pattern cycle time
    		neuron->syn_state[syn_ind_from_delay].update_ready += neuron->window_size;

    	} else {
    		if (PRINT_PLASTICITY){
    			io_printf(IO_BUF, "update_ready: %u/%u - no update performed\n",
    					neuron->syn_state[syn_ind_from_delay].update_ready, syn_ind_from_delay);
    		}
    		// don't update weight - get update state based on state cached in SDRAM
    		// assume reg rate is zero to avoid

    		final_state = synapse_structure_get_final_state(current_state, 0);
    		// Don't reset delta_w -> keep this accumulating and apply weight change in future
    	}

        // Add contribution to synaptic input
        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapse_row_get_ring_buffer_index_combined(
				time, type_index,
                synapse_type_index_bits, synapse_delay_mask);

        // Check for ring buffer saturation
        int16_t accumulation = ring_buffers[ring_buffer_index] +
                synapse_structure_get_final_weight(final_state);

        // overflow check
        if (accumulation < ring_buffers[ring_buffer_index] + (
        		synapse_structure_get_final_weight(final_state))
				&& ring_buffers[ring_buffer_index] > 0 && (
            		synapse_structure_get_final_weight(final_state) > 0)) {
            accumulation = ring_buffers[ring_buffer_index];
        }
        // underflow check
        if (accumulation > ring_buffers[ring_buffer_index] + (
        		synapse_structure_get_final_weight(final_state))
				&& ring_buffers[ring_buffer_index] < 0 && (
            		synapse_structure_get_final_weight(final_state) < 0)) {
            accumulation = ring_buffers[ring_buffer_index];
        }

        ring_buffers[ring_buffer_index] = accumulation;

        // Write back updated synaptic word to plastic region
        *plastic_words++ =
                synapse_structure_get_final_synaptic_word(final_state);
    }
    *write_back = true;
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

// TODO: fix below to match other dynamics impls? (Do we want structural plasticity
//       mixed with eprop??)

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
