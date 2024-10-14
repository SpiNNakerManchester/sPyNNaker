/*
 * Copyright (c) 2024 The University of Manchester
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

//! \file
//! \brief Allow weight change
#include "post_events_with_weight_change.h"
#include <neuron/synapses.h>
#include <neuron/plasticity/synapse_dynamics.h>
#include <stddef.h>

typedef struct limits {
	weight_t min;
	weight_t max;
} limits;

typedef struct change_params {
	uint32_t n_limits;
	limits weight_limits[];
} change_params;

typedef struct updatable_synapse_t {
    weight_t weight;
} updatable_synapse_t;

struct synapse_row_plastic_data_t {
    uint32_t pre_spike: 31;
    uint32_t is_update: 1;

    // This is only present if is_update is false
    updatable_synapse_t synapses[];
};

typedef struct fixed_stdp_synapse {
    uint32_t delay;
    uint32_t type;
    uint32_t index;
    uint32_t ring_buffer_index;
} fixed_stdp_synapse;

//! \brief The history data of post-events
static post_event_history_t *post_event_history;

//! Count of pre-synaptic events relevant to plastic processing
static uint32_t num_plastic_pre_synaptic_events = 0;

//! Count of times that the plastic math became saturated
static uint32_t plastic_saturation_count = 0;

//! Parameters
static change_params *params;

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        uint32_t n_synapse_types,
        UNUSED uint32_t *ring_buffer_to_input_buffer_left_shifts) {

	change_params *sdram_params = (change_params *) address;
	uint32_t size = sizeof(change_params) + (n_synapse_types * sizeof(limits));
	params = spin1_malloc(size);
	if (params == NULL) {
		log_error("Unable to allocate memory for params");
		return false;
	}
	spin1_memcpy(params, sdram_params, size);
	for (uint32_t i = 0; i < n_synapse_types; i++) {
		log_info("Synapse type %u: min = %d, max = %d", i,
				params->weight_limits[i].min, params->weight_limits[i].max);
	}

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        log_error("Failed to allocate post_event_history");
        return false;
    }

    return true;
}

//---------------------------------------
void synapse_dynamics_process_post_synaptic_event(
        UNUSED uint32_t time, UNUSED index_t neuron_index) {
    // Do Nothing - not needed here!
}

static inline fixed_stdp_synapse synapse_dynamics_stdp_get_fixed(
        uint32_t control_word, uint32_t time, uint32_t colour_delay) {
    // Extract control-word components
    // **NOTE** cunningly, control word is just the same as lower
    // 16-bits of 32-bit fixed synapse so same functions can be used
    uint32_t delay = synapse_row_sparse_delay(control_word,
            synapse_type_index_bits, synapse_delay_mask);
    uint32_t type_index = synapse_row_sparse_type_index(control_word,
            synapse_type_index_mask);
    uint32_t type = synapse_row_sparse_type(control_word, synapse_index_bits,
    		synapse_type_mask);
    uint32_t index = synapse_row_sparse_index(control_word, synapse_index_mask);
    return (fixed_stdp_synapse) {
       .delay = delay,
       .type = type,
	   .index = index,
       .ring_buffer_index = synapse_row_get_ring_buffer_index_combined(
                (delay + time) - colour_delay, type_index,
                synapse_type_index_bits, synapse_delay_mask)
    };
}

static inline void synapse_dynamics_stdp_update_ring_buffers(
        weight_t *ring_buffers, fixed_stdp_synapse s, int32_t weight) {
    uint32_t accumulation = ring_buffers[s.ring_buffer_index] + weight;

    uint32_t sat_test = accumulation & 0xFFFF0000;
    if (sat_test) {
        accumulation = 0xFFFF;
        plastic_saturation_count++;
    }

    ring_buffers[s.ring_buffer_index] = accumulation;
}

//---------------------------------------
static inline updatable_synapse_t process_plastic_synapse(
        uint32_t pre_spike, uint32_t control_word, weight_t *ring_buffers,
        uint32_t time, uint32_t colour_delay, updatable_synapse_t synapse,
        uint32_t *changed) {
    fixed_stdp_synapse s = synapse_dynamics_stdp_get_fixed(control_word, time,
            colour_delay);


    // Work out if the weight needs to be updated
    post_event_history_t *history = &post_event_history[s.index];
    weight_t min_weight = params->weight_limits[s.type].min;
    weight_t max_weight = params->weight_limits[s.type].max;
    log_debug("    Looking at change weight history 0x%08x of %u items to post"
    		" neuron index %u", history, history->count, s.index);
    for (uint32_t i = 0; i < history->count; i++) {
        update_post_trace_t *trace = &history->traces[i];
		log_debug(
				"        Checking history item %u, weight change %d for"
				" pre-neuron %u, synapse_type = %u",
				i, trace->weight_change, trace->pre_spike, trace->synapse_type);
        if (trace->pre_spike == pre_spike && s.type == trace->synapse_type) {
        	int32_t new_weight = synapse.weight + trace->weight_change;
            if (new_weight < min_weight) {
                synapse.weight = min_weight;
            } else if (new_weight > max_weight) {
                synapse.weight = max_weight;
            } else {
                synapse.weight = (weight_t) new_weight;
            }
            log_debug("        Weight now %d", synapse.weight);
            *changed = 1;

            // Remove the done item from history and then go back to make sure
            // we do the next one!
            if (post_events_remove(history, i)) {
                i--;
            }
        }
    }

    // Add weight to ring-buffer entry, but only if not too late
    if (s.delay > colour_delay) {
        synapse_dynamics_stdp_update_ring_buffers(ring_buffers, s,
                synapse.weight);
    } else {
        skipped_synapses++;
    }

    return synapse;
}

static inline int16_t change_sign(weight_t weight) {
    union {
        weight_t weight;
        int16_t value;
    } converter;
    converter.weight = weight;
    return converter.value;
}

static inline void process_weight_update(
        synapse_row_plastic_data_t *plastic_region_address,
        synapse_row_fixed_part_t *fixed_region) {
    uint32_t n_synapses = synapse_row_num_plastic_controls(fixed_region);
    const uint32_t *words = (uint32_t *) synapse_row_plastic_controls(fixed_region);
    uint32_t pre_spike = plastic_region_address->pre_spike;

	log_debug("Weight change update for pre-neuron %u", pre_spike);

    // Loop through synapses
    for (; n_synapses > 0; n_synapses--) {
        // Get next control word (auto incrementing)
        uint32_t word = *words++;
        int32_t weight_change = change_sign(synapse_row_sparse_weight(word));
        uint32_t synapse_type = synapse_row_sparse_type(word,
        		synapse_index_bits, synapse_type_mask);
        uint32_t neuron_index = synapse_row_sparse_index(word,
        		synapse_index_mask);

        log_debug("    Adding weight change %d to post-neuron %u",
						weight_change, neuron_index);

        // Get post event history of this neuron
        post_event_history_t *history = &post_event_history[neuron_index];

        // Add a new history trace into the buffer of post synaptic events
        post_events_add(history, weight_change, pre_spike, synapse_type);
    }
}

bool synapse_dynamics_process_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_address,
        synapse_row_fixed_part_t *fixed_region,
        weight_t *ring_buffers, uint32_t time, uint32_t colour_delay,
        bool *write_back) {

    // If the flag is set, this is neuromodulation
    if (plastic_region_address->is_update) {
        process_weight_update(plastic_region_address, fixed_region);
        *write_back = false;
        return true;
    }

    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    updatable_synapse_t *plastic_words = plastic_region_address->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    size_t n_plastic_synapses = synapse_row_num_plastic_controls(fixed_region);

    num_plastic_pre_synaptic_events += n_plastic_synapses;
    uint32_t pre_spike = plastic_region_address->pre_spike;

    log_debug("Checking for weight changes for pre-neuron %u", pre_spike);

    // Loop through plastic synapses
    for (; n_plastic_synapses > 0; n_plastic_synapses--) {
        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;
        uint32_t changed = 0;
        plastic_words[0] = process_plastic_synapse(pre_spike, control_word,
                ring_buffers, time, colour_delay, plastic_words[0], &changed);
        plastic_words++;
        if (changed) {
            *write_back = true;
        }
    }
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
