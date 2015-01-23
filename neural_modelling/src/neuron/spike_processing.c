#include "spike_processing.h"
#include "population_table.h"
#include <spin1_api.h>

// The number of DMA Buffers to use
#define N_DMA_BUFFERS 3

// The number of extra words to keep in a DMA buffer for local use
#define N_DMA_BUFFER_EXTRA_WORDS 2

static uint32_t dma_read_buffer_index;
static uint32_t dma_write_buffer_index;
static bool dma_busy;
static uint32_t* dma_buffers[N_DMA_BUFFERS];

// Called when a spike is received
void _multicast_packet_received_callback(uint32_t key, uint32_t payload) {

}

// Called when a DMA completes
void _dma_complete_callback(uint32_t unused, uint32_t tag) {

}

// Called when a user event is received
void _user_event_callback(uint32_t unused0, uint32_t unused1) {

}

void _setup_synaptic_dma_read() {

}

void _setup_synaptic_dma_write(uint32_t dma_buffer_index) {

}

bool spike_processing_initialise(uint32_t row_max_n_words) {

    // Allocate the DMA buffers
    for (uint32_t i = 0; i < N_DMA_BUFFERS; i++) {
        dma_buffers[i] = (uint32_t *) spin1_malloc(
            (row_max_n_words + N_DMA_BUFFER_EXTRA_WORDS) * sizeof(uint32_t));
    }
    dma_busy = FALSE;
    dma_read_buffer_index = 0;
    dma_write_buffer_index = 0;

    spin1_callback_on(MC_PACKET_RECEIVED,
            _multicast_packet_received_callback, -1);
    spin1_callback_on(DMA_TRANSFER_DONE,
            _dma_complete_callback, 0);
    spin1_callback_on(USER_EVENT,
            _user_event_callback, 0);
}

void spike_processing_finish_write(uint32_t process_id) {

}
