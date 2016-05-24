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

static inline counter_t in_spikes_get_n_buffer_overflows() {
    return circular_buffer_get_n_buffer_overflows(buffer);
}

static inline counter_t in_spikes_get_n_buffer_underflows() {
    return 0;
}

#endif // _IN_SPIKES_H_
