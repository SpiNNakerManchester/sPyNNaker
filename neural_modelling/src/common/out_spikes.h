#ifndef _OUT_SPIKES_H_
#define _OUT_SPIKES_H_

#include "neuron-typedefs.h"

void out_spikes_reset();

void out_spikes_initialize(size_t max_spike_sources);

void out_spikes_record();

bool out_spikes_is_empty();

bool out_spikes_is_nonempty();

bool out_spikes_is_spike(index_t neuron_index);

void out_spikes_print();

#endif // _OUT_SPIKES_H_
