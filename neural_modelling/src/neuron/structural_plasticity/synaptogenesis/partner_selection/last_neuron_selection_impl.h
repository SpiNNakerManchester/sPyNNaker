#ifndef _LAST_NEURON_SELECTION_IMPL_H_
#define _LAST_NEURON_SELECTION_IMPL_H_

#include "partner.h"
#include <neuron/spike_processing.h>


// For last spike selection
#include <circular_buffer.h>

// Include debug header for log_info etc
#include <debug.h>

typedef struct {
    // circular buffer indices
    uint32_t my_cb_input, my_cb_output, no_spike_in_interval, cb_total_size;
    // a local reference to the circular buffer
    circular_buffer cb;
} circular_buffer_info_t;


// struct for keeping track of Circular buffer indices
circular_buffer_info_t cb_info;

//! randomly (with uniform probability) select one of the last received spikes
static inline bool potential_presynaptic_partner(
        rewiring_data_t *rewiring_data, uint32_t *population_id,
        uint32_t *sub_population_id, uint32_t *neuron_id, spike_t *spike) {
    if (!received_any_spike() || cb_info.no_spike_in_interval == 0) {
        return false;
    }
    uint32_t offset = ulrbits(mars_kiss64_seed(rewiring_data->local_seed)) *
        cb_info.no_spike_in_interval;
    *spike = circular_buffer_value_at_index(
        cb_info.cb, (cb_info.my_cb_output + offset) & cb_info.cb_total_size);
    return sp_structs_find_by_spike(rewiring_data, *spike, neuron_id,
            population_id, sub_population_id);
}

#endif // _LAST_NEURON_SELECTION_IMPL_H_
