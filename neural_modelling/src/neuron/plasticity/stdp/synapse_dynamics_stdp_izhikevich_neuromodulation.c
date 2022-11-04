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

typedef struct neuromodulation_data_t {
    uint32_t synapse_type:30;
    uint32_t is_reward:1;
    uint32_t is_neuromodulation: 1;
} neuromodulation_data_t;

typedef struct neuromodulated_synapse_t {
    weight_t weight;
    plastic_synapse_t eligibility_synapse;
} neuromodulated_synapse_t;

typedef struct nm_update_state_t {
    accum weight;
    uint32_t weight_shift;
    update_state_t eligibility_state;
} nm_update_state_t;

typedef struct nm_final_state_t {
    weight_t weight;
    final_state_t final_state;
} nm_final_state_t;

struct synapse_row_plastic_data_t {
    union {
        struct {
            //! The pre-event history
            pre_event_history_t history;
            //! The per-synapse information
            neuromodulated_synapse_t synapses[];
        };
        //! Neuromodulation data
        neuromodulation_data_t neuromodulation;
    };
};

typedef struct nm_params_t {

    //! Constant part of weight update
    accum weight_update_constant_component;

    //! Maximum of weight after update
    accum max_weight;

    //! Minimum of weight after update (must be >= 0)
    accum min_weight;

} nm_params_t;

static nm_params_t nm_params;

static int16_lut *tau_c_lookup;

static int16_lut *tau_d_lookup;

static uint32_t *nm_weight_shift;

extern uint32_t skipped_synapses;

#define DECAY_LOOKUP_TAU_C(time) \
    maths_lut_exponential_decay(time, tau_c_lookup)
#define DECAY_LOOKUP_TAU_D(time) \
    maths_lut_exponential_decay(time, tau_d_lookup)

static inline nm_update_state_t get_nm_update_state(
        neuromodulated_synapse_t synapse, index_t synapse_type) {
    accum s1615_weight = kbits(synapse.weight << nm_weight_shift[synapse_type]);
    nm_update_state_t update_state = {
        .weight=s1615_weight,
        .weight_shift=nm_weight_shift[synapse_type],
        .eligibility_state=synapse_structure_get_update_state(
                synapse.eligibility_synapse, synapse_type)
    };
    return update_state;
}

static inline nm_final_state_t get_nm_final_state(
        nm_update_state_t update_state) {
    update_state.weight = kbits(MAX(bitsk(update_state.weight),
            bitsk(nm_params.min_weight)));
    update_state.weight = kbits(MIN(bitsk(update_state.weight),
            bitsk(nm_params.max_weight)));
    nm_final_state_t final_state = {
        .weight=(weight_t) (bitsk(update_state.weight) >> update_state.weight_shift),
        .final_state=synapse_structure_get_final_state(
                update_state.eligibility_state)
    };
    return final_state;
}

static inline neuromodulated_synapse_t get_nm_final_synaptic_word(
        nm_final_state_t final_state) {
    neuromodulated_synapse_t synapse = {
        .weight=final_state.weight,
        .eligibility_synapse=synapse_structure_get_final_synaptic_word(
                final_state.final_state)
    };
    return synapse;
}

static inline post_event_window_t get_post_event_window(
        const post_event_history_t * post_event_history,
        const uint32_t delayed_pre_time, const uint32_t delayed_last_pre_time,
        const uint32_t delay_dendritic) {
    // Get the post-synaptic window of events to be processed
    const uint32_t window_begin_time =
            (delayed_last_pre_time >= delay_dendritic)
            ? (delayed_last_pre_time - delay_dendritic) : 0;
    const uint32_t window_end_time =
            (delayed_pre_time >= delay_dendritic)
            ? (delayed_pre_time - delay_dendritic) : 0;
    post_event_window_t post_window = post_events_get_window_delayed(
            post_event_history, window_begin_time, window_end_time);

    log_debug("\t\tbegin_time:%u, end_time:%u - prev_time:%u (valid %u), num_events:%u",
            window_begin_time, window_end_time, post_window.prev_time,
            post_window.prev_time_valid, post_window.num_events);

#if LOG_LEVEL >= LOG_DEBUG
    print_event_history(post_event_history);
    print_delayed_window_events(post_event_history, window_begin_time,
            window_end_time, delay_dendritic);
#endif
    return post_window;
}

