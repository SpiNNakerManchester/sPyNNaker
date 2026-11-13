/*
 * Copyright (c) 2015 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Implementation of non-inlined API in spike_processing.h
#include "spike_processing.h"
#include "population_table/population_table.h"
#include "synapse_row.h"
#include "synapses.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include <simulation.h>
#include <debug.h>
#include <common/in_spikes.h>
#include <recording.h>

#ifdef STDP_NO_SPIKE_UPDATES
#include "dma_common.h"
#include "plasticity/synapse_dynamics.h"

static stdp_update_commit_t scheduled_stdp_update;
static stdp_update_commit_t pending_stdp_write;
static bool stdp_write_pending;
static bool stdp_paused;
#endif

//! DMA buffer structure combines the row read from SDRAM with information
//! about the read.
typedef struct dma_buffer {
    //! Address in SDRAM to write back plastic region to
    synaptic_row_t sdram_writeback_address;

    //! \brief Key of originating spike
    //! \details used to allow row data to be re-used for multiple spikes
    spike_t originating_spike;

    //! Number of bytes transferred in the read
    uint32_t n_bytes_transferred;

    //! Spike colour
    uint32_t colour;

    //! Spike colour mask
    uint32_t colour_mask;

    //! Row data
    synaptic_row_t row;
} dma_buffer;

//! The number of DMA Buffers to use
#define N_DMA_BUFFERS 2

//! DMA tags
enum spike_processing_dma_tags {
    //! Tag of a DMA read of a full synaptic row
    DMA_TAG_READ_SYNAPTIC_ROW,
    //! Tag of a DMA write of the plastic region of a synaptic row
    DMA_TAG_WRITE_PLASTIC_REGION
};

//! The current timer tick value
extern uint32_t time;

//! True if the DMA "loop" is currently running
static volatile bool dma_busy;

//! The DTCM buffers for the synapse rows
static dma_buffer dma_buffers[N_DMA_BUFFERS];

//! The index of the next buffer to be filled by a DMA
static uint32_t next_buffer_to_fill;

//! The index of the buffer currently being filled by a DMA read
static uint32_t buffer_being_read;

//! Number of outstanding synaptogenic rewires
static volatile uint32_t rewires_to_do = 0;

//! \brief The number of rewires to do when the DMA completes.
//! \details When a DMA is first set up, only this or ::dma_n_spikes can be 1
//!     with the other being 0.
static uint32_t dma_n_rewires;

//! \brief The number of spikes to do when the DMA completes.
//! \details When a DMA is first set up, only this or ::dma_n_rewires can be 1
//!     with the other being 0.
static uint32_t dma_n_spikes;

//! the number of DMA completes (used in provenance generation)
static uint32_t dma_complete_count;

//! the number of spikes that were processed (used in provenance generation)
static uint32_t spike_processing_count;

//! The number of successful rewires
static uint32_t n_successful_rewires;

//! \brief How many packets were lost from the input buffer because of
//!     late arrival
static uint32_t count_input_buffer_packets_late;

//! tracker of how full the input buffer got.
static uint32_t biggest_fill_size_of_input_buffer;

//! \brief Whether if we should clear packets from the input buffer at the
//!     end of a timer tick.
static bool clear_input_buffers_of_late_packets;

//! the number of packets received this time step
static struct {
    uint32_t time;
    uint32_t packets_this_time_step;
} p_per_ts_struct;

//! the region to record the packets per timestep in
static uint32_t p_per_ts_region;

/* PRIVATE FUNCTIONS - static for inlining */

