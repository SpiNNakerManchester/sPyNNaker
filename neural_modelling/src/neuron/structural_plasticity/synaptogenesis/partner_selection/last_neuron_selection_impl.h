#ifndef _LAST_NEURON_SELECTION_IMPL_H_
#define _LAST_NEURON_SELECTION_IMPL_H_

#include "partner.h"
#include <neuron/spike_processing.h>


// For last spike selection
#include <circular_buffer.h>

// Include debug header for log_info etc
#include <debug.h>

// value to be returned when there is no valid partner selection
#define INVALID_SELECTION ((spike_t) - 1)

typedef struct {
    // circular buffer indices
    uint32_t my_cb_input, my_cb_output, no_spike_in_interval, cb_total_size;
    // a local reference to the circular buffer
    circular_buffer cb;
} circular_buffer_info_t;


// struct for keeping track of Circular buffer indices
circular_buffer_info_t cb_info;

//! randomly (with uniform probability) select one of the last received spikes
static spike_t potential_presynaptic_partner(mars_kiss64_seed_t seed) {
    if (!received_any_spike() || cb_info.no_spike_in_interval == 0) {
        return INVALID_SELECTION;
    }
    uint32_t offset = ulrbits(mars_kiss64_seed(seed)) *
        cb_info.no_spike_in_interval;
    return circular_buffer_value_at_index(
        cb_info.cb,
        (cb_info.my_cb_output + offset) & cb_info.cb_total_size);
}

#endif // _LAST_NEURON_SELECTION_IMPL_H_