static inline accum get_weight_update(int16_t decay_eligibility_trace,
        int16_t decay_dopamine_trace, int16_t last_dopamine_trace,
        accum eligibility_weight) {
    // (exp(-(t_j - t_c) / tau_C).exp(-(t_j - t_c) / tau_D) - 1)
    int16_t mul_decay = STDP_FIXED_MUL_16X16(
            decay_eligibility_trace, decay_dopamine_trace)
                    - STDP_FIXED_POINT_ONE;
    // C_ij.D_c
    accum mul_trace = mul_accum_fixed(eligibility_weight, last_dopamine_trace);
    // C_ij.D_c.(exp(-(t_j - t_c) / tau_C).exp(-(t_j - t_c) / tau_D) - 1)
    accum mul_trace_decay = mul_accum_fixed(mul_trace, mul_decay);
    // Constant component = 1 / -((1/tau_C) + (1/tau_D))
    // const_component.C_ij.D_c.
    //        (exp(-(t_j - t_c) / tau_C).exp(-(t_j - t_c) / tau_D) - 1)
    accum res =  mul_trace_decay * nm_params.weight_update_constant_component;
    return res;
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
static inline nm_final_state_t izhikevich_neuromodulation_plasticity_update_synapse(
        const uint32_t time,
        const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
        const pre_trace_t new_pre_trace, const uint32_t delay_dendritic,
        const uint32_t delay_axonal, nm_update_state_t current_state,
        const post_event_history_t *post_event_history) {
    log_debug("\tPerforming deferred synapse update at time:%u", time);
    // Apply axonal delay to time of last presynaptic spike
    const uint32_t delayed_last_pre_time = last_pre_time + delay_axonal;
    const uint32_t delayed_pre_time = time + delay_axonal;

    // history <- getHistoryEntries(j, t_old, t)
    post_event_window_t post_window = get_post_event_window(
            post_event_history, delayed_pre_time,
            delayed_last_pre_time, delay_dendritic);

    // t_c = t_old
    uint32_t prev_corr_time = delayed_last_pre_time;

    // D_c = D_prev.exp(-t_c - t_prev / tau_D)
    int16_t last_dopamine_trace = 0;
    if (post_window.prev_time_valid) {
        last_dopamine_trace = STDP_FIXED_MUL_16X16(
            post_window.prev_trace.dopamine_trace,
            DECAY_LOOKUP_TAU_D(delayed_last_pre_time - post_window.prev_time));
    }

    // Process events in post-synaptic window
    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time = *post_window.next_time + delay_dendritic;

        log_debug("\t\tApplying post-synaptic event at delayed time:%u, pre:%u, prev_corr:%u",
                delayed_post_time, delayed_last_pre_time, prev_corr_time);

        // Calculate EXP components of the weight update equation
        int16_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
            delayed_post_time - prev_corr_time);

        // No point if dopamine trace is 0 as will just multiply by 0
        if (last_dopamine_trace != 0) {
            int16_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
                        delayed_post_time - prev_corr_time);
            accum eligibility_weight = synapse_structure_get_update_weight(
                    current_state.eligibility_state);
            current_state.weight += get_weight_update(decay_eligibility_trace,
                    decay_dopamine_trace, last_dopamine_trace, eligibility_weight);
        }

        // C_ij = C_ij.exp(-(t_j-t_c) / tau_C)
        synapse_structure_decay_weight(&(current_state.eligibility_state),
                decay_eligibility_trace);

        if (!post_events_next_is_dopamine(post_window)) {
            current_state.eligibility_state = timing_apply_post_spike(
                delayed_post_time, post_window.next_trace->post_trace,
                delayed_last_pre_time, last_pre_trace, post_window.prev_time,
                post_window.prev_trace.post_trace, current_state.eligibility_state);
        }

        // Update previous correlation to point to this post-event
        // D_c = D_j
        last_dopamine_trace = post_window.next_trace->dopamine_trace;
        // t_c = t_j
        prev_corr_time = delayed_post_time;

        // Go onto next event
        post_window = post_events_next(post_window);
    }

    // Apply spike to state only if there has been a post spike ever
    if (post_window.prev_time_valid) {
        const uint32_t delayed_last_post = post_window.prev_time + delay_dendritic;
        log_debug("\t\tApplying pre-synaptic event at time:%u last post time:%u, prev_corr=%u",
                delayed_pre_time, delayed_last_post, prev_corr_time);
        int32_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
                delayed_pre_time - prev_corr_time);

        if (last_dopamine_trace != 0) {
            int32_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
                    delayed_pre_time - prev_corr_time);
            accum eligibility_weight = synapse_structure_get_update_weight(
                    current_state.eligibility_state);
            current_state.weight += get_weight_update(decay_eligibility_trace,
                    decay_dopamine_trace, last_dopamine_trace, eligibility_weight);
        }

        // C_ij = C_ij.exp(-(t-t_c) / tau_C)
        synapse_structure_decay_weight(&(current_state.eligibility_state),
                decay_eligibility_trace);

        current_state.eligibility_state = timing_apply_pre_spike(
            delayed_pre_time, new_pre_trace, delayed_last_pre_time, last_pre_trace,
            delayed_last_post, post_window.prev_trace.post_trace,
            current_state.eligibility_state);
    }

    return get_nm_final_state(current_state);
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

    // Load parameters
    nm_params_t *sdram_params = (nm_params_t *) address;
    spin1_memcpy(&nm_params, sdram_params, sizeof(nm_params_t));

    log_info("Constant %k, min weight %k, max weight %k",
            nm_params.weight_update_constant_component,
            nm_params.min_weight, nm_params.max_weight);

    // Read lookup tables
    address_t lut_address = (void *) &sdram_params[1];
    tau_c_lookup = maths_copy_int16_lut(&lut_address);
    tau_d_lookup = maths_copy_int16_lut(&lut_address);

    // Store weight shifts
    nm_weight_shift = spin1_malloc(sizeof(uint32_t) * n_synapse_types);
    if (nm_weight_shift == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    for (uint32_t s = 0; s < n_synapse_types; s++) {
        nm_weight_shift[s] = ring_buffer_to_input_buffer_left_shifts[s];
        log_info("Weight shift %u = %u", s, nm_weight_shift[s]);
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
    log_debug("Adding post-synaptic event to trace %u at time:%u", neuron_index, time);

    // Add post-event
    post_event_history_t *history = &post_event_history[neuron_index];
    const uint32_t last_post_time = history->times[history->count_minus_one];
    const nm_post_trace_t last_post_trace =
            history->traces[history->count_minus_one];
    post_trace_t new_post_trace = timing_add_post_spike(
            time, last_post_time, last_post_trace.post_trace);
    int32_t new_dopamine_trace = STDP_FIXED_MUL_16X16(
            last_post_trace.dopamine_trace,
            DECAY_LOOKUP_TAU_D(time - last_post_time));

    post_events_add(time, history, new_post_trace, new_dopamine_trace, false);
}

//---------------------------------------
static inline neuromodulated_synapse_t process_plastic_synapse(
        uint32_t control_word, uint32_t last_pre_time, pre_trace_t last_pre_trace,
		pre_trace_t new_pre_trace, weight_t *ring_buffers, uint32_t time,
		uint32_t colour_delay, neuromodulated_synapse_t synapse) {
    fixed_stdp_synapse s = synapse_dynamics_stdp_get_fixed(control_word, time,
            colour_delay);

    // Create update state from the plastic synaptic word
    nm_update_state_t current_state = get_nm_update_state(synapse, s.type);

	// Update the synapse state
	uint32_t post_delay = s.delay_dendritic;
	if (!params.backprop_delay) {
		post_delay = 0;
	}
	nm_final_state_t final_state =
	    izhikevich_neuromodulation_plasticity_update_synapse(
            time - colour_delay, last_pre_time, last_pre_trace, new_pre_trace,
            post_delay, s.delay_axonal, current_state,
            &post_event_history[s.index]);

	// Add weight to ring-buffer entry, but only if not too late
    if (s.delay_dendritic + s.delay_axonal >= colour_delay) {
        synapse_dynamics_stdp_update_ring_buffers(ring_buffers, s,
                final_state.weight);
    } else {
        skipped_synapses++;
    }

    return get_nm_final_synaptic_word(final_state);
}

static inline void process_neuromodulation(
        synapse_row_plastic_data_t *plastic_region_address,
        synapse_row_fixed_part_t *fixed_region, uint32_t time) {
    bool reward = plastic_region_address->neuromodulation.is_reward;
    uint32_t n_synapses = synapse_row_num_plastic_controls(fixed_region);
    const uint32_t *words = (uint32_t *) synapse_row_plastic_controls(fixed_region);

    // Loop through synapses
    for (; n_synapses > 0; n_synapses--) {
        // Get next control word (auto incrementing)
        uint32_t word = *words++;
        int32_t concentration = (int32_t) synapse_row_sparse_weight(word);

        if (!reward) {
            concentration = -concentration;
        }

        uint32_t neuron_index = synapse_row_sparse_index(word, 0xFFFF);

        // Get post event history of this neuron
        post_event_history_t *history = &post_event_history[neuron_index];
        const uint32_t last_post_time = history->times[history->count_minus_one];
        const nm_post_trace_t last_post_trace =
            history->traces[history->count_minus_one];

        post_trace_t new_post_trace = timing_decay_post(
                    time, last_post_time, last_post_trace.post_trace);
        int32_t new_dopamine_trace = STDP_FIXED_MUL_16X16(
                last_post_trace.dopamine_trace,
                DECAY_LOOKUP_TAU_D(time - last_post_time));
        new_dopamine_trace += concentration;

        // Add a new history trace into the buffer of post synaptic events
        post_events_add(time, history, new_post_trace, new_dopamine_trace, true);
    }
}

bool synapse_dynamics_process_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_address,
        synapse_row_fixed_part_t *fixed_region,
        weight_t *ring_buffers, uint32_t time, uint32_t colour_delay,
        bool *write_back) {

    // If the flag is set, this is neuromodulation
    if (plastic_region_address->neuromodulation.is_neuromodulation) {
        process_neuromodulation(plastic_region_address, fixed_region, time);
        *write_back = false;
        return true;
    }

    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    neuromodulated_synapse_t *plastic_words = plastic_region_address->synapses;
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

static inline neuromodulated_synapse_t *get_plastic_synapses(synaptic_row_t row) {
    synapse_row_plastic_data_t *plastic_data = (void *)
                synapse_row_plastic_region(row);
    return plastic_data->synapses;
}

bool synapse_dynamics_find_neuron(
        uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay,
        uint32_t *offset, uint32_t *synapse_type) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    const neuromodulated_synapse_t *plastic_words = get_plastic_synapses(row);
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    const size_t n_plastic_synapses = synapse_row_num_plastic_controls(fixed_region);

    // Loop through plastic synapses
    for (size_t plastic_synapse = n_plastic_synapses; plastic_synapse > 0;
            plastic_synapse--, plastic_words++) {
        // Take the weight anyway as this updates the plastic words

        // Check if index is the one I'm looking for
        uint32_t control_word = *control_words++;
        if (synapse_row_sparse_index(control_word, synapse_index_mask) == id) {
            *weight = synapse_structure_get_weight(
                    plastic_words->eligibility_synapse);
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
    neuromodulated_synapse_t *plastic_words = get_plastic_synapses(row);
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
    neuromodulated_synapse_t *plastic_words = get_plastic_synapses(row);
    plastic_synapse_t new_weight = synapse_structure_create_synapse(0);
    control_t new_control = control_conversion(id, delay, type);

    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Add weight at offset
    plastic_words[plastic_synapse] = (neuromodulated_synapse_t) {
        .eligibility_synapse = new_weight,
        .weight = weight
    };

    // Add control word at offset
    control_words[plastic_synapse] = new_control;

    // Increment FP
    fixed_region->num_plastic++;
    return true;
}
