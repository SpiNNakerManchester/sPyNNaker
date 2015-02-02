#include "spike_processing.h"
#include "population_table.h"
#include "synapse_row.h"
#include "synapses.h"
#include "../common/in_spikes.h"
#include <spin1_api.h>
#include <debug.h>

// The number of DMA Buffers to use
#define N_DMA_BUFFERS 3

// The number of extra words to keep in a DMA buffer for local use
#define N_DMA_BUFFER_EXTRA_WORDS 2

// The number of spaces in the incoming spike buffer
#define N_INCOMING_SPIKES 256

// DMA tags
#define DMA_TAG_READ_SYNAPTIC_ROW 0
#define DMA_TAG_WRITE_PLASTIC_REGION 1

extern uint32_t time;

// True if the DMA "loop" is currently running
static bool dma_busy;

// True if a read would have taken place, but the position in the dma buffers
// is currently being written to SDRAM, so the read would clash
static bool write_blocked_next_read;

// The DTCM buffers for the synapse rows
static uint32_t* dma_buffers[N_DMA_BUFFERS];

// The index of the next buffer to be filled by a DMA
static uint32_t next_buffer_to_fill;

// The index of the buffer currently being filled by a DMA read
static uint32_t buffer_being_read;

// The index of the buffer currently being
static uint32_t buffer_being_written;


/* PRIVATE FUNCTIONS - static for inlining */

static inline void _setup_synaptic_dma_read() {

    // If the next buffer to be filled is currently being written,
    // we need to wait until the write completes
    if (next_buffer_to_fill == buffer_being_written) {
        write_blocked_next_read = true;
    } else {

        // If there's more incoming spikes
        spike_t spike;
        uint32_t setup_done = false;
        while (!setup_done && in_spikes_get_next_spike(&spike)) {
            log_debug("Checking for row for spike 0x%.8x\n", spike);

            // Decode spike to get address of destination synaptic row
            address_t row_address;
            size_t n_bytes_to_transfer;

            if (population_table_get_address(spike, &row_address,
                    &n_bytes_to_transfer)) {

                // Write the SDRAM address and originating spike to the
                // beginning of dma buffer
                dma_buffers[next_buffer_to_fill][0] = (uint32_t) row_address;
                dma_buffers[next_buffer_to_fill][1] = spike;

                // Start a DMA transfer to fetch this synaptic row into current
                // buffer
                buffer_being_read = next_buffer_to_fill;
                spin1_dma_transfer(DMA_TAG_READ_SYNAPTIC_ROW, row_address,
                                   &dma_buffers[next_buffer_to_fill][2],
                                   DMA_READ, n_bytes_to_transfer);
                next_buffer_to_fill = (next_buffer_to_fill + 1) % N_DMA_BUFFERS;

                setup_done = true;
            }
        }

        // If the setup was not done, and there are no more spikes,
        // stop trying to set up synaptic dmas
        if (!setup_done) {
            log_debug("DMA not busy");
            dma_busy = false;
        }
    }
}

static inline void _setup_synaptic_dma_write(uint32_t dma_buffer_index) {

    // Get the number of plastic bytes and the writeback address from the
    // synaptic row
    size_t n_plastic_region_bytes = synapse_row_plastic_size(
            dma_buffers[dma_buffer_index]) * sizeof(uint32_t);
    address_t writeback_address = synapse_row_plastic_write_back_address(
            dma_buffers[dma_buffer_index]);

    log_debug("Writing back %u bytes of plastic region to %08x",
              n_plastic_region_bytes, writeback_address);

    // Start transfer
    buffer_being_written = dma_buffer_index;
    spin1_dma_transfer(
        DMA_TAG_WRITE_PLASTIC_REGION, writeback_address,
        synapse_row_plastic_region(dma_buffers[dma_buffer_index]),
        DMA_WRITE, n_plastic_region_bytes);
}


/* CALLBACK FUNCTIONS - cannot be static */

// Called when a multicast packet is received
void _multicast_packet_received_callback(uint key, uint payload) {
    use(payload);

    log_debug("Received spike %x at %d, DMA Busy = %d", key, time, dma_busy);

    // If there was space to add spike to incoming spike queue
    if (in_spikes_add_spike(key)) {

        // If we're not already processing synaptic dmas,
        // flag pipeline as busy and trigger a feed event
        if (!dma_busy) {

            log_debug("Sending user event for new spike");
            if (spin1_trigger_user_event(0, 0)) {
                dma_busy = true;
            } else {
                log_debug("Could not trigger user event\n");
            }
        }
    } else {
        log_debug("Could not add spike");
    }
}

// Called when a user event is received
void _user_event_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    _setup_synaptic_dma_read();
}

// Called when a DMA completes
void _dma_complete_callback(uint unused, uint tag) {
    use(unused);

    log_debug("DMA transfer complete with tag %u", tag);

    // If this DMA is the result of a read
    if (tag == DMA_TAG_READ_SYNAPTIC_ROW) {

        // Start the next DMA transfer, so it is complete when we are finished
        _setup_synaptic_dma_read();

        // Extract originating spike from start of DMA buffer
        spike_t spike = synapse_row_originating_spike(
                dma_buffers[buffer_being_read]);

        // Process synaptic row repeatedly
        bool subsequent_spikes;
        do {
            // Are there any more incoming spikes from the same pre-synaptic
            // neuron?
            subsequent_spikes = in_spikes_is_next_spike_equal(spike);

            // Process synaptic row, writing it back if it's the last time
            // it's going to be processed
            synapses_process_synaptic_row(time, dma_buffers[buffer_being_read],
                                          !subsequent_spikes,
                                          buffer_being_read);

        } while (subsequent_spikes);
    } else if (tag == DMA_TAG_WRITE_PLASTIC_REGION) {

        // If this is a DMA write, reset the index
        buffer_being_written = -1;

        // If the write blocked a read, start reading again
        if (write_blocked_next_read) {
            write_blocked_next_read = false;
            _setup_synaptic_dma_read();
        }

    } else {

        // Otherwise, if it ISN'T the result of a plastic region write
        log_error("Invalid tag %d received in DMA", tag);
    }
}


/* INTERFACE FUNCTIONS - cannot be static */

bool spike_processing_initialise(size_t row_max_n_words) {

    // Allocate the DMA buffers
    for (uint32_t i = 0; i < N_DMA_BUFFERS; i++) {
        dma_buffers[i] = (uint32_t *) spin1_malloc(
                (row_max_n_words + N_DMA_BUFFER_EXTRA_WORDS)
                        * sizeof(uint32_t));
        if (dma_buffers[i] == NULL) {
            log_error("Could not initialise DMA buffers");
            return false;
        }
    }
    dma_busy = false;
    write_blocked_next_read = false;
    next_buffer_to_fill = 0;
    buffer_being_read = N_DMA_BUFFERS;
    buffer_being_written = N_DMA_BUFFERS;

    // Allocate incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(N_INCOMING_SPIKES)) {
        return false;
    }

    // Set up the callbacks
    spin1_callback_on(MC_PACKET_RECEIVED,
            _multicast_packet_received_callback, -1);
    spin1_callback_on(DMA_TRANSFER_DONE, _dma_complete_callback, 0);
    spin1_callback_on(USER_EVENT, _user_event_callback, 0);

    return true;
}

void spike_processing_finish_write(uint32_t process_id) {
    _setup_synaptic_dma_write(process_id);
}
