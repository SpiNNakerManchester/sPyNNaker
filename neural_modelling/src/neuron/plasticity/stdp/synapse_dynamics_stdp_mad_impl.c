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
#include "post_events.h"
#include "synapse_dynamics_stdp_common.h"

/* PRIVATE FUNCTIONS */

//---------------------------------------
// Synapse update loop
//---------------------------------------
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

address_t synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    stdp_params *sdram_params = (stdp_params *) address;
    spin1_memcpy(&params, sdram_params, sizeof(stdp_params));
    address = (address_t) &sdram_params[1];

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

    return weight_result;
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

//---------------------------------------
void synapse_dynamics_process_neuromodulator_event(
        uint32_t time, int32_t concentration, uint32_t neuron_index,
        uint32_t synapse_type) {
    use(time);
    use(concentration);
    use(neuron_index);
    use(synapse_type);
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

    // Get event history from synaptic row
    pre_event_history_t *event_history =
            plastic_event_history(plastic_region_address);

    // Get last pre-synaptic event from event history
    const uint32_t last_pre_time = event_history->prev_time;
    const pre_trace_t last_pre_trace = event_history->prev_trace;

    // Update pre-synaptic trace
    log_debug("Adding pre-synaptic event to trace at time:%u", time);
    event_history->prev_time = time;
    event_history->prev_trace =
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
                time, last_pre_time, last_pre_trace, event_history->prev_trace,
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
