#ifndef _IN_SPIKES_H_
#define _IN_SPIKES_H_

#include "neuron-typedefs.h"

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
void in_spikes_initialize_spike_buffer(uint size);

bool in_spikes_add_spike(spike_t spike);

bool in_spikes_get_next_spike_if_equals(spike_t spike);

bool in_spikes_get_next_spike_if_equals(spike_t spike);

counter_t in_spikes_get_n_buffer_overflows();

counter_t in_spikes_get_n_buffer_underflows();

void in_spikes_print_buffer();

#endif // _IN_SPIKES_H_
