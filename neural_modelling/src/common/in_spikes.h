#ifndef _IN_SPIKES_H_
#define _IN_SPIKES_H_

#include "neuron-typedefs.h"
#include <circular_buffer.h>

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
    return circular_buffer_initialize(size);
}

static inline bool in_spikes_add_spike(spike_t spike) {
    return circular_buffer_add(spike);
}

static inline bool in_spikes_get_next_spike(spike_t* spike) {
    return circular_buffer_get_next(spike);
}

static inline bool in_spikes_is_next_spike_equal(spike_t spike) {
    return circular_buffer_advance_if_next_equals(spike);
}

static inline counter_t in_spikes_get_n_buffer_overflows() {
    return circular_buffer_get_n_buffer_overflows();
}

static inline counter_t in_spikes_get_n_buffer_underflows() {
    return 0;
}

static inline void in_spikes_print_buffer() {
    circular_buffer_print_buffer();
}

#endif // _IN_SPIKES_H_
