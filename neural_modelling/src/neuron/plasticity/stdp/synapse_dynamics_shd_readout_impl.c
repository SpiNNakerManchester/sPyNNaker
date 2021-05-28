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
#include <neuron/synapses.h>

// Plasticity includes
#include "maths.h"
#include "post_events.h"

#include "weight_dependence/weight.h"
#include "timing_dependence/timing.h"
#include <debug.h>
#include <utils.h>
#include <neuron/plasticity/synapse_dynamics.h>


#include <neuron/models/neuron_model.h>
//#include <neuron/models/neuron_model_eprop_adaptive_impl.h>
#include <neuron/models/neuron_model_shd_readout_impl.h>

extern neuron_pointer_t neuron_array;
extern global_neuron_params_pointer_t global_parameters;

static uint32_t synapse_type_index_bits;
static uint32_t synapse_index_bits;
static uint32_t synapse_index_mask;
static uint32_t synapse_type_index_mask;
static uint32_t synapse_delay_index_type_bits;
static uint32_t synapse_type_mask;

uint32_t num_plastic_pre_synaptic_events = 0;
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


uint32_t RECURRENT_SYNAPSE_OFFSET = 100;

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
    pre_trace_t prev_trace;
    uint32_t prev_time;
} pre_event_history_t;

post_event_history_t *post_event_history;

/* PRIVATE FUNCTIONS */

//---------------------------------------
// Synapse update loop
//---------------------------------------
//static inline final_state_t plasticity_update_synapse(
//        uint32_t time,
//        const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
//        const pre_trace_t new_pre_trace, const uint32_t delay_dendritic,
//        const uint32_t delay_axonal, update_state_t current_state,
//        const post_event_history_t *post_event_history) {
//    // Apply axonal delay to time of last presynaptic spike
//    const uint32_t delayed_last_pre_time = last_pre_time + delay_axonal;
//
//    // Get the post-synaptic window of events to be processed
//    const uint32_t window_begin_time =
//            (delayed_last_pre_time >= delay_dendritic)
//            ? (delayed_last_pre_time - delay_dendritic) : 0;
//    const uint32_t window_end_time = time + delay_axonal - delay_dendritic;
//    post_event_window_t post_window = post_events_get_window_delayed(
//            post_event_history, window_begin_time, window_end_time);
//
//    log_debug("\tPerforming deferred synapse update at time:%u", time);
//    log_debug("\t\tbegin_time:%u, end_time:%u - prev_time:%u, num_events:%u",
//            window_begin_time, window_end_time, post_window.prev_time,
//            post_window.num_events);
//
//    // print_event_history(post_event_history);
//    // print_delayed_window_events(post_event_history, window_begin_time,
//    //		   window_end_time, delay_dendritic);
//
//    // Process events in post-synaptic window
//    while (post_window.num_events > 0) {
//        const uint32_t delayed_post_time =
//                *post_window.next_time + delay_dendritic;
//        log_debug("\t\tApplying post-synaptic event at delayed time:%u\n",
//                delayed_post_time);
//
//        // Apply spike to state
//        current_state = timing_apply_post_spike(
//                delayed_post_time, *post_window.next_trace, delayed_last_pre_time,
//                last_pre_trace, post_window.prev_time, post_window.prev_trace,
//                current_state);
//
//        // Go onto next event
//        post_window = post_events_next_delayed(post_window, delayed_post_time);
//    }
//
//    const uint32_t delayed_pre_time = time + delay_axonal;
//    log_debug("\t\tApplying pre-synaptic event at time:%u last post time:%u\n",
//            delayed_pre_time, post_window.prev_time);
//
//    // Apply spike to state
//    // **NOTE** dendritic delay is subtracted
//    current_state = timing_apply_pre_spike(
//            delayed_pre_time, new_pre_trace, delayed_last_pre_time, last_pre_trace,
//            post_window.prev_time, post_window.prev_trace, current_state);
//
//    // Return final synaptic word and weight
//    return synapse_structure_get_final_state(current_state);
//}

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
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
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

    return weight_result;
}