//! \brief Perform a DMA read of a synaptic row
//! \param[in] spike: The spike that triggered this read
//! \param[in] result: The result of the lookup
static inline void do_dma_read(
        spike_t spike, pop_table_lookup_result_t *result) {
    // Write the SDRAM address of the plastic region and the
    // Key of the originating spike to the beginning of DMA buffer
    dma_buffer *next_buffer = &dma_buffers[next_buffer_to_fill];
    next_buffer->sdram_writeback_address = result->row_address;
    next_buffer->originating_spike = spike;
    next_buffer->n_bytes_transferred = result->n_bytes_to_transfer;
    next_buffer->colour = result->colour;
    next_buffer->colour_mask = result->colour_mask;

    // Start a DMA transfer to fetch this synaptic row into current
    // buffer
    buffer_being_read = next_buffer_to_fill;
    while (!spin1_dma_transfer(
            DMA_TAG_READ_SYNAPTIC_ROW, result->row_address, next_buffer->row, DMA_READ,
            result->n_bytes_to_transfer)) {
        // Do Nothing
    }
    next_buffer_to_fill = (next_buffer_to_fill + 1) % N_DMA_BUFFERS;
}

//! \brief Check if there is anything to do. If not, DMA is not busy
//! \param[out] spike: The spike being processed
//! \param[out] result: The result of the pop table lookup
//! \param[in,out] n_rewire: Accumulator of number of rewires
//! \param[in,out] n_process_spike: Accumulator of number of processed spikes
//! \return True if there's something to do
static inline bool is_something_to_do(
        spike_t *spike, pop_table_lookup_result_t *result, uint32_t *n_rewire,
		uint32_t *n_process_spike) {
    // Disable interrupts here as dma_busy modification is a critical section
    uint cpsr = spin1_int_disable();

    // Check for synaptic rewiring
    while (rewires_to_do) {
        rewires_to_do--;
        spin1_mode_restore(cpsr);
        if (synaptogenesis_dynamics_rewire(time, spike, result)) {
            *n_rewire += 1;
            return true;
        }
        cpsr = spin1_int_disable();
    }

    // Is there another address in the population table?
    spin1_mode_restore(cpsr);
    if (population_table_get_next_address(spike, result)) {
        *n_process_spike += 1;
        return true;
    }
    cpsr = spin1_int_disable();

    // track for provenance
    uint32_t input_buffer_filled_size = in_spikes_size();
    if (biggest_fill_size_of_input_buffer < input_buffer_filled_size) {
        biggest_fill_size_of_input_buffer = input_buffer_filled_size;
    }

#ifdef STDP_NO_SPIKE_UPDATES
check_input_buffer:
#endif
    // Are there any more spikes to process?
    while (in_spikes_get_next_spike(spike)) {
        // Enable interrupts while looking up in the master pop table,
        // as this can be slow
        spin1_mode_restore(cpsr);
        if (population_table_get_first_address(*spike, result)) {
            synaptogenesis_spike_received(time, *spike);
            *n_process_spike += 1;
            return true;
        }

        // Disable interrupts before checking if there is another spike
        cpsr = spin1_int_disable();
    }

#ifdef STDP_NO_SPIKE_UPDATES
    // Allow packet reception while scanning the SDRAM registry. The DMA
    // loop is still busy, so the packet callback only queues new input.
    spin1_mode_restore(cpsr);
    scheduled_stdp_update = stdp_updates_next(time);
    if (scheduled_stdp_update.row != NULL) {
        const stdp_update_row_t *row = scheduled_stdp_update.row;
        *spike = 0;
        *result = (pop_table_lookup_result_t) {
            .row_address = (synaptic_row_t) row->address,
            .n_bytes_to_transfer = row->n_bytes
        };
        return true;
    }
    cpsr = spin1_int_disable();
    if (in_spikes_size() != 0) {
        goto check_input_buffer;
    }
#endif

    // If nothing to do, the DMA is not busy
    dma_busy = false;

    // Restore interrupts
    spin1_mode_restore(cpsr);
    return false;
}

