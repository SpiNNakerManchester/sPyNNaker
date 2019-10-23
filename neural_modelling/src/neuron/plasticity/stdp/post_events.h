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
#define MAX_POST_SYNAPTIC_EVENTS 16

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
    uint32_t count_minus_one;

    uint32_t times[MAX_POST_SYNAPTIC_EVENTS];
    post_trace_t traces[MAX_POST_SYNAPTIC_EVENTS];
} post_event_history_t;

typedef struct {
    post_trace_t prev_trace;
    uint32_t prev_time;
    const post_trace_t *next_trace;
    const uint32_t *next_time;
    uint32_t num_events;
    uint32_t prev_time_valid;
} post_event_window_t;

//---------------------------------------
// Inline functions
//---------------------------------------

static inline void print_event_history(const post_event_history_t *events) {
    log_info("      ##  printing entire post event history  ##");
    for (uint32_t i = 0; i <= events->count_minus_one; i++) {
        log_info("post event: %u, time: %u, trace: %u",
                i, events->times[i], events->traces[i]);
    }
}

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
        post_event_history[n].traces[0] = timing_get_initial_post_trace();
        post_event_history[n].count_minus_one = 0;
    }

    return post_event_history;
}

//---------------------------------------
static inline post_event_window_t post_events_get_window_delayed(
        const post_event_history_t *events, uint32_t begin_time,
        uint32_t end_time) {
    // Start at end event - beyond end of post-event history
    const uint32_t count = events->count_minus_one + 1;
    const uint32_t *end_event_time = events->times + count;
    const uint32_t *event_time = end_event_time;

    post_event_window_t window;
    do {
        // If this event is still in the future, set it as the end
        if (*event_time > end_time) {
            end_event_time = event_time;
        }

        // Cache pointer to this event as potential
        // Next event and go back one event
        // **NOTE** next_time can be invalid
        window.next_time = event_time--;
    }

    // Keep looping while event occurred after start
    // Of window and we haven't hit beginning of array
    while (*event_time > begin_time && event_time != events->times);

    // Deference event to use as previous
    window.prev_time = *event_time;
    window.prev_time_valid = event_time != events->times;

    // Calculate number of events
    window.num_events = (end_event_time - window.next_time);

    // Using num_events, find next and previous traces
    const post_trace_t *end_event_trace = events->traces + count;
    window.next_trace = (end_event_trace - window.num_events);
    window.prev_trace = *(window.next_trace - 1);

    // Return window
    return window;
}

//---------------------------------------
static inline post_event_window_t post_events_next(
        post_event_window_t window) {
    // Update previous time and increment next time
    window.prev_time = *window.next_time++;
    window.prev_trace = *window.next_trace++;

    // Time will now be valid for sure!
    window.prev_time_valid = 1;

    // Decrement remaining events
    window.num_events--;
    return window;
}

//---------------------------------------
static inline void post_events_add(
        uint32_t time, post_event_history_t *events, post_trace_t trace) {
    if (events->count_minus_one < MAX_POST_SYNAPTIC_EVENTS - 1) {
        // If there's still space, store time at current end
        // and increment count minus 1
        const uint32_t new_index = ++events->count_minus_one;
        events->times[new_index] = time;
        events->traces[new_index] = trace;
    } else {
        // Otherwise Shuffle down elements
        // **NOTE** 1st element is always an entry at time 0
        for (uint32_t e = 2; e < MAX_POST_SYNAPTIC_EVENTS; e++) {
            events->times[e - 1] = events->times[e];
            events->traces[e - 1] = events->traces[e];
        }

        // Stick new time at end
        events->times[MAX_POST_SYNAPTIC_EVENTS - 1] = time;
        events->traces[MAX_POST_SYNAPTIC_EVENTS - 1] = trace;
    }
}

static inline void print_delayed_window_events(
        post_event_history_t *post_event_history,
        uint32_t begin_time, uint32_t end_time, uint32_t delay_dendritic) {
    log_debug("     ##  printing post window  ##");
    post_event_window_t post_window = post_events_get_window_delayed(
            post_event_history, begin_time, end_time);

    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time =
                *post_window.next_time + delay_dendritic;
        log_debug("post spike: %u, time: %u, trace: %u",
                post_window.num_events, delayed_post_time,
                *post_window.next_trace);

        post_window = post_events_next(post_window);
    }
}

#endif  // _POST_EVENTS_H_