static inline final_state_t eprop_plasticity_update(update_state_t current_state,
		REAL delta_w){

	// Test weight change
    // delta_w = -0.1k;


	// Convert delta_w to int16_t (same as weight) - take only integer bits from REAL?
//	int32_t delta_w_int = bitsk(delta_w); // THIS NEEDS UPDATING TO APPROPRIATE SCALING
	int32_t delta_w_int = (int32_t)roundk(delta_w, 15); // THIS NEEDS UPDATING TO APPROPRIATE SCALING
//	int32_t delta_w_int_shift = (int32_t)roundk(delta_w << 3, 15); // THIS NEEDS UPDATING TO APPROPRIATE SCALING
//	int16_t delta_w_int = (int) delta_w; // >> 15;

    if (delta_w){
        if (PRINT_PLASTICITY){
            io_printf(IO_BUF, "delta_w: %k, delta_w_int: %d"
//                    ", 16b delta_w_int: %d, delta << 7: %d, delta << 9: %d, delta << 11: %d"
                    "\n",
                    delta_w, delta_w_int
//                    , (int16_t)delta_w_int, (int16_t)(delta_w_int << 7), (int16_t)(delta_w_int << 9), (int16_t)(delta_w_int << 11)
                    );
//            io_printf(IO_BUF, "shift delta_w_int: %d, 16b delta_w_int: %d, delta << 7: %d, delta << 9: %d, delta << 11: %d\n",
//                    delta_w_int_shift, (int16_t)delta_w_int_shift, (int16_t)(delta_w_int_shift << 1), (int16_t)(delta_w_int_shift << 2), (int16_t)(delta_w_int_shift << 4));
        }

        if (delta_w_int < 0){
            current_state = weight_one_term_apply_depression(current_state,  (int16_t)(delta_w_int << 0));
        } else {
            current_state = weight_one_term_apply_potentiation(current_state,  (int16_t)(delta_w_int << 0));
        }
    }
	else {
//        if (PRINT_PLASTICITY){
//            io_printf(IO_BUF, "delta_w: %k\n", delta_w);
//        }
		current_state = current_state;
	}

	// Calculate regularisation error
	REAL reg_error = 0.0; //global_parameters->core_target_rate - global_parameters->core_pop_rate;


    // Return final synaptic word and weight
    return synapse_structure_get_final_state(current_state, reg_error);
}




