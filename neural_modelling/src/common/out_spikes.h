#ifndef _OUT_SPIKES_H_
#define _OUT_SPIKES_H_

#include "neuron-typedefs.h"

#include <bit_field.h>

extern bit_field_t out_spikes;

void out_spikes_reset();

bool out_spikes_initialize(size_t max_spike_sources);

void out_spikes_record(uint32_t recording_flags);

bool out_spikes_is_empty();

bool out_spikes_is_nonempty();

bool out_spikes_is_spike(index_t neuron_index);

void out_spikes_print();

static inline void out_spikes_set_spike(index_t neuron_index) {
    bit_field_set(out_spikes, neuron_index);
}

#endif // _OUT_SPIKES_H_
