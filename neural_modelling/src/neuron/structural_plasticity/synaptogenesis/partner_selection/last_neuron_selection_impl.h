#ifndef _LAST_NEURON_SELECTION_IMPL_H_
#define _LAST_NEURON_SELECTION_IMPL_H_

#include "partner.h"
#include <neuron/spike_processing.h>

// Include debug header for log_info etc
#include <debug.h>

extern spike_t* last_spikes_buffer[2];
extern uint32_t n_spikes[2];
extern uint32_t last_spikes_buffer_size;
extern uint32_t last_time;

static inline void partner_spike_received(uint32_t time, spike_t spike) {
    uint32_t buffer = time & 0x1;
    if (time != last_time) {
        last_time = time;
        n_spikes[buffer] = 0;
    }
    if (n_spikes[buffer] < last_spikes_buffer_size) {
        last_spikes_buffer[buffer][n_spikes[buffer]++] = spike;
    }
}

//! randomly (with uniform probability) select one of the last received spikes
static inline bool potential_presynaptic_partner(
        uint32_t time, rewiring_data_t *rewiring_data, uint32_t *population_id,
        uint32_t *sub_population_id, uint32_t *neuron_id, spike_t *spike) {
    uint32_t buffer = (time - 1) & 0x1;
    if (!n_spikes[buffer]) {
        return false;
    }
    uint32_t offset = ulrbits(mars_kiss64_seed(rewiring_data->local_seed)) *
        n_spikes[buffer];
    *spike = last_spikes_buffer[buffer][offset];
    return sp_structs_find_by_spike(rewiring_data, *spike, neuron_id,
            population_id, sub_population_id);
}

#endif // _LAST_NEURON_SELECTION_IMPL_H_