//! \brief Set up a new synaptic DMA read.
//! \details
//! If a current_buffer is passed in, any spike found that matches the
//! originating spike of the buffer will increment a count, and the DMA of that
//! row will be skipped.  The number of times a row should be rewired and the
//! number of times synaptic processing should be done on a row is returned.
//!
//! Calls is_something_to_do(), do_direct_row() and do_dma_read()
//! \param[in] current_buffer: The current buffer, if any.
//! \param[in,out] n_rewires: Accumulator of number of rewires
//! \param[in,out] n_synapse_processes:
//!     Accumulator of number of synapses processed
//! \return Whether an actual DMA was set up or not
static bool setup_synaptic_dma_read(dma_buffer *current_buffer,
        uint32_t *n_rewires, uint32_t *n_synapse_processes) {
    // Set up to store the DMA location and size to read
    spike_t spike;
    pop_table_lookup_result_t result;
    dma_n_spikes = 0;
    dma_n_rewires = 0;
#ifdef STDP_NO_SPIKE_UPDATES
    scheduled_stdp_update = (stdp_update_commit_t) {0};
#endif

    // Keep looking if there is something to do until a DMA can be done
    bool setup_done = false;
    while (!setup_done && is_something_to_do(
            &spike, &result, &dma_n_rewires, &dma_n_spikes)) {
        if (current_buffer != NULL &&
                current_buffer->sdram_writeback_address == result.row_address) {
            // If we can reuse the row, add on what we can use it for
            // Note that only one of these will have a value of 1 with the
            // other being set to 0, but we add both as it is simple
            *n_rewires += dma_n_rewires;
            *n_synapse_processes += dma_n_spikes;
            dma_n_rewires = 0;
            dma_n_spikes = 0;
            // Although we can reuse the buffer, the colour might be different
            current_buffer->colour = result.colour;
        } else {
            // If the row is in SDRAM, set up the transfer and we are done
            do_dma_read(spike, &result);
            setup_done = true;
        }

        // needs to be here to ensure that its only recording actual spike
        // processing and not the surplus DMA requests.
#ifdef STDP_NO_SPIKE_UPDATES
        if (scheduled_stdp_update.row == NULL)
#endif
        {
            spike_processing_count++;
        }
    }
    return setup_done;
}

//! \brief Set up a DMA write of synaptic data.
//! \param[in] dma_buffer_index: Index of DMA buffer to use
//! \param[in] plastic_only: If false, write the whole synaptic row.
//!     If true, only write the plastic data region of the synaptic row.
static inline void setup_synaptic_dma_write(
        uint32_t dma_buffer_index, bool plastic_only) {
    // Get pointer to current buffer
    dma_buffer *buffer = &dma_buffers[dma_buffer_index];

    // Get the number of plastic bytes and the write back address from the
    // synaptic row
    size_t write_size = buffer->n_bytes_transferred;
    void *sdram_start_address = buffer->sdram_writeback_address;
    void *dtcm_start_address = buffer->row;
    if (plastic_only) {
        write_size = synapse_row_plastic_size(buffer->row) * sizeof(uint32_t);
        sdram_start_address = synapse_row_plastic_region(
                buffer->sdram_writeback_address);
        dtcm_start_address = synapse_row_plastic_region(buffer->row);
    }

    // Start transfer
    while (!spin1_dma_transfer(DMA_TAG_WRITE_PLASTIC_REGION, sdram_start_address,
            dtcm_start_address, DMA_WRITE, write_size)) {
        // Do Nothing
    }
}

//! \brief Start the DMA processing loop if not already running
static inline void start_dma_loop(void) {
#ifdef STDP_NO_SPIKE_UPDATES
    if (stdp_paused) {
        return;
    }
#endif
    // If we're not already processing synaptic DMAs,
    // flag pipeline as busy and trigger a feed event
    // NOTE: locking is not used here because this is assumed to be FIQ
    if (!dma_busy) {
        // Only set busy if successful.
        // NOTE: Counts when unsuccessful are handled by the API
        if (spin1_trigger_user_event(0, 0)) {
            dma_busy = true;
        }
    }
}

//! \brief Called when a multicast packet is received
//! \param[in] key: The key of the packet. The spike.
//! \param[in] unused: Only specified to match API
static void multicast_packet_received_callback(uint key, UNUSED uint unused) {
    p_per_ts_struct.packets_this_time_step += 1;
    if (in_spikes_add_spike(key)) {
        start_dma_loop();
    }
}

