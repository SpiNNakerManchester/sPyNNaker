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

#ifndef _POST_EVENTS_RATE_PYRAMIDAL_H_
#define _POST_EVENTS_RATE_PYRAMIDAL_H_

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include <debug.h>

//---------------------------------------
// Structures
//---------------------------------------

typedef struct {

    REAL vb_diff;
    REAL va_diff;

} post_event_history_t;

//---------------------------------------
// Inline functions
//---------------------------------------

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
        post_event_history[n].vb_diff = 0.0k;
        post_event_history[n].va_diff = 0.0k;
    }

    return post_event_history;
}

static inline void post_events_update(
        post_event_history_t *post_event_history, REAL va_diff, REAL vb_diff) {

    post_event_history->vb_diff = vb_diff;
    post_event_history->va_diff = va_diff;

}


#endif  // _POST_EVENTS_RATE_PYRAMIDAL_H_
