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

// Include post_events and common
#include "post_events_with_da.h"
#include "synapse_dynamics_stdp_common.h"
#include "stdp_typedefs.h"

#define SMULBB_STDP_FIXED(a, b) (__smulbb(a, b) >> STDP_FIXED_POINT)

uint32_t weight_update_constant_component;
weight_state_t weight_state;

//---------------------------------------
// On each dopamine spike arrival, we add a new history trace in the post
// synaptic history trace buffer
static inline post_trace_t add_dopamine_spike(
        uint32_t time, int32_t concentration, uint32_t last_post_time,
        post_trace_t last_trace, uint32_t synapse_type) {

    // Get time since last dopamine spike
    uint32_t delta_time = time - last_post_time;

    // Apply exponential decay to get the current value of the dopamine
    // trace
    int32_t decayed_dopamine_trace = __smulbb(last_trace,
            DECAY_LOOKUP_TAU_D(delta_time)) >> STDP_FIXED_POINT;

    // Put dopamine concentration into STDP fixed-point format
    weight_state_t dop_weight_state = weight_get_initial(
        concentration, synapse_type);
    if (dop_weight_state.weight_multiply_right_shift > STDP_FIXED_POINT) {
        concentration >>=
           (dop_weight_state.weight_multiply_right_shift - STDP_FIXED_POINT);
    }
    else {
        concentration <<=
           (STDP_FIXED_POINT - dop_weight_state.weight_multiply_right_shift);
    }

    // Step increase dopamine trace due to new spike
    int32_t new_dopamine_trace = decayed_dopamine_trace + concentration;

    // Decay previous post trace
    int32_t decayed_last_post_trace = __smultb(
            last_trace,
            DECAY_LOOKUP_TAU_MINUS(delta_time)) >> STDP_FIXED_POINT;

    return (post_trace_t) trace_build(decayed_last_post_trace,
        new_dopamine_trace);
}

static inline void correlation_apply_post_spike(
        uint32_t time, UNUSED post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, int32_t last_dopamine_trace,
        uint32_t last_update_time, plastic_synapse_t *previous_state,
        bool dopamine, int32_t* weight_update) {

    // Calculate EXP components of the weight update equation
    int32_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
        time - last_update_time);
    int32_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
        time - last_update_time);

    if (last_dopamine_trace != 0) {
        // Evaluate weight function
        int32_t temp = SMULBB_STDP_FIXED(
            SMULBB_STDP_FIXED(last_dopamine_trace, *previous_state),
            SMULBB_STDP_FIXED(
                decay_eligibility_trace, decay_dopamine_trace)
                 - STDP_FIXED_POINT_ONE);

        *weight_update += maths_fixed_mul32(weight_update_constant_component,
                                                   temp, STDP_FIXED_POINT);
    }

    int32_t decayed_eligibility_trace = __smulbb(
        *previous_state, decay_eligibility_trace) >> STDP_FIXED_POINT;

    // Apply STDP to the eligibility trace if this spike is non-dopamine spike
    if (!dopamine) {
        // Apply STDP
        uint32_t time_since_last_pre = time - last_pre_time;
        if (time_since_last_pre > 0) {
            int32_t decayed_pre_trace = __smulbb(
                last_pre_trace, DECAY_LOOKUP_TAU_PLUS(time_since_last_pre)) >> STDP_FIXED_POINT;
            decayed_pre_trace = __smulbb(decayed_pre_trace,
                weight_state.weight_region->a2_plus) >> weight_state.weight_multiply_right_shift;
            decayed_eligibility_trace += decayed_pre_trace;
        }
    }

    // Update eligibility trace in synapse state
    *previous_state =
        synapse_structure_update_state(decayed_eligibility_trace,
            synapse_structure_get_eligibility_weight(*previous_state));
}

