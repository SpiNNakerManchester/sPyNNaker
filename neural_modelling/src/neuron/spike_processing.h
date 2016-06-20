#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include "../common/neuron-typedefs.h"

bool spike_processing_initialise(
    size_t row_max_n_bytes, uint mc_packet_callback_priority,
    uint dma_trasnfer_callback_priority, uint user_event_priority,
    uint incoming_spike_buffer_size,
    address_t single_fixed_synapses_base_address,
    address_t *single_fixed_synapses_local_address);

void spike_processing_finish_write(uint32_t process_id);

void spike_processing_do_timestep_update(uint32_t time);

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t spike_processing_get_buffer_overflows();

#endif // _SPIKE_PROCESSING_H_
