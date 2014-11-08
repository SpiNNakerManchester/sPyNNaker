/*
 * in_spikes.c
 *
 *
 *  SUMMARY
 *    Incoming spike handling for SpiNNaker neural modelling
 *
 *    The essential feature of the buffer used in this impementation is that it
 *    requires no critical-section interlocking --- PROVIDED THERE ARE ONLY TWO
 *    PROCESSES: a producer/consumer pair. If this is changed, then a more
 *    intricate implementation will probably be required, involving the use
 *    of enable/disable interrupts.
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *
 *
 *  CREATION DATE
 *    10 December, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 10 December 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "in_spikes.h"

#include <debug.h>

static spike_t* buffer;
static uint buffer_size;

static index_t output;
static index_t input;
static counter_t overflows;
static counter_t underflows;

// unallocated
//
// Returns the number of buffer slots currently unallocated
static inline counter_t unallocated() {
    return ((input - output) % buffer_size);
}

// allocated
//
// Returns the number of buffer slots currently allocated
static inline counter_t allocated() {
    return ((output - input - 1) % buffer_size);
}

// The following two functions are used to determine whether a
// buffer can have an element extracted/inserted respectively.
static inline bool non_empty() {
    return (allocated() > 0);
}

static inline bool non_full() {
    return (unallocated() > 0);
}

void in_spikes_initialize_spike_buffer(uint size) {
    buffer = (spike_t *) sark_alloc(1, size * sizeof(spike_t));
    buffer_size = size;
    input = size - 1;
    output = 0;
    overflows = 0;
    underflows = 0;
}

uint32_t in_spikes_n_spikes_in_buffer() {
    return allocated();
}

#define peek_next(a) ((a - 1) % buffer_size)

#define next(a) do {(a) = peek_next(a);} while (false)

bool in_spikes_add_spike(spike_t spike) {
    bool success = non_full();

    if (success) {
        buffer[input] = spike;
        next(input);
    } else
        overflows++;

    return (success);
}

bool in_spikes_get_next_spike(spike_t* spike) {
    bool success = non_empty();

    if (success) {
        next(output);
        *spike = buffer[output];
    } else
        underflows++;

    return (success);
}

bool in_spikes_get_next_spike_if_equals(spike_t spike) {
    if (non_empty()) {
        uint peek_output = peek_next(output);
        if (buffer[peek_output] == spike) {
            output = peek_output;
            return true;
        }
    }
    return false;
}

// The following two functions are used to access the locally declared
// variables.
counter_t in_spikes_get_n_buffer_overflows() {
    return (overflows);
}

counter_t in_spikes_get_n_buffer_underflows() {
    return (underflows);
}

#if LOG_LEVEL >= LOG_DEBUG
void in_spikes_print_buffer() {
    counter_t n = allocated();
    index_t a;

    log_debug("buffer: input = %3u, output = %3u elements = %3u\n", input,
            output, n);
    printf("------------------------------------------------\n");

    for (; n > 0; n--) {
        a = (input + n) % buffer_size;
        log_debug("  %3u: %08x\n", a, buffer[a]);
    }

    log_debug("------------------------------------------------\n");
}
#else // DEBUG
void in_spikes_print_buffer() {
    skip();
}
#endif // DEBUG