static inline void correlation_apply_pre_spike(
        uint32_t time, UNUSED pre_trace_t trace, uint32_t last_post_time,
        UNUSED post_trace_t last_post_trace, int32_t last_dopamine_trace,
        plastic_synapse_t *previous_state, UNUSED bool dopamine,
        int32_t* weight_update) {

    // Calculate EXP components of the weight update equation
    int32_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
        time - last_post_time);
    int32_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
        time - last_post_time);

    if (last_dopamine_trace != 0) {
        // Evaluate weight function
        int32_t temp = SMULBB_STDP_FIXED(
            SMULBB_STDP_FIXED(last_dopamine_trace, *previous_state),
            SMULBB_STDP_FIXED(
                decay_eligibility_trace, decay_dopamine_trace)
                 - STDP_FIXED_POINT_ONE);

        *weight_update += maths_fixed_mul32(weight_update_constant_component,
                                                   temp, STDP_FIXED_POINT);
    }

    int32_t decayed_eligibility_trace = __smulbb(
        *previous_state, decay_eligibility_trace) >> STDP_FIXED_POINT;

    // Apply STDP to the eligibility trace if this spike is non-dopamine spike
    uint32_t time_since_last_post = time - last_post_time;
    if (time_since_last_post > 0) {
        int32_t decayed_post_trace = __smultb(
            last_post_trace,
            DECAY_LOOKUP_TAU_MINUS(time_since_last_post)) >> STDP_FIXED_POINT;
        decayed_post_trace = __smulbb(decayed_post_trace,
            weight_state.weight_region->a2_minus) >> weight_state.weight_multiply_right_shift;
        decayed_eligibility_trace -= decayed_post_trace;
        if (decayed_eligibility_trace < 0) {
            decayed_eligibility_trace = 0;
        }
    }

    // Update eligibility trace in synapse state
    *previous_state =
        synapse_structure_update_state(decayed_eligibility_trace,
            synapse_structure_get_eligibility_weight(*previous_state));
}

// Synapse update loop
//---------------------------------------
static inline plastic_synapse_t izhikevich_neuromodulation_plasticity_update_synapse(
    const uint32_t time,
    const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
    const pre_trace_t new_pre_trace, const uint32_t delay_dendritic,
    const uint32_t delay_axonal, plastic_synapse_t *current_state,
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

    uint32_t prev_corr_time = delayed_last_pre_time;
    int32_t last_dopamine_trace = __smulbb(post_window.prev_trace,
            DECAY_LOOKUP_TAU_D(delayed_last_pre_time - post_window.prev_time))
            >> STDP_FIXED_POINT;
    bool next_trace_is_dopamine = false;
    int32_t weight_update = 0;

    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time =
            *post_window.next_time + delay_dendritic;
        next_trace_is_dopamine = post_events_next_is_dopamine(post_window);

        correlation_apply_post_spike(
            delayed_post_time, *post_window.next_trace,
            delayed_last_pre_time, last_pre_trace,
            last_dopamine_trace,
            prev_corr_time, current_state,
            next_trace_is_dopamine,
            &weight_update);

        // Update previous correlation to point to this post-event
        prev_corr_time = delayed_post_time;
        last_dopamine_trace = get_dopamine_trace(*post_window.next_trace);

        // Go onto next event
        post_window = post_events_next_delayed(post_window, delayed_post_time);
    }

    correlation_apply_pre_spike(
        delayed_pre_time, new_pre_trace,
        prev_corr_time, post_window.prev_trace,
        last_dopamine_trace, current_state,
        next_trace_is_dopamine,
        &weight_update);

    // Put total weight change into correct run-time weight fixed-point format
    // NOTE: Accuracy loss when shifting right.
    if (weight_state.weight_multiply_right_shift > STDP_FIXED_POINT) {
        weight_update <<=
           (weight_state.weight_multiply_right_shift - STDP_FIXED_POINT);
    }
    else {
        weight_update >>=
           (STDP_FIXED_POINT - weight_state.weight_multiply_right_shift);
    }

    int32_t new_weight = weight_update + synapse_structure_get_eligibility_weight(*current_state);

    // Saturate weight
    new_weight = MIN(weight_state.weight_region->max_weight,
                        MAX(new_weight,
                            weight_state.weight_region->min_weight));

    return synapse_structure_update_state(
        synapse_structure_get_eligibility_trace(*current_state),
        new_weight);
}

