#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include "../common/neuron-typedefs.h"

bool spike_processing_initialise(
    size_t row_max_n_bytes, uint mc_packet_callback_priority,
    uint dma_trasnfer_callback_priority, uint user_event_priority,
    uint incoming_spike_buffer_size);

void spike_processing_finish_write(uint32_t process_id);

void spike_processing_print_buffer_overflows();

#endif // _SPIKE_PROCESSING_H_
