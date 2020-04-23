/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "spike_processing.h"
#include "population_table/population_table.h"
#include "synapse_row.h"
#include "synapses.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include <simulation.h>
#include <debug.h>

//! DMA buffer structure combines the row read from SDRAM with information
//! about the read.
typedef struct dma_buffer {

    // Address in SDRAM to write back plastic region to
    address_t sdram_writeback_address;

    // Key of originating spike
    // (used to allow row data to be re-used for multiple spikes)
    spike_t originating_spike;

    // Number of bytes transferred in the read
    uint32_t n_bytes_transferred;

    // Row data
    address_t row;

} dma_buffer;

// The number of DMA Buffers to use
#define N_DMA_BUFFERS 2

// DMA tags
enum spike_processing_dma_tags {
    DMA_TAG_READ_SYNAPTIC_ROW,
    DMA_TAG_WRITE_PLASTIC_REGION
};

extern uint32_t time;

// True if the DMA "loop" is currently running
static volatile bool dma_busy;

// The DTCM buffers for the synapse rows
static dma_buffer dma_buffers[N_DMA_BUFFERS];

// The index of the next buffer to be filled by a DMA
static uint32_t next_buffer_to_fill;

// The index of the buffer currently being filled by a DMA read
static uint32_t buffer_being_read;

static uint32_t max_n_words;

static uint32_t single_fixed_synapse[4];

static volatile uint32_t rewires_to_do = 0;

// The number of rewires to do when the DMA completes.  When a DMA is first set
// up, only this or dma_n_spikes can be 1 with the other being 0.
static uint32_t dma_n_rewires;

// The number of spikes to do when the DMA completes.  When a DMA is first set
// up, only this or dma_n_rewires can be 1 with the other being 0.
static uint32_t dma_n_spikes;

// The number of successful rewires
static uint32_t n_successful_rewires = 0;


/* PRIVATE FUNCTIONS - static for inlining */

static inline void do_dma_read(
        address_t row_address, size_t n_bytes_to_transfer, spike_t spike) {
    // Write the SDRAM address of the plastic region and the
    // Key of the originating spike to the beginning of DMA buffer
    dma_buffer *next_buffer = &dma_buffers[next_buffer_to_fill];
    next_buffer->sdram_writeback_address = row_address;
    next_buffer->originating_spike = spike;
    next_buffer->n_bytes_transferred = n_bytes_to_transfer;

    // Start a DMA transfer to fetch this synaptic row into current
    // buffer
    buffer_being_read = next_buffer_to_fill;
    while (!spin1_dma_transfer(
            DMA_TAG_READ_SYNAPTIC_ROW, row_address, next_buffer->row, DMA_READ,
            n_bytes_to_transfer)) {
        // Do Nothing
    }
    next_buffer_to_fill = (next_buffer_to_fill + 1) % N_DMA_BUFFERS;
}


static inline void do_direct_row(address_t row_address) {
    single_fixed_synapse[3] = (uint32_t) row_address[0];
    // Write back should be False by definition as single rows don't have STDP
    bool write_back;
    synapses_process_synaptic_row(time, single_fixed_synapse, &write_back);
}

// Check if there is anything to do - if not, DMA is not busy
static inline bool is_something_to_do(
        address_t *row_address, size_t *n_bytes_to_transfer,
        spike_t *spike, uint32_t *n_rewire, uint32_t *n_process_spike) {
    // Disable interrupts here as dma_busy modification is a critical section
    uint cpsr = spin1_int_disable();

    // Check for synaptic rewiring
    while (rewires_to_do) {
        rewires_to_do--;
        spin1_mode_restore(cpsr);
        if (synaptogenesis_dynamics_rewire(time, spike, row_address,
                n_bytes_to_transfer)) {
            *n_rewire += 1;
            return true;
        }
        cpsr = spin1_int_disable();
    }

    // Is there another address in the population table?
    spin1_mode_restore(cpsr);
    if (population_table_get_next_address(
            spike, row_address, n_bytes_to_transfer)) {
        *n_process_spike += 1;
        return true;
    }
    cpsr = spin1_int_disable();
    // Are there any more spikes to process?
    while (in_spikes_get_next_spike(spike)) {
        // Enable interrupts while looking up in the master pop table,
        // as this can be slow
        spin1_mode_restore(cpsr);
        if (population_table_get_first_address(
                *spike, row_address, n_bytes_to_transfer)) {
            synaptogenesis_spike_received(time, *spike);
            *n_process_spike += 1;
            return true;
        }

        // Disable interrupts before checking if there is another spike
        cpsr = spin1_int_disable();
    }

    // If nothing to do, the DMA is not busy
    dma_busy = false;

    // Restore interrupts
    spin1_mode_restore(cpsr);
    return false;
}

