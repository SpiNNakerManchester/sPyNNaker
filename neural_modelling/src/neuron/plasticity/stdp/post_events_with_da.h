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
//! \brief Post-synaptic events
#ifndef _POST_EVENTS_H_
#define _POST_EVENTS_H_

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include <debug.h>

//---------------------------------------
// Macros
//---------------------------------------
//! Maximum number of post-synaptic events supported
#define MAX_POST_SYNAPTIC_EVENTS 16

typedef struct nm_post_trace_t {
    int16_t dopamine_trace;
    post_trace_t post_trace;
} nm_post_trace_t;

//---------------------------------------
// Structures
//---------------------------------------
//! Trace history of post-synaptic events
typedef struct {
    //! Number of events stored (minus one)
    uint32_t count_minus_one;
    //! Event times
    uint32_t times[MAX_POST_SYNAPTIC_EVENTS];
    //! Event traces
    nm_post_trace_t traces[MAX_POST_SYNAPTIC_EVENTS];
    //! Bit field to indicate whether a trace is dopamine or not
    uint32_t dopamine_trace_markers;
} post_event_history_t;

//! Post event window description
typedef struct {
    //! The previous post-synaptic event trace
    nm_post_trace_t prev_trace;
    //! The previous post-synaptic event time
    uint32_t prev_time;
    //! The next post-synaptic event trace
    const nm_post_trace_t *next_trace;
    //! The next post-synaptic event time
    const uint32_t *next_time;
    //! The number of events
    uint32_t num_events;
    //! Whether the previous post-synaptic event is valid (based on time)
    uint32_t prev_time_valid;
    //! Bit field to indicate whether a trace is dopamine or not
    uint32_t dopamine_trace_markers;
} post_event_window_t;

//---------------------------------------
// Inline functions
//---------------------------------------

#if LOG_LEVEL >= LOG_DEBUG
//! \brief Print a post-synaptic event history
//! \param[in] events: The history
static inline void print_event_history(const post_event_history_t *events) {
    log_debug("      ##  printing entire post event history  ##");
    for (uint32_t i = 0; i <= events->count_minus_one; i++) {
        log_debug("post event: %u, time: %u, trace: %u",
                i, events->times[i], events->traces[i]);
    }
}
#endif

//! \brief Initialise an array of post-synaptic event histories
//! \param[in] n_neurons: Number of neurons
//! \return The array
static inline post_event_history_t *post_events_init_buffers(
        uint32_t n_neurons) {
    post_event_history_t *post_event_history =
            spin1_malloc(n_neurons * sizeof(post_event_history_t));
    // Check allocations succeeded
    if (post_event_history == NULL) {
        log_error("Unable to allocate global STDP structures - Out of DTCM: Try "
                "reducing the number of neurons per core to fix this problem ");
        return NULL;
    }

    // Loop through neurons
    for (uint32_t n = 0; n < n_neurons; n++) {
        // Add initial placeholder entry to buffer
        post_event_history[n].times[0] = 0;
        post_event_history[n].traces[0].dopamine_trace = 0;
        post_event_history[n].traces[0].post_trace =
                timing_get_initial_post_trace();
        post_event_history[n].count_minus_one = 0;
        post_event_history[n].dopamine_trace_markers = 0x00000000;
    }

    return post_event_history;
}

//---------------------------------------
//! \brief Get the post-synaptic event window
//! \param[in] events: The post-synaptic event history
//! \param[in] begin_time: The start of the window
//! \param[in] end_time: The end of the window
//! \return The window
static inline post_event_window_t post_events_get_window_delayed(
        const post_event_history_t *events, uint32_t begin_time,
        uint32_t end_time) {
    // Start at end event - beyond end of post-event history
    const uint32_t count = events->count_minus_one + 1;
    const uint32_t *end_event_time = events->times + count;
    const uint32_t *event_time = end_event_time;
    const nm_post_trace_t *event_trace = events->traces + count;

    post_event_window_t window;
    do {
        // If this event is still in the future, set it as the end
        if (*event_time > end_time) {
            end_event_time = event_time;
        }

        // Cache pointer to this event as potential next event and go back one
        // event.
        // **NOTE** next_time can be invalid
        window.next_time = event_time--;
        window.next_trace = event_trace--;

        // Keep looping while event occurred after start of window and we
        // haven't hit beginning of array...
    } while (*event_time > begin_time && event_time != events->times);

    // Deference event to use as previous
    window.prev_time = *event_time;
    window.prev_trace = *event_trace;
    window.prev_time_valid = event_time != events->times;

    // Calculate number of events
    window.num_events = (end_event_time - window.next_time);

    // Find a vector of dopamine trace markers, with the LSB
    // entry in the vector corresponding to the oldest trace in the window
    window.dopamine_trace_markers =
        events->dopamine_trace_markers >> (count - window.num_events);

    // Return window
    return window;
}

