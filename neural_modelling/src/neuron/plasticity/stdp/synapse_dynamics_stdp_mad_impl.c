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
#include "post_events.h"
#include "synapse_dynamics_stdp_common.h"

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
static inline final_state_t mad_plasticity_update_synapse(
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

bool synapse_dynamics_stdp_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    // Load timing dependence data
    address_t weight_region_address = timing_initialise(address);
    if (address == NULL) {
        return false;
    }

    // Load weight dependence data
    address_t weight_result = weight_initialise(
            weight_region_address, n_synapse_types,
            ring_buffer_to_input_buffer_left_shifts);
    if (weight_result == NULL) {
        return false;
    }

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        return false;
    }

    return true;
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
void synapse_dynamics_process_neuromodulator_event(
        UNUSED uint32_t time, UNUSED int32_t concentration,
        UNUSED uint32_t neuron_index, UNUSED uint32_t synapse_type) {
}

bool synapse_dynamics_is_neuromodulated(
        UNUSED uint32_t synaptic_word, UNUSED uint32_t synapse_index_bits,
        UNUSED uint32_t synapse_type_mask) {
    return false;
}

int32_t synapse_dynamics_get_concentration(
        UNUSED uint32_t synapse_type, UNUSED int32_t concentration) {
    return 0;
}

// can this be inlined?
void synapse_dynamics_stdp_process_plastic_synapse(
        uint32_t control_word, uint32_t last_pre_time, pre_trace_t last_pre_trace,
		pre_trace_t new_pre_trace, weight_t *ring_buffers, uint32_t time,
		plastic_synapse_t* plastic_words) {

	// Extract control-word components
	// **NOTE** cunningly, control word is just the same as lower
	// 16-bits of 32-bit fixed synapse so same functions can be used
	uint32_t delay_axonal = sparse_axonal_delay(control_word);
	uint32_t delay_dendritic = synapse_row_sparse_delay(
			control_word, synapse_type_index_bits, synapse_delay_mask);
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
	uint32_t ring_buffer_index = synapse_row_get_ring_buffer_index_combined(
			delay_axonal + delay_dendritic + time, type_index,
			synapse_type_index_bits, synapse_delay_mask);

	// Update the synapse state
	uint32_t post_delay = delay_dendritic;
	if (!params.backprop_delay) {
		post_delay = 0;
	}
	final_state_t final_state = mad_plasticity_update_synapse(
			time, last_pre_time, last_pre_trace, new_pre_trace,
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

	*plastic_words++ = synapse_structure_get_final_synaptic_word(final_state);
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
