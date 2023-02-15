/*
 * Copyright (c) 2017-2023 The University of Manchester
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
#include "post_events.h"
#include "synapse_dynamics_stdp_common.h"

//! The format of the plastic data region of a synaptic row
struct synapse_row_plastic_data_t {
    //! The pre-event history
    pre_event_history_t history;
    //! The per-synapse information
    plastic_synapse_t synapses[];
};

extern uint32_t skipped_synapses;

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
        log_debug("nA) d: %2u, n = %3u)] - {%08x %08x}\n",
                synapse_row_sparse_delay(control_word, synapse_type_index_bits, synapse_delay_mask),
                synapse_row_sparse_index(control_word, synapse_index_mask),
                synapse_delay_mask, synapse_type_index_bits);
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

//---------------------------------------
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

//---------------------------------------
static inline plastic_synapse_t process_plastic_synapse(
        uint32_t control_word, uint32_t last_pre_time, pre_trace_t last_pre_trace,
		pre_trace_t new_pre_trace, weight_t *ring_buffers, uint32_t time,
		uint32_t colour_delay, plastic_synapse_t synapse) {
    fixed_stdp_synapse s = synapse_dynamics_stdp_get_fixed(control_word, time,
            colour_delay);

	// Create update state from the plastic synaptic word
	update_state_t current_state = synapse_structure_get_update_state(
	        synapse, s.type);

	// Update the synapse state
	uint32_t post_delay = s.delay_dendritic;
	if (!params.backprop_delay) {
		post_delay = 0;
	}
	final_state_t final_state = plasticity_update_synapse(
			time - colour_delay, last_pre_time, last_pre_trace, new_pre_trace,
			post_delay, s.delay_axonal, current_state,
			&post_event_history[s.index]);

	// Add weight to ring-buffer entry, but only if not too late
	if (s.delay_axonal + s.delay_dendritic > colour_delay) {
	    int32_t weight = synapse_structure_get_final_weight(final_state);
	    synapse_dynamics_stdp_update_ring_buffers(ring_buffers, s, weight);
    } else {
        skipped_synapses++;
    }

	return synapse_structure_get_final_synaptic_word(final_state);
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
    size_t n_plastic_synapses = synapse_row_num_plastic_controls(fixed_region);

    num_plastic_pre_synaptic_events += n_plastic_synapses;

    // Get last pre-synaptic event from event history
    const uint32_t last_pre_time = plastic_region_address->history.prev_time;
    const pre_trace_t last_pre_trace = plastic_region_address->history.prev_trace;

    // Update pre-synaptic trace
    log_debug("Adding pre-synaptic event to trace at time:%u", time);
    plastic_region_address->history.prev_time = time - colour_delay;
    plastic_region_address->history.prev_trace =
            timing_add_pre_spike(time - colour_delay, last_pre_time, last_pre_trace);

    // Loop through plastic synapses
    for (; n_plastic_synapses > 0; n_plastic_synapses--) {
        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        plastic_words[0] = process_plastic_synapse(
                control_word, last_pre_time, last_pre_trace,
                plastic_region_address->history.prev_trace, ring_buffers, time,
                colour_delay, plastic_words[0]);
        plastic_words++;
    }
    *write_back = true;
    return true;
}

bool synapse_dynamics_find_neuron(
        uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay,
        uint32_t *offset, uint32_t *synapse_type) {
   synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    const synapse_row_plastic_data_t *plastic_data = (void *)
            synapse_row_plastic_region(row);
    const plastic_synapse_t *plastic_words = plastic_data->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    const size_t n_plastic_synapses = synapse_row_num_plastic_controls(fixed_region);

    // Loop through plastic synapses
    for (size_t plastic_synapse = n_plastic_synapses; plastic_synapse > 0;
            plastic_synapse--) {
        // Take the weight anyway as this updates the plastic words
        *weight = synapse_structure_get_weight(*plastic_words++);

        // Check if index is the one I'm looking for
        uint32_t control_word = *control_words++;
        if (synapse_row_sparse_index(control_word, synapse_index_mask) == id) {
            *offset = n_plastic_synapses - plastic_synapse;
            *delay = synapse_row_sparse_delay(control_word,
                    synapse_type_index_bits, synapse_delay_mask);
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

bool synapse_dynamics_add_neuron(uint32_t id, synaptic_row_t row,
        weight_t weight, uint32_t delay, uint32_t type) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    synapse_row_plastic_data_t *plastic_data = synapse_row_plastic_region(row);
    plastic_synapse_t *plastic_words = plastic_data->synapses;
    plastic_synapse_t new_weight = synapse_structure_create_synapse(weight);
    control_t new_control = control_conversion(id, delay, type);

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
