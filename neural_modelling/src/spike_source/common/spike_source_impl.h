
#ifndef SPIKE_SOURCE_IMPL
#define SPIKE_SOURCE_IMPL

#include "../../common/common-typedefs.h"
#include "../../common/common-impl.h"

// Externals
extern uint32_t num_spike_sources;
extern uint32_t key;

// Function declarations in spike-source-poisson.c
bool spike_source_data_filled (address_t base_address, uint32_t flags, uint32_t spike_history_recording_region_size, 
                               uint32_t neuron_potentials_recording_region_size, uint32_t neuron_gsyns_recording_region_size);
void spike_source_generate(uint32_t tick);

void spike_source_dma_callback(uint unused, uint tag);

#endif  // SPIKE_SOURCE_IMPL