//! \brief Called when a multicast packet is received
//! \param[in] key: The key of the packet. The spike.
//! \param[in] payload: the payload of the packet. The count.
static void multicast_packet_pl_received_callback(uint key, uint payload) {
    p_per_ts_struct.packets_this_time_step += 1;

    // cycle through the packet insertion
    bool added = false;
    for (uint count = payload; count > 0; count--) {
        added = in_spikes_add_spike(key);
    }
    if (added) {
        start_dma_loop();
    }
}

static void report_row_error(dma_buffer *buffer) {
    log_error("Error processing spike 0x%.8x for address 0x%.8x (local=0x%.8x)",
            buffer->originating_spike, buffer->sdram_writeback_address,
            buffer->row);
    address_t row = (address_t) buffer->row;
    for (uint32_t i = 0; i < (buffer->n_bytes_transferred >> 2); i++) {
        log_error("%u: 0x%08x", i, row[i]);
    }
    rt_error(RTE_SWERR);
}

#ifdef STDP_NO_SPIKE_UPDATES
static void stdp_write_complete(UNUSED uint unused, UNUSED uint tag) {
    stdp_updates_commit(pending_stdp_write);
    stdp_write_pending = false;
    if (!stdp_paused) {
        setup_synaptic_dma_read(NULL, NULL, NULL);
    }
}

//! Process one read without prefetch. A read of this row after this point
//! must see both the new weights and the cursor of the same transaction.
static void process_stdp_dma_row(uint32_t buffer_index) {
    dma_buffer *buffer = &dma_buffers[buffer_index];
    stdp_update_commit_t update = scheduled_stdp_update;
    bool write_back = false;
    if (update.row != NULL) {
        uint32_t cursor = update.row->cursor;
        write_back = synapse_dynamics_update_without_spike(
                buffer->row, update.time, &cursor);
        update.time = cursor;
    } else if (dma_n_spikes != 0) {
        if (!synapses_process_synaptic_row_with_update(
                time, buffer->colour, buffer->colour_mask, buffer->row,
                buffer->sdram_writeback_address, buffer->n_bytes_transferred,
                &write_back, &update)) {
            report_row_error(buffer);
        }
    }

    if (write_back) {
        pending_stdp_write = update;
        stdp_write_pending = true;
        setup_synaptic_dma_write(buffer_index, true);
    } else if (!stdp_paused) {
        setup_synaptic_dma_read(NULL, NULL, NULL);
    }
}
#endif

//! \brief Called when a DMA completes
//! \param unused: unused
//! \param[in] tag: What sort of DMA has finished?
static void dma_complete_callback(UNUSED uint unused, UNUSED uint tag) {

    // increment the dma complete count for provenance generation
    dma_complete_count++;

    // Get pointer to current buffer
    uint32_t current_buffer_index = buffer_being_read;
#ifdef STDP_NO_SPIKE_UPDATES
    buffer_being_read = N_DMA_BUFFERS;
    process_stdp_dma_row(current_buffer_index);
#else
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
    for (uint32_t i = n_rewires; i > 0; i--) {
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
                time, current_buffer->colour, current_buffer->colour_mask,
				current_buffer->row, &write_back_now)) {
            report_row_error(current_buffer);
        }

        write_back |= write_back_now;
        n_spikes--;
    }

    if (write_back) {
        setup_synaptic_dma_write(current_buffer_index, plastic_only);
    }
#endif
}

//! \brief Called when a user event is received
//! \param unused0: unused
//! \param unused1: unused
void user_event_callback(UNUSED uint unused0, UNUSED uint unused1) {
#ifdef STDP_NO_SPIKE_UPDATES
    if (!stdp_paused) {
        setup_synaptic_dma_read(NULL, NULL, NULL);
    }
#else
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
#endif
}

/* INTERFACE FUNCTIONS - cannot be static */
void spike_processing_clear_input_buffer(timer_t time) {
    uint32_t n_spikes = in_spikes_size();
    if (clear_input_buffers_of_late_packets) {
#ifndef STDP_NO_SPIKE_UPDATES
        spin1_dma_flush();
        dma_busy = false;
#endif
        in_spikes_clear();
    }

    // Record the number of packets received last timer tick
    p_per_ts_struct.time = time;
    recording_record(p_per_ts_region, &p_per_ts_struct, sizeof(p_per_ts_struct));
    p_per_ts_struct.packets_this_time_step = 0;

    // Record the count whether clearing or not for provenance
    count_input_buffer_packets_late += n_spikes;
}

