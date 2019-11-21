/*
 * Copyright (c) 2013-2019 The University of Manchester
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

#ifndef _RATE_BUFFER_H_
#define _RATE_BUFFER_H_

#include <stdint.h>
#include <stdbool.h>

typedef struct rate_t {
    uint32_t key;
    uint32_t rate;
} rate_t;

typedef struct _rate_buffer {
    uint32_t buffer_size;
    uint32_t output;
    uint32_t input;
    uint32_t overflows;
    rate_t *buffer;
} _rate_buffer, *rate_buffer;

// Returns the index of the next position in the buffer from the given value
static inline uint32_t _rate_buffer_next(
        rate_buffer buffer,
	uint32_t current)
{
    return (current + 1) & buffer->buffer_size;
}

// Returns true if the buffer is not empty
static inline bool _rate_buffer_not_empty(
	rate_buffer buffer)
{
    return buffer->input != buffer->output;
}

// Returns true if the buffer is not full
static inline bool _rate_buffer_not_full(
	rate_buffer buffer)
{
    return _rate_buffer_next(buffer, buffer->input) != buffer->output;
}

//! \brief Creates a new FIFO rate buffer of at least the given size.  For
//!        efficiency, the buffer can be bigger than requested
//! \param[in] size The minimum number of elements in the buffer to be created
//! \return A struct representing the created buffer
rate_buffer rate_buffer_initialize(uint32_t size);

//! \brief Adds an item to an existing buffer
//! \param[in] buffer The buffer struct to add to
//! \param[in] item The item to add
//! \return True if the item was added, False if the buffer was full
static inline bool rate_buffer_add(
	rate_buffer buffer,
	rate_t item)
{
    bool success = _rate_buffer_not_full(buffer);

    if (success) {
	buffer->buffer[buffer->input] = item;
	buffer->input = _rate_buffer_next(buffer, buffer->input);
    } else {
	buffer->overflows++;
    }

    return success;
}

//! \brief Get the next item from an existing buffer
//! \param[in] buffer The buffer to get the next item from
//! \param[out] item  A pointer to receive the next item
//! \return True if an item was retrieved, False if the buffer was empty
static inline bool rate_buffer_get_next(
	rate_buffer buffer,
	rate_t *item)
{
    bool success = _rate_buffer_not_empty(buffer);

    if (success) {
	*item = buffer->buffer[buffer->output];
	buffer->output = _rate_buffer_next(buffer, buffer->output);
    }

    return success;
}

//! \brief Advances the buffer if the next item is equal to the given value
//! \param[in] buffer The buffer to advance
//! \param[in] The item to check
//! \return True if the buffer was advanced, False otherwise
static inline bool rate_buffer_advance_if_next_equals(
        rate_buffer buffer,
	uint32_t item)
{
    bool success = _rate_buffer_not_empty(buffer);
    if (success) {
	    success = (buffer->buffer[buffer->output].key == item);
	    if (success) {
	        buffer->output = _rate_buffer_next(buffer, buffer->output);
	    }
    }
    return success;
}

//! \brief Gets the size of the buffer
//! \param[in] buffer The buffer to get the size of
//! \return The number of elements currently in the buffer
static inline uint32_t rate_buffer_size(
	rate_buffer buffer)
{
    return buffer->input >= buffer->output
	    ? buffer->input - buffer->output
	    : (buffer->input + buffer->buffer_size + 1) - buffer->output;
}

//! \brief Gets the number of overflows that have occurred when adding to
//!        the buffer
//! \param[in] buffer The buffer to check for overflows
//! \return The number of times add was called and returned False
static inline uint32_t rate_buffer_get_n_buffer_overflows(
	rate_buffer buffer)
{
    return buffer->overflows;
}

//! \brief clears the rate buffer
//! \param[in] buffer The buffer to clear
static inline void rate_buffer_clear(
	rate_buffer buffer)
{
    buffer->input = 0;
    buffer->output = 0;
}

//! \brief Prints the contents of the buffer.
//! Do not use if the sark IO_BUF is being used for binary data.
//! \param[in] The buffer to print
void rate_buffer_print_buffer(rate_buffer buffer);

//---------------------------------------
// Synaptic rewiring support functions
//---------------------------------------
static inline uint32_t rate_buffer_input(
	rate_buffer buffer)
{
    return buffer->input;
}

static inline uint32_t rate_buffer_output(
	rate_buffer buffer)
{
    return buffer->output;
}

static inline uint32_t rate_buffer_real_size(
	rate_buffer buffer)
{
    return buffer->buffer_size;
}

static inline rate_t rate_buffer_value_at_index(
	rate_buffer buffer,
	uint32_t index)
{
    return buffer->buffer[index & buffer->buffer_size];
}

#endif // _RATE_BUFFER_H_