// Set up a new synaptic DMA read.  If a current_buffer is passed in, any spike
// found that matches the originating spike of the buffer will increment a
// count, and the DMA of that row will be skipped.  The number of times a row
// should be rewired and the number of times synaptic processing should be
// done on a row is returned.
static void setup_synaptic_dma_read(dma_buffer *current_buffer,
        uint32_t *n_rewires, uint32_t *n_synapse_processes) {

    // Set up to store the DMA location and size to read
    address_t row_address;
    size_t n_bytes_to_transfer;
    spike_t spike;
    dma_n_spikes = 0;
    dma_n_rewires = 0;

    // Keep looking if there is something to do until a DMA can be done
    bool setup_done = false;
    while (!setup_done && is_something_to_do(&row_address,
            &n_bytes_to_transfer, &spike, &dma_n_rewires, &dma_n_spikes)) {
        if (current_buffer != NULL &&
                current_buffer->sdram_writeback_address == row_address) {
            // If we can reuse the row, add on what we can use it for
            // Note that only one of these will have a value of 1 with the
            // other being set to 0, but we add both as it is simple
            *n_rewires += dma_n_rewires;
            *n_synapse_processes += dma_n_spikes;
            dma_n_rewires = 0;
            dma_n_spikes = 0;
        } else if (n_bytes_to_transfer == 0) {
            // If the row is in DTCM, process the row now
            do_direct_row(row_address);
            dma_n_rewires = 0;
            dma_n_spikes = 0;
        } else {
            // If the row is in SDRAM, set up the transfer and we are done
            do_dma_read(row_address, n_bytes_to_transfer, spike);
            setup_done = true;
        }
    }
}

static inline void setup_synaptic_dma_write(
        uint32_t dma_buffer_index, bool plastic_only) {

    // Get pointer to current buffer
    dma_buffer *buffer = &dma_buffers[dma_buffer_index];

    // Get the number of plastic bytes and the write back address from the
    // synaptic row
    size_t write_size = buffer->n_bytes_transferred;
    address_t sdram_start_address = buffer->sdram_writeback_address;
    address_t dtcm_start_address = buffer->row;
    if (plastic_only) {
        write_size = synapse_row_plastic_size(buffer->row) * sizeof(uint32_t);
        sdram_start_address = synapse_row_plastic_region(sdram_start_address);
        dtcm_start_address = synapse_row_plastic_region(dtcm_start_address);
    }

    log_debug("Writing back %u bytes of plastic region to %08x for spike %u",
              write_size, sdram_start_address, buffer->originating_spike);

    // Start transfer
    while (!spin1_dma_transfer(DMA_TAG_WRITE_PLASTIC_REGION, sdram_start_address,
            dtcm_start_address, DMA_WRITE, write_size)) {
        // Do Nothing
    }
}

