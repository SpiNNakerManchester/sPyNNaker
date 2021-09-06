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
//! \brief STDP-with-neuromodulation implementation
#include "post_events_with_da.h"
#include "synapse_dynamics_stdp_common.h"
#include "stdp_typedefs.h"

#define SMULBB_STDP_FIXED(a, b) (__smulbb(a, b) >> STDP_FIXED_POINT)

//! The format of the plastic data region of a synaptic row
struct synapse_row_plastic_data_t {
    uint32_t flags;
};

typedef struct stdp_plastic_data_t {
    //! The pre-event history
    pre_event_history_t history;
    //! The per-synapse information
    plastic_synapse_t synapses[];
} stdp_plastic_data_t;

static uint32_t weight_update_constant_component;

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
        bool dopamine, int32_t* weight_update, weight_state_t weight_state) {

    // Calculate EXP components of the weight update equation
    int32_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
        time - last_update_time);
    int32_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
        time - last_update_time);

    if (last_dopamine_trace != 0) {
        // Evaluate weight function
        int32_t temp = SMULBB_STDP_FIXED(
            SMULBB_STDP_FIXED(last_dopamine_trace, *previous_state),
            SMULBB_STDP_FIXED(decay_eligibility_trace, decay_dopamine_trace)
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
        int32_t* weight_update, weight_state_t weight_state) {

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
static inline plastic_synapse_t izhikevich_neuromodulation_plasticity_update_synapse(
        const uint32_t time,
        const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
        const pre_trace_t new_pre_trace, const uint32_t delay_dendritic,
        const uint32_t delay_axonal, plastic_synapse_t *current_state,
        const post_event_history_t *post_event_history,
        weight_state_t weight_state) {
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

    uint32_t prev_corr_time = delayed_last_pre_time;
    int32_t last_dopamine_trace = __smulbb(post_window.prev_trace,
            DECAY_LOOKUP_TAU_D(delayed_last_pre_time - post_window.prev_time))
            >> STDP_FIXED_POINT;
    bool next_trace_is_dopamine = false;
    int32_t weight_update = 0;

    // Process events in post-synaptic window
    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time = *post_window.next_time + delay_dendritic;

        log_debug("\t\tApplying post-synaptic event at delayed time:%u, pre:%u\n",
                delayed_post_time, delayed_last_pre_time);

        next_trace_is_dopamine = post_events_next_is_dopamine(post_window);
        
        // Apply spike to state
        correlation_apply_post_spike(
                delayed_post_time, *post_window.next_trace,
                delayed_last_pre_time, last_pre_trace,
                last_dopamine_trace,
                prev_corr_time, current_state,
                next_trace_is_dopamine,
                &weight_update, weight_state);

        // Update previous correlation to point to this post-event
        prev_corr_time = delayed_post_time;
        last_dopamine_trace = get_dopamine_trace(*post_window.next_trace);

        // Go onto next event
        post_window = post_events_next(post_window);
    }

    // Apply spike to state only if there has been a post spike ever
    if (post_window.prev_time_valid) {
        const uint32_t delayed_last_post = post_window.prev_time + delay_dendritic;
        log_debug("\t\tApplying pre-synaptic event at time:%u last post time:%u\n",
                delayed_pre_time, delayed_last_post);
        correlation_apply_pre_spike(
                delayed_pre_time, new_pre_trace, prev_corr_time, post_window.prev_trace,
                last_dopamine_trace, current_state, next_trace_is_dopamine, &weight_update, weight_state);
    }

    // Put total weight change into correct run-time weight fixed-point format
    // NOTE: Accuracy loss when shifting right.
    if (weight_state.weight_multiply_right_shift > STDP_FIXED_POINT) {
        weight_update <<=
           (weight_state.weight_multiply_right_shift - STDP_FIXED_POINT);
    } else {
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

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    if (!synapse_dynamics_stdp_init(&address, &params, n_synapse_types,
                ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    // Read Izhikevich weight update equation constant component
    weight_update_constant_component = address[0];

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
void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    log_debug("Adding post-synaptic event to trace at time:%u", time);

    // Add post-event
    post_event_history_t *history = &post_event_history[neuron_index];
    const uint32_t last_post_time = history->times[history->count_minus_one];
    const post_trace_t last_post_trace =
            history->traces[history->count_minus_one];
    post_events_add(time, history,
            timing_add_post_spike(time, last_post_time, last_post_trace), false);
}

//---------------------------------------
static inline void process_plastic_synapse(
        uint32_t control_word, uint32_t last_pre_time, pre_trace_t last_pre_trace,
		pre_trace_t new_pre_trace, weight_t *ring_buffers, uint32_t time,
		plastic_synapse_t* plastic_words) {
    fixed_stdp_synapse s = synapse_dynamics_stdp_get_fixed(control_word, time);

	// Get state of synapse - weight and eligibility trace.
	plastic_synapse_t* current_state = plastic_words;

	// Update the global weight_state
	weight_state_t weight_state = weight_get_initial(
		synapse_structure_get_eligibility_weight(*current_state), s.type);

	// Update the synapse state
	uint32_t post_delay = s.delay_dendritic;
	if (!params.backprop_delay) {
		post_delay = 0;
	}
	plastic_synapse_t final_state =
	    izhikevich_neuromodulation_plasticity_update_synapse(
            time, last_pre_time, last_pre_trace, new_pre_trace,
            post_delay, s.delay_axonal, current_state,
            &post_event_history[s.index], weight_state);

	// Add weight to ring-buffer entry
	int32_t weight = synapse_structure_get_eligibility_weight(final_state);
	synapse_dynamics_stdp_update_ring_buffers(ring_buffers, s, weight);

	*plastic_words++ = final_state;
}

static inline void process_neuromodulation(
        synapse_row_plastic_data_t *plastic_region_address,
        synapse_row_fixed_part_t *fixed_region, uint32_t time) {
    bool reward = plastic_region_address->flags & 0x40000000;
    uint32_t synapse_type = plastic_region_address->flags & 0x3FFFFFFF;
    uint32_t n_synapses = synapse_row_num_plastic_controls(fixed_region);
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    weight_t *weights = (void *) &plastic_region_address[1];

    // Loop through synapses
    for (; n_synapses > 0; n_synapses--) {
        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;
        int32_t concentration = (int32_t) *weights++;

        if (!reward) {
            concentration = -concentration;
        }

        uint32_t neuron_index = synapse_row_sparse_index(
                control_word, synapse_index_mask);

        // Get post event history of this neuron
        post_event_history_t *history = &post_event_history[neuron_index];
        const uint32_t last_post_time = history->times[history->count_minus_one];
        const post_trace_t last_post_trace =
            history->traces[history->count_minus_one];

        // Add a new history trace into the buffer of post synaptic events
        post_events_add(time, history, add_dopamine_spike(time,
            concentration, last_post_time, last_post_trace, synapse_type), true);
    }
}

bool synapse_dynamics_process_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_address,
        synapse_row_fixed_part_t *fixed_region,
        weight_t *ring_buffers, uint32_t time) {

    // If the flag is set, this is neuromodulation
    if (plastic_region_address->flags & 0x80000000) {
        process_neuromodulation(plastic_region_address, fixed_region, time);
        return true;
    }

    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    stdp_plastic_data_t *plastic_data = (void *) &plastic_region_address[1];
    plastic_synapse_t *plastic_words = plastic_data->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    size_t n_plastic_synapses = synapse_row_num_plastic_controls(fixed_region);

    num_plastic_pre_synaptic_events += n_plastic_synapses;

    // Get last pre-synaptic event from event history
    const uint32_t last_pre_time = plastic_data->history.prev_time;
    const pre_trace_t last_pre_trace = plastic_data->history.prev_trace;

    // Update pre-synaptic trace
    log_debug("Adding pre-synaptic event to trace at time:%u", time);
    plastic_data->history.prev_time = time;
    plastic_data->history.prev_trace =
            timing_add_pre_spike(time, last_pre_time, last_pre_trace);

    // Loop through plastic synapses
    for (; n_plastic_synapses > 0; n_plastic_synapses--) {
        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        process_plastic_synapse(
                control_word, last_pre_time, last_pre_trace,
                plastic_data->history.prev_trace, ring_buffers, time,
                plastic_words);
    }
    return true;
}

static inline plastic_synapse_t *get_plastic_synapses(synaptic_row_t row) {
    const synapse_row_plastic_data_t *plastic_data = (void *)
                synapse_row_plastic_region(row);
    stdp_plastic_data_t *stdp_plastic_data = (void *) &plastic_data[1];
    return stdp_plastic_data->synapses;
}

bool synapse_dynamics_find_neuron(
        uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay,
        uint32_t *offset, uint32_t *synapse_type) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    const plastic_synapse_t *plastic_words = get_plastic_synapses(row);

    return synapse_dynamics_stdp_find_neuron(id, plastic_words, fixed_region,
            weight, delay, offset, synapse_type);
}

bool synapse_dynamics_remove_neuron(uint32_t offset, synaptic_row_t row) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    plastic_synapse_t *plastic_words = get_plastic_synapses(row);

    return synapse_dynamics_stdp_remove_neuron(offset, fixed_region, plastic_words);
}

bool synapse_dynamics_add_neuron(uint32_t id, synaptic_row_t row,
        weight_t weight, uint32_t delay, uint32_t type) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    plastic_synapse_t *plastic_words = get_plastic_synapses(row);
    return synapse_dynamics_stdp_add_neuron(id, fixed_region, plastic_words,
            weight, delay, type);
}