bool spike_processing_initialise( // EXPORTED
        size_t row_max_n_words, uint mc_packet_callback_priority,
        uint user_event_priority, uint incoming_spike_buffer_size,
        bool clear_input_buffers_of_late_packets_init,
        uint32_t packets_per_timestep_region) {
    // Allocate the DMA buffers
    for (uint32_t i = 0; i < N_DMA_BUFFERS; i++) {
        dma_buffers[i].row = spin1_malloc(row_max_n_words * sizeof(uint32_t));
        if (dma_buffers[i].row == NULL) {
            log_error("Could not initialise DMA buffers with %u words", row_max_n_words);
            return false;
        }
    }
    dma_busy = false;
    clear_input_buffers_of_late_packets =
        clear_input_buffers_of_late_packets_init;
    next_buffer_to_fill = 0;
    buffer_being_read = N_DMA_BUFFERS;
    p_per_ts_region = packets_per_timestep_region;

    // Allocate incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(incoming_spike_buffer_size)) {
        return false;
    }

    // Set up the callbacks
    spin1_callback_on(MC_PACKET_RECEIVED,
            multicast_packet_received_callback, mc_packet_callback_priority);
    spin1_callback_on(MCPL_PACKET_RECEIVED,
            multicast_packet_pl_received_callback, mc_packet_callback_priority);
    simulation_dma_transfer_done_callback_on(
            DMA_TAG_READ_SYNAPTIC_ROW, dma_complete_callback);
#ifdef STDP_NO_SPIKE_UPDATES
    simulation_dma_transfer_done_callback_on(
            DMA_TAG_WRITE_PLASTIC_REGION, stdp_write_complete);
#endif
    spin1_callback_on(USER_EVENT, user_event_callback, user_event_priority);

    return true;
}

void spike_processing_store_provenance(struct spike_processing_provenance *prov) {
    prov->n_input_buffer_overflows = in_spikes_get_n_buffer_overflows();
    prov->n_dmas_complete = dma_complete_count;
    prov->n_spikes_processed = spike_processing_count;
    prov->n_rewires = n_successful_rewires;
    prov->n_packets_dropped_from_lateness = count_input_buffer_packets_late;
    prov->max_filled_input_buffer_size = biggest_fill_size_of_input_buffer;
}

bool spike_processing_do_rewiring(int number_of_rewires) {
    // disable interrupts
    uint cpsr = spin1_int_disable();
    rewires_to_do += number_of_rewires;
    start_dma_loop();
    // enable interrupts
    spin1_mode_restore(cpsr);
    return true;
}

#ifdef STDP_NO_SPIKE_UPDATES
void spike_processing_do_stdp_updates(timer_t local_time) {
    uint32_t cpsr = spin1_int_disable();
    if (local_time == time) {
        stdp_paused = false;
        stdp_updates_begin_timestep(local_time);
        start_dma_loop();
    }
    spin1_mode_restore(cpsr);
}

void spike_processing_pause_stdp_updates(void) {
    uint32_t cpsr = spin1_int_disable();
    stdp_paused = true;
    if (buffer_being_read < N_DMA_BUFFERS &&
            scheduled_stdp_update.row == NULL) {
        // Finish an in-flight real spike before the host can read weights.
        // A pending background read is safe to cancel: it changed no state.
        wait_for_dma_to_complete();
        spin1_dma_flush();
        process_stdp_dma_row(buffer_being_read);
    }
    if (stdp_write_pending) {
        wait_for_dma_to_complete();
        stdp_updates_commit(pending_stdp_write);
        stdp_write_pending = false;
    }
    spin1_dma_flush();
    buffer_being_read = N_DMA_BUFFERS;
    dma_busy = false;
    spin1_mode_restore(cpsr);
}
#endif