// Called when a multicast packet is received
static void multicast_packet_received_callback(uint key, uint payload) {
    use(payload);
    log_debug("Received spike %x at %d, DMA Busy = %d", key, time, dma_busy);

    // If there was space to add spike to incoming spike queue
    if (in_spikes_add_spike(key)) {
        // If we're not already processing synaptic DMAs,
        // flag pipeline as busy and trigger a feed event
        // NOTE: locking is not used here because this is assumed to be FIQ
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

// Called when a DMA completes
static void dma_complete_callback(uint unused, uint tag) {
    use(unused);

    log_debug("DMA transfer complete at time %u with tag %u", time, tag);

    // Get pointer to current buffer
    uint32_t current_buffer_index = buffer_being_read;
    dma_buffer *current_buffer = &dma_buffers[current_buffer_index];

    // Start the next DMA transfer and get a count of the rewires and spikes
    // that can be done on this row now (there might be more while the DMA
    // was in progress).  Note that either dma_n_rewires or dma_n_spikes is set
    // to 1 here, with the other being 0.  We take a copy of the count and this
    // is the value added to for this processing, as setup_synaptic_dma will
    // count repeats of the current spike
    uint32_t n_rewires = dma_n_rewires;
    uint32_t n_spikes = dma_n_spikes;
    setup_synaptic_dma_read(current_buffer, &n_rewires, &n_spikes);

    // Assume no write back but assume any write back is plastic only
    bool write_back = false;
    bool plastic_only = true;

    // If rewiring, do rewiring first
    for (uint32_t i = 0; i < n_rewires; i++) {
        if (synaptogenesis_row_restructure(time, current_buffer->row)) {
            write_back = true;
            plastic_only = false;
            n_successful_rewires++;
        }
    }

    // Process synaptic row repeatedly for any upcoming spikes
    while (n_spikes > 0) {

        // Process synaptic row, writing it back if it's the last time
        // it's going to be processed
        bool write_back_now = false;
        if (!synapses_process_synaptic_row(
                time, current_buffer->row, &write_back_now)) {
            log_error(
                    "Error processing spike 0x%.8x for address 0x%.8x"
                    " (local=0x%.8x)",
                    current_buffer->originating_spike,
                    current_buffer->sdram_writeback_address,
                    current_buffer->row);

            // Print out the row for debugging
            for (uint32_t i = 0;
                    i < (current_buffer->n_bytes_transferred >> 2); i++) {
                log_error("%u: 0x%.8x", i, current_buffer->row[i]);
            }
            rt_error(RTE_SWERR);
        }

        write_back |= write_back_now;
        n_spikes--;
    }

    if (write_back) {
        setup_synaptic_dma_write(current_buffer_index, plastic_only);
    }
}

// Called when a user event is received
void user_event_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);

    // Reset the counters as this is a new process
    dma_n_rewires = 0;
    dma_n_spikes = 0;

    if (buffer_being_read < N_DMA_BUFFERS) {
        // If the DMA buffer is full of valid data, attempt to reuse it on the
        // next data to be used, as this might be able to make use of the buffer
        // without transferring data
        dma_complete_callback(0, DMA_TAG_READ_SYNAPTIC_ROW);
    } else {
        // If the DMA buffer is invalid, just do the first transfer possible
        setup_synaptic_dma_read(NULL, NULL, NULL);
    }
}

/* INTERFACE FUNCTIONS - cannot be static */

bool spike_processing_initialise( // EXPORTED
        size_t row_max_n_words, uint mc_packet_callback_priority,
        uint user_event_priority, uint incoming_spike_buffer_size) {
    // Allocate the DMA buffers
    for (uint32_t i = 0; i < N_DMA_BUFFERS; i++) {
        dma_buffers[i].row = spin1_malloc(row_max_n_words * sizeof(uint32_t));
        if (dma_buffers[i].row == NULL) {
            log_error("Could not initialise DMA buffers");
            return false;
        }
        log_debug("DMA buffer %u allocated at 0x%08x",
                i, dma_buffers[i].row);
    }
    dma_busy = false;
    next_buffer_to_fill = 0;
    buffer_being_read = N_DMA_BUFFERS;
    max_n_words = row_max_n_words;

    // Allocate incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(incoming_spike_buffer_size)) {
        return false;
    }

    // Set up for single fixed synapses (data that is consistent per direct row)
    single_fixed_synapse[0] = 0;
    single_fixed_synapse[1] = 1;
    single_fixed_synapse[2] = 0;

    // Set up the callbacks
    spin1_callback_on(MC_PACKET_RECEIVED,
            multicast_packet_received_callback, mc_packet_callback_priority);
    simulation_dma_transfer_done_callback_on(
            DMA_TAG_READ_SYNAPTIC_ROW, dma_complete_callback);
    spin1_callback_on(USER_EVENT, user_event_callback, user_event_priority);

    return true;
}

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overloaded
uint32_t spike_processing_get_buffer_overflows(void) { // EXPORTED
    // Check for buffer overflow
    return in_spikes_get_n_buffer_overflows();
}

//! \brief get the address of the circular buffer used for buffering received
//! spikes before processing them
//! \return address of circular buffer
circular_buffer get_circular_buffer(void) { // EXPORTED
    return buffer;
}

//! \brief returns the number of successful rewires performed
//! \return the number of successful rewires
uint32_t spike_processing_get_successful_rewires(void) { // EXPORTED
    return n_successful_rewires;
}

//! \brief set the number of times spike_processing has to attempt rewiring
//! \return bool: currently, always true
bool spike_processing_do_rewiring(int number_of_rewires) {

    // disable interrupts
    uint cpsr = spin1_int_disable();
    rewires_to_do += number_of_rewires;

    // If we're not already processing synaptic DMAs,
    // flag pipeline as busy and trigger a feed event
    if (!dma_busy) {
        log_debug("Sending user event for rewiring");
        if (spin1_trigger_user_event(0, 0)) {
            dma_busy = true;
        } else {
            log_debug("Could not trigger user event\n");
        }
    }
    // enable interrupts
    spin1_mode_restore(cpsr);
    return true;
}
