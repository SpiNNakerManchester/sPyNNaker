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
//! \brief Functions for immediate handling of incoming spikes.

#ifndef _IN_SPIKES_H_
#define _IN_SPIKES_H_

#include "neuron-typedefs.h"
#include <circular_buffer.h>

//! \brief Buffer for quickly taking spikes received by a fast interrupt and
//! queueing them for later processing by less critical code.
static circular_buffer buffer;

//! \brief This function initialises the input spike buffer.
//!
//! It configures:
//! <dl>
//!    <dt>::buffer</dt>
//!    <dd>the buffer to hold the spikes (initialised with size spaces)</dd>
//!    <dt>input</dt>
//!    <dd>index for next spike inserted into buffer</dd>
//!    <dt>output</dt>
//!    <dd>index for next spike extracted from buffer</dd>
//!    <dt>overflows</dt>
//!    <dd>a counter for the number of times the buffer overflows</dd>
//!    <dt>underflows</dt>
//!    <dd>a counter for the number of times the buffer underflows</dd>
//! </dl>
//! If underflows is ever non-zero, then there is a problem with this code.
//!
//! \param[in] size: The number of spikes we expect to handle in the buffer;
//!     this should be a power of 2 (and will be increased to the next one up
//!     if it isn't).
//! \return True if the buffer was successfully initialised
static inline bool in_spikes_initialize_spike_buffer(uint32_t size) {
    buffer = circular_buffer_initialize(size);
    return buffer != 0;
}

//! \brief Adds a spike to the input spike buffer.
//! \param[in] spike: The spike to add
//! \return True if the spike was added
static inline bool in_spikes_add_spike(spike_t spike) {
    return circular_buffer_add(buffer, spike);
}

//! \brief Retrieves a spike from the input spike buffer.
//! \param[out] spike: The spike that was retrieved.
//! \return True if a spike was retrieved, false if the buffer was empty.
static inline bool in_spikes_get_next_spike(spike_t* spike) {
    return circular_buffer_get_next(buffer, spike);
}

//! \brief Skips the next spike in the buffer if it is equal to an existing
//!     spike.
//! \param[in] spike: The spike to compare against.
//! \return True if a spike was skipped over, false otherwise.
static inline bool in_spikes_is_next_spike_equal(spike_t spike) {
    return circular_buffer_advance_if_next_equals(buffer, spike);
}

//! \brief Get the number of times that the input spike buffer overflowed.
//! \return A count.
static inline counter_t in_spikes_get_n_buffer_overflows(void) {
    return circular_buffer_get_n_buffer_overflows(buffer);
}

//! \brief Get the number of times that the input spike buffer underflowed.
//! \return A count.
static inline counter_t in_spikes_get_n_buffer_underflows(void) {
    return 0;
}

//! \brief Print the input spike buffer.
//! \details Expected to be mainly for debugging.
static inline void in_spikes_print_buffer(void) {
    circular_buffer_print_buffer(buffer);
}

//---------------------------------------
// Synaptic rewiring functions
//---------------------------------------
//! \brief Get the index in the buffer of the point where the next insertion
//!     goes.
//! \return An index.
static inline uint32_t in_spikes_input_index(void) {
    return circular_buffer_input(buffer);
}

//! \brief Get the index in the buffer of the point where the next removal
//!     comes from.
//! \return An index.
static inline uint32_t in_spikes_output_index(void) {
    return circular_buffer_output(buffer);
}

//! \brief Get the size of the input spike buffer.
//! \return The size of the buffer (a power of 2).
static inline uint32_t in_spikes_real_size(void) {
    return circular_buffer_real_size(buffer);
}

//! \brief get the size of the input spike buffer
//! \return The size of the buffer.
static inline uint32_t in_spikes_size(void) {
    return circular_buffer_size(buffer);
}

//! \brief clears the input spike buffer.
static inline void in_spikes_clear(void) {
    circular_buffer_clear(buffer);
}

//! \brief Get the spike at a specific index of the input spike buffer.
//! \param[in] index: The index to retrieve from. Will be _wrapped_ within the
//!     buffer.
//! \return The spike at the index. **WARNING:** _if there is no spike at that
//!     index, the value returned may be arbitrary._
static inline spike_t in_spikes_value_at_index(uint32_t index) {
    return circular_buffer_value_at_index(buffer, index);
}
#endif // _IN_SPIKES_H_
