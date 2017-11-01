#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include "../common/neuron-typedefs.h"
#include "../common/in_spikes.h"

bool spike_processing_initialise(
    size_t row_max_n_bytes, uint mc_packet_callback_priority,
    uint user_event_priority, uint incoming_spike_buffer_size);

void spike_processing_finish_write(uint32_t process_id);

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t spike_processing_get_buffer_overflows();


// DMA buffer structure combines the row read from SDRAM with
typedef struct dma_buffer {

    // Address in SDRAM to write back plastic region to
    address_t sdram_writeback_address;

    // Key of originating spike
    // (used to allow row data to be re-used for multiple spikes)
    spike_t originating_spike;

    uint32_t n_bytes_transferred;

    // Row data
    uint32_t *row;

} dma_buffer;

//spike_t get_last_spike();
//uint32_t get_buffer_real_size();
circular_buffer get_circular_buffer();

#endif // _SPIKE_PROCESSING_H_
