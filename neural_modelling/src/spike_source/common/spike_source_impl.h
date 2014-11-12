#ifndef _SPIKE_SOURCE_IMPL_H_
#define _SPIKE_SOURCE_IMPL_H_

#include "../../common/neuron-typedefs.h"
#include "../../common/out_spikes.h"

#include <spin1_api.h>

uint32_t spike_source_impl_get_application_id();

uint32_t spike_source_impl_get_spike_recording_region_id();

bool spike_source_impl_initialize(
        address_t data_address, uint32_t *spike_source_key,
        uint32_t *spike_source_n_sources);

void spike_source_impl_generate_spikes(uint32_t tick);

void spike_source_impl_dma_callback(uint unused, uint tag);

#endif  // _SPIKE_SOURCE_IMPL_H_