bool synapse_dynamics_stdp_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    // Load timing dependence data
    address_t weight_region_address = timing_initialise(address);
    if (address == NULL) {
        return false;
    }

    // Read Izhikevich weight update equation constant component
    weight_update_constant_component = *weight_region_address++;

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
static inline index_t sparse_axonal_delay(uint32_t x) {
    return ((x >> synapse_delay_bits) & SYNAPSE_AXONAL_DELAY_MASK);
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
    post_events_add(time, history, timing_add_post_spike(time, last_post_time,
                                                     last_post_trace), false);
}

//--------------------------------------
void synapse_dynamics_process_neuromodulator_event(
        uint32_t time, int32_t concentration, uint32_t neuron_index,
        uint32_t synapse_type) {
    log_debug(
        "Adding neuromodulation event to trace at time:%u concentration:%d type:%u",
        time, concentration, synapse_type);

    // Get post event history of this neuron
    post_event_history_t *history = &post_event_history[neuron_index];
    const uint32_t last_post_time = history->times[history->count_minus_one];
    const post_trace_t last_post_trace =
        history->traces[history->count_minus_one];

    // Add a new history trace into the buffer of post synaptic events
    post_events_add(time, history, add_dopamine_spike(time,
        concentration, last_post_time, last_post_trace, synapse_type), true);
}

bool synapse_dynamics_is_neuromodulated(uint32_t synapse_type) {
    if (synapse_type > 1) { // hard-coded still?
        return true;
    }
    else {
        return false;
    }
}

int32_t synapse_dynamics_get_concentration(uint32_t synapse_type, int32_t concentration) {
    if (synapse_type == 3) { // hard-coded still?
        concentration = ~concentration + 1;
    }
    return concentration;
}

//---------------------------------------
// can this be inlined?
void synapse_dynamics_stdp_process_plastic_synapse(
        uint32_t control_word, uint32_t last_pre_time, pre_trace_t last_pre_trace,
		pre_trace_t new_pre_trace, weight_t *ring_buffers, uint32_t time,
		plastic_synapse_t* plastic_words) {
	// Extract control-word components
	// **NOTE** cunningly, control word is just the same as lower
	// 16-bits of 32-bit fixed synapse so same functions can be used
	uint32_t delay_dendritic = synapse_row_sparse_delay(control_word,
		synapse_type_index_bits, synapse_delay_mask);
	uint32_t delay_axonal = 0;//sparse_axonal_delay(control_word);
	uint32_t type = synapse_row_sparse_type(
		control_word, synapse_index_bits, synapse_type_mask);
	uint32_t index = synapse_row_sparse_index(
		control_word, synapse_index_mask);
	uint32_t type_index = synapse_row_sparse_type_index(control_word,
		synapse_type_index_mask);

	// Convert into ring buffer index
	uint32_t ring_buffer_index = synapse_row_get_ring_buffer_index_combined(
		delay_axonal + delay_dendritic + time, type_index,
		synapse_type_index_bits, synapse_delay_mask);

	// Get state of synapse - weight and eligibility trace.
	plastic_synapse_t* current_state = plastic_words;

	// Update the global weight_state
	weight_state = weight_get_initial(
		synapse_structure_get_eligibility_weight(*current_state), type);

	// Update the synapse state
	uint32_t post_delay = delay_dendritic;
	if (!params.backprop_delay) {
		post_delay = 0;
	}
	plastic_synapse_t final_state = izhikevich_neuromodulation_plasticity_update_synapse(
		time, last_pre_time, last_pre_trace, new_pre_trace,
		post_delay, delay_axonal, current_state,
		&post_event_history[index]);

	// Add weight to ring-buffer entry (deal with saturation)
	uint32_t accumulation = ring_buffers[ring_buffer_index] +
			synapse_structure_get_eligibility_weight(final_state);

	uint32_t sat_test = accumulation & 0x10000;
	if (sat_test) {
		accumulation = sat_test - 1;
		plastic_saturation_count++;
	}

	ring_buffers[ring_buffer_index] = accumulation;

	*plastic_words++ = final_state;
}
