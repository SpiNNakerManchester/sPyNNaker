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

#ifndef _IN_SPIKES_H_
#define _IN_SPIKES_H_

#include "neuron-typedefs.h"
#include <circular_buffer.h>

static circular_buffer buffer;

// initialize_spike_buffer
//
// This function initializes the input spike buffer.
// It configures:
//    buffer:     the buffer to hold the spikes (initialized with size spaces)
//    input:      index for next spike inserted into buffer
//    output:     index for next spike extracted from buffer
//    overflows:  a counter for the number of times the buffer overflows
//    underflows: a counter for the number of times the buffer underflows
//
// If underflows is ever non-zero, then there is a problem with this code.
static inline bool in_spikes_initialize_spike_buffer(uint32_t size) {
    buffer = circular_buffer_initialize(size);
    return buffer != 0;
}

static inline bool in_spikes_add_spike(spike_t spike) {
    return circular_buffer_add(buffer, spike);
}

static inline bool in_spikes_get_next_spike(spike_t* spike) {
    return circular_buffer_get_next(buffer, spike);
}

static inline bool in_spikes_is_next_spike_equal(spike_t spike) {
    return circular_buffer_advance_if_next_equals(buffer, spike);
}

static inline counter_t in_spikes_get_n_buffer_overflows(void) {
    return circular_buffer_get_n_buffer_overflows(buffer);
}

static inline counter_t in_spikes_get_n_buffer_underflows(void) {
    return 0;
}

static inline void in_spikes_print_buffer(void) {
    circular_buffer_print_buffer(buffer);
}

//---------------------------------------
// Synaptic rewiring functions
//---------------------------------------
static inline uint32_t in_spikes_input_index(void) {
    return circular_buffer_input(buffer);
}

static inline uint32_t in_spikes_output_index(void) {
    return circular_buffer_output(buffer);
}

static inline uint32_t in_spikes_real_size(void) {
    return circular_buffer_real_size(buffer);
}

static inline uint32_t in_spikes_value_at_index(uint32_t index) {
    return circular_buffer_value_at_index(buffer, index);
}

#endif // _IN_SPIKES_H_