bool synapse_dynamics_process_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        weight_t *ring_buffers, uint32_t time) {
    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    plastic_synapse_t *plastic_words =
            plastic_synapses(plastic_region_address);
    const control_t *control_words =
            synapse_row_plastic_controls(fixed_region_address);
    size_t plastic_synapse =
            synapse_row_num_plastic_controls(fixed_region_address);

    num_plastic_pre_synaptic_events += plastic_synapse;

    // Could maybe have a single z_bar for the entire synaptic row and update it once here for all synaptic words?



    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {
        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        // Extract control-word components
        // **NOTE** cunningly, control word is just the same as lower
        // 16-bits of 32-bit fixed synapse so same functions can be used
//        uint32_t delay_axonal = sparse_axonal_delay(control_word);

        uint32_t delay = 1.0k;
        uint32_t syn_ind_from_delay =
         		synapse_row_sparse_delay(control_word, synapse_type_index_bits);

//        uint32_t delay_dendritic = synapse_row_sparse_delay(
//                control_word, synapse_type_index_bits);
        uint32_t type = synapse_row_sparse_type(
                control_word, synapse_index_bits, synapse_type_mask);
        uint32_t index =
                synapse_row_sparse_index(control_word, synapse_index_mask);
        uint32_t type_index = synapse_row_sparse_type_index(
                control_word, synapse_type_index_mask);


        int32_t neuron_ind = synapse_row_sparse_index(control_word, synapse_index_mask);

        // For low pass filter of incoming spike train on this synapse
        // Use postsynaptic neuron index to access neuron struct,

        if (type==1){
        	// this is a recurrent synapse: add 100 to index to correct array location
        	syn_ind_from_delay += RECURRENT_SYNAPSE_OFFSET;
        }

        neuron_pointer_t neuron = &neuron_array[neuron_ind];
        neuron->syn_state[syn_ind_from_delay].z_bar_inp += 1024; // !!!! Check what units this is in - same as weight? !!!!


        // Create update state from the plastic synaptic word
        update_state_t current_state =
                synapse_structure_get_update_state(*plastic_words, type);

    	if (PRINT_PLASTICITY){
//            io_printf(IO_BUF, "neuron ind: %u, synapse ind: %u, type: %u, zbar: %k\n",
//                neuron_ind, syn_ind_from_delay, type, neuron->syn_state[syn_ind_from_delay].z_bar_inp);

    		io_printf(IO_BUF, "neuron ind: %u, synapse ind: %u, %type: %u init w (plas): %d, summed_dw: %k, time: %u\n",
        		neuron_ind, syn_ind_from_delay, type,
				current_state.initial_weight,
				neuron->syn_state[syn_ind_from_delay].delta_w, time);
    	}

        // Perform weight update: only if batch time has elapsed
    	final_state_t final_state;
//        if (time % 51 == 0){
//            io_printf(IO_BUF, "syn %u - update %u - +%u\n", syn_ind_from_delay,
//                neuron->syn_state[syn_ind_from_delay].update_ready, neuron->window_size);
//        }
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
            neuron->syn_state[syn_ind_from_delay].update_ready += neuron->window_size;// / 1000;

        } else {
            if (PRINT_PLASTICITY){
                io_printf(IO_BUF, "update_ready: %u - no update performed\n",
                        neuron->syn_state[syn_ind_from_delay].update_ready);
            }
            // don't update weight - get update state based on state cached in SDRAM
            // assume reg rate is zero to avoid

            final_state = synapse_structure_get_final_state(current_state, 0);
            // Don't reset delta_w -> keep this accumulating and apply weight change in future
        }

        // Add contribution to synaptic input
        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
                // delay_axonal + delay_dendritic +
				time, type_index,
                synapse_type_index_bits);

        // Check for ring buffer saturation
        int16_t accumulation = ring_buffers[ring_buffer_index] +
                synapse_structure_get_final_weight(final_state);
//        io_printf(IO_BUF, "d acc:%d, rb:%d, syn:%d\n", accumulation, ring_buffers[ring_buffer_index], synapse_structure_get_final_weight(final_state));
//        io_printf(IO_BUF, "u acc:%u, rb:%u, syn:%u\n", accumulation, ring_buffers[ring_buffer_index], synapse_structure_get_final_weight(final_state));
//        io_printf(IO_BUF, "k acc:%k, rb:%k, syn:%k\n", accumulation, ring_buffers[ring_buffer_index], synapse_structure_get_final_weight(final_state));
        // overflow check
//        if (accumulation < ring_buffers[ring_buffer_index] + synapse_structure_get_final_weight(final_state)
//            && ring_buffers[ring_buffer_index] > 0 && synapse_structure_get_final_weight(final_state) > 0){
//            accumulation = ring_buffers[ring_buffer_index];
//            plastic_saturation_count++;
//        }
//        // underflow check
//        if (accumulation > ring_buffers[ring_buffer_index] + synapse_structure_get_final_weight(final_state)
//            && ring_buffers[ring_buffer_index] < 0 && synapse_structure_get_final_weight(final_state) < 0){
//            accumulation = ring_buffers[ring_buffer_index];
//            plastic_saturation_count++;
//        }

        bool neg_sat_test = (accumulation < 0);
        bool neg_check_1 = (ring_buffers[ring_buffer_index] < 0);
        bool neg_check_2 = (synapse_structure_get_final_weight(final_state) < 0);
        if (neg_sat_test && !neg_check_1 && !neg_check_2) {
            accumulation = 0x8000 - 1;
            plastic_saturation_count++;
        }
        if (!neg_sat_test && neg_check_1 && neg_check_2) {
            accumulation = 0x8000;
            plastic_saturation_count++;
        }

//        uint32_t sat_test = accumulation & 0x10000;
//        if (sat_test) {
//            accumulation = sat_test - 1;
//            plastic_saturation_count++;
//        }

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