//---------------------------------------
//! \brief Advance a post-synaptic event window to the next event
//! \param[in] window: The window to advance
//! \return the advanced window
static inline post_event_window_t post_events_next(
        post_event_window_t window) {
    // Update previous time and increment next time
    window.prev_time = *window.next_time++;
    window.prev_trace = *window.next_trace++;

    // Time will now be valid for sure!
    window.prev_time_valid = 1;

    // Decrement remaining events
    window.num_events--;

    // Shift the dopamine trace markers to place the next trace marker at LSB
    window.dopamine_trace_markers >>= 1;
    return window;
}

//---------------------------------------

// Check the LSB of dopamine trace marker vector to figure out whether the
// oldest trace in the given history trace window is dopamine trace
static inline bool post_events_next_is_dopamine(
        post_event_window_t window) {
    return (window.dopamine_trace_markers & 0x1) != 0x0;
}

//---------------------------------------
//! \brief Add a post-synaptic event to the history
//! \param[in] time: the time of the event
//! \param[in,out] events: the history to add to
//! \param[in] trace: the trace of the event
static inline void post_events_add(
        uint32_t time, post_event_history_t *events, post_trace_t post_trace,
        int16_t dopamine_trace, bool dopamine) {
    if (events->count_minus_one < MAX_POST_SYNAPTIC_EVENTS - 1) {
        // If there's still space, store time at current end
        // and increment count minus 1
        const uint32_t new_index = ++events->count_minus_one;
        events->times[new_index] = time;
        events->traces[new_index].post_trace = post_trace;
        events->traces[new_index].dopamine_trace = dopamine_trace;
        if (dopamine) {
            events->dopamine_trace_markers |= (1 << new_index);
        } else {
            events->dopamine_trace_markers &= ~(1 << new_index);
        }
    } else {
        // Otherwise Shuffle down elements
        // **NOTE** 1st element is always an entry at time 0
        for (uint32_t e = 2; e < MAX_POST_SYNAPTIC_EVENTS; e++) {
            events->times[e - 1] = events->times[e];
            events->traces[e - 1] = events->traces[e];
        }
        events->dopamine_trace_markers >>= 1;

        // Stick new time at end
        events->times[MAX_POST_SYNAPTIC_EVENTS - 1] = time;
        events->traces[MAX_POST_SYNAPTIC_EVENTS - 1].post_trace = post_trace;
        events->traces[MAX_POST_SYNAPTIC_EVENTS - 1].dopamine_trace = dopamine_trace;
        if (dopamine) {
            events->dopamine_trace_markers |=
                (1 << (MAX_POST_SYNAPTIC_EVENTS - 1));
        } else {
            events->dopamine_trace_markers &=
                ~(1 << (MAX_POST_SYNAPTIC_EVENTS - 1));
        }
    }
}

#if LOG_LEVEL >= LOG_DEBUG
//! \brief Print the post-synaptic event history
//! \param[in] post_event_history: the history
//! \param[in] begin_time: The start time of the history
//! \param[in] end_time: The end time of the history
//! \param[in] delay_dendritic: The amount of dendritic delay
static inline void print_delayed_window_events(
        const post_event_history_t *post_event_history,
        uint32_t begin_time, uint32_t end_time, uint32_t delay_dendritic) {
    log_info("     ##  printing post window  ##");
    post_event_window_t post_window = post_events_get_window_delayed(
            post_event_history, begin_time, end_time);

    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time =
                *post_window.next_time + delay_dendritic;
        log_info("post spike: %u, time: %u, trace: %u, dop_trace: %u",
                post_window.num_events, delayed_post_time,
                post_window.next_trace->post_trace,
                post_window.next_trace->dopamine_trace);

        post_window = post_events_next(post_window);
    }
}
#endif

#endif  // _POST_EVENTS_H_
