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
//! \brief Post-synaptic events
#ifndef _POST_EVENTS_H_
#define _POST_EVENTS_H_

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include <debug.h>
#include <stddef.h>

//---------------------------------------
// Macros
//---------------------------------------
//! Maximum number of pre-synaptic events per post neuron
#define MAX_EVENTS 16

typedef struct update_post_trace_t {

    //! The amount to change the weight by (positive or negative)
    int16_t weight_change;

    //! The synapse type
    uint16_t synapse_type;

    //! The pre-spike to look out for in doing the update
    uint32_t pre_spike;
} update_post_trace_t;

//---------------------------------------
// Structures
//---------------------------------------
//! Trace history of post-synaptic events
typedef struct {
    //! Number of events stored
    uint32_t count;
    //! Event traces
    update_post_trace_t traces[MAX_EVENTS];
} post_event_history_t;

//---------------------------------------
// Inline functions
//---------------------------------------

//! \brief Initialise an array of post-synaptic event histories
//! \param[in] n_neurons: Number of neurons
//! \return The array
static inline post_event_history_t *post_events_init_buffers(
        uint32_t n_neurons) {
    post_event_history_t *history =
            spin1_malloc(n_neurons * sizeof(post_event_history_t));
    // Check allocations succeeded
    if (history == NULL) {
        log_error("Unable to allocate global STDP structures - Out of DTCM: Try "
                "reducing the number of neurons per core to fix this problem ");
        return NULL;
    }

    // Loop through neurons and set count to 0
    for (uint32_t n = 0; n < n_neurons; n++) {
    	history[n].count = 0;
		for (uint32_t e = 0; e < MAX_EVENTS; e++) {
			history[n].traces[e].synapse_type = 0;
			history[n].traces[e].pre_spike = 0;
			history[n].traces[e].weight_change = 0;
		}
    }

    return history;
}

//---------------------------------------
//! \brief Add a post-synaptic event to the history
//! \param[in] time: the time of the event
//! \param[in,out] events: the history to add to
//! \param[in] trace: the trace of the event
static inline void post_events_add(
        post_event_history_t *events, uint16_t weight_change,
        uint32_t pre_spike, uint16_t synapse_type) {
    if (events->count < MAX_EVENTS) {
        // If there's still space, store time at current end
        // and increment count minus 1
        const uint32_t new_index = events->count++;
        events->traces[new_index].weight_change = weight_change;
        events->traces[new_index].pre_spike = pre_spike;
        events->traces[new_index].synapse_type = synapse_type;
		log_debug("Added pre spike %u with weight change %d to index %d", pre_spike,
			weight_change, new_index);
    } else {
    	log_debug("Events full, shuffling");
        // Otherwise Shuffle down elements
        for (uint32_t e = 1; e < MAX_EVENTS; e++) {
            events->traces[e - 1] = events->traces[e];
        }

        // Stick new time at end
        events->traces[MAX_EVENTS - 1].weight_change = weight_change;
        events->traces[MAX_EVENTS - 1].pre_spike = pre_spike;
        events->traces[MAX_EVENTS - 1].synapse_type = synapse_type;
    	log_debug("Added pre spike %u with weight change %d to index %d", pre_spike,
    			weight_change, MAX_EVENTS - 1);
    }
}

static inline bool post_events_remove(post_event_history_t *events, uint32_t index) {
    // Already gone? nothing to do!
    if (index >= events->count) {
        return false;
    }
    if (events->count > 1) {
        // Swap the last one with the one to remove
        events->traces[index] = events->traces[events->count - 1];
    }
    events->count--;
    return events->count > 0;
}

#endif  // _POST_EVENTS_H_
