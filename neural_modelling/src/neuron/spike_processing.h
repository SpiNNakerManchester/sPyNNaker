#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include "../common/neuron-typedefs.h"

bool spike_processing_initialise(
    size_t row_max_n_bytes, uint mc_packet_callback_priority,
    uint dma_trasnfer_callback_priority, uint user_event_priority);

void spike_processing_finish_write(uint32_t process_id);

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t spike_processing_get_buffer_overflows();

#endif // _SPIKE_PROCESSING_H_
