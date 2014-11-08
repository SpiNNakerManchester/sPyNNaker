#ifndef _RECORDING_H_
#define _RECORDING_H_

#include "neuron-typedefs.h"

typedef enum recording_channel_e {
    e_recording_channel_spike_history,
    e_recording_channel_neuron_potential,
    e_recording_channel_neuron_gsyn,
    e_recording_channel_max,
} recording_channel_e;

bool recording_initialze_channel(
        address_t output_region, recording_channel_e channel,
        uint32_t size_bytes);

bool recording_record(
        recording_channel_e channel, void *data, uint32_t size_bytes);

void recording_finalise();

#endif // _RECORDING_H_
