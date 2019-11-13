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
#include "rate_buffer.h"

static rate_buffer buffer;

// initialize_rate_buffer
//
// This function initializes the input rate buffer.
// It configures:
//    buffer:     the buffer to hold the rates (initialized with size spaces)
//    input:      index for next rate inserted into buffer
//    output:     index for next rate extracted from buffer
//    overflows:  a counter for the number of times the buffer overflows
//    underflows: a counter for the number of times the buffer underflows
//
// If underflows is ever non-zero, then there is a problem with this code.
static inline bool in_rates_initialize_rate_buffer(uint32_t size) {
    buffer = rate_buffer_initialize(size);
    return buffer != 0;
}

static inline bool in_rates_add_rate(rate_t rate) {

    return rate_buffer_add(buffer, rate);
}

static inline bool in_rates_get_next_rate(rate_t* rate) {
    return rate_buffer_get_next(buffer, rate);
}

static inline bool in_rates_is_next_rate_equal(uint32_t key) {
    return rate_buffer_advance_if_next_equals(buffer, key);
}

static inline counter_t in_rates_get_n_buffer_overflows(void) {
    return rate_buffer_get_n_buffer_overflows(buffer);
}

static inline counter_t in_rates_get_n_buffer_underflows(void) {
    return 0;
}

static inline void in_rates_print_buffer(void) {
    rate_buffer_print_buffer(buffer);
}

//---------------------------------------
// Synaptic rewiring functions
//---------------------------------------
static inline uint32_t in_rates_input_index(void) {
    return rate_buffer_input(buffer);
}

static inline uint32_t in_rates_output_index(void) {
    return rate_buffer_output(buffer);
}

static inline uint32_t in_rates_real_size(void) {
    return rate_buffer_real_size(buffer);
}

static inline rate_t in_rates_value_at_index(uint32_t index) {
    return rate_buffer_value_at_index(buffer, index);
}

#endif // _IN_SPIKES_H_
