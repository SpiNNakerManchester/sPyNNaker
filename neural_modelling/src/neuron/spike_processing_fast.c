/*
 * Copyright (c) 2020 The University of Manchester
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

#include "spike_processing_fast.h"
#include "population_table/population_table.h"
#include "synapses.h"
#include <spin1_api_params.h>
#include <scamp_spin1_sync.h>
#include <simulation.h>
#include <recording.h>
#include <debug.h>
#include <wfi.h>

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

    //! Row data
    synaptic_row_t row;
} dma_buffer;

//! The number of DMA Buffers to use
#define N_DMA_BUFFERS 2

//! Mask to apply to perform modulo on the DMA buffer index
#define DMA_BUFFER_MOD_MASK 0x1

//! The extra overhead to add to the transfer time
#define TRANSFER_OVERHEAD_CLOCKS 100

//! The DTCM buffers for the synapse rows
static dma_buffer dma_buffers[N_DMA_BUFFERS];

//! DMA write flags
static const uint32_t DMA_WRITE_FLAGS =
        DMA_WIDTH << 24 | DMA_BURST_SIZE << 21 | DMA_WRITE << 19;

//! DMA read flags
static const uint32_t DMA_READ_FLAGS =
        DMA_WIDTH << 24 | DMA_BURST_SIZE << 21 | DMA_READ << 19;

//! The index of the next buffer to be filled by a DMA
static uint32_t next_buffer_to_fill;

//! The index of the buffer currently being filled by a DMA read
static uint32_t next_buffer_to_process;

//! \brief How many packets were lost from the input buffer because of
//!     late arrival
static uint32_t count_input_buffer_packets_late;

//! tracker of how full the input buffer got.
static uint32_t biggest_fill_size_of_input_buffer;

//! \brief Whether if we should clear packets from the input buffer at the
//!     end of a timer tick.
static bool clear_input_buffers_of_late_packets;

static uint32_t clocks_to_transfer = 0;

static uint32_t n_successful_rewires = 0;

static uint32_t dma_complete_count = 0;

static uint32_t spike_processing_count = 0;

static uint32_t max_spikes_received = 0;

static uint32_t spikes_processed_this_time_step = 0;

static uint32_t max_spikes_processed = 0;

//! the number of packets received this time step
static struct {
    uint32_t time;
    uint32_t packets_this_time_step;
} p_per_ts_struct;

//! the region to record the packets per timestep in
static uint32_t p_per_ts_region;

//! Where synaptic input is to be written
static struct sdram_config sdram_inputs;

// The ring buffers to use
static weight_t *ring_buffers;

static bool write_data_next = false;

//! \brief Determine if this is the end of the time step
//! \return True if end of time step
static inline bool is_end_of_time_step(void) {
    return tc[T2_COUNT] == 0;
}

//! \brief Clear end of time step
static inline void clear_end_of_time_step(void) {
    tc[T2_INT_CLR] = 1;
}

static inline void do_fast_dma_write(void *tcm_address, void *system_address,
        uint32_t n_bytes) {
    uint32_t desc = DMA_WRITE_FLAGS | n_bytes;
    dma[DMA_ADRS] = (uint32_t) system_address;
    dma[DMA_ADRT] = (uint32_t) tcm_address;
    dma[DMA_DESC] = desc;
}

//! \brief perform a DMA transfer from SDRAM to TCM
static inline void do_fast_dma_read(void *system_address, void *tcm_address,
        uint32_t n_bytes) {
    uint32_t desc = DMA_READ_FLAGS | n_bytes;
    dma[DMA_ADRS] = (uint32_t) system_address;
    dma[DMA_ADRT] = (uint32_t) tcm_address;
    dma[DMA_DESC] = desc;
}

static inline void wait_for_dma_to_complete(void) {
    // Wait for completion of DMA
    uint32_t n_loops = 0;
    while (!(dma[DMA_STAT] & (1 << 10)) && n_loops < 10000) {
        n_loops++;
    }
    if (!(dma[DMA_STAT] & (1 << 10))) {
        log_error("Timeout on DMA loop: DMA stat = 0x%08x!", dma[DMA_STAT]);
        rt_error(RTE_SWERR);
    }
    dma[DMA_CTRL] = 0x8;
}

static inline void cancel_dmas(void) {
    dma[DMA_CTRL] = 0x3;
    while (dma[DMA_STAT] & 0x1) {
        continue;
    }
    dma[DMA_CTRL] = 0xc;
}

static inline bool wait_for_dma_to_complete_or_end(void) {
    // Wait for completion of DMA
    uint32_t n_loops = 0;
    while (!is_end_of_time_step() && !(dma[DMA_STAT] & (1 << 10)) && n_loops < 10000) {
        n_loops++;
    }
    if (!is_end_of_time_step() && !(dma[DMA_STAT] & (1 << 10))) {
        log_error("Timeout on DMA loop: DMA stat = 0x%08x!", dma[DMA_STAT]);
        rt_error(RTE_SWERR);
    }
    dma[DMA_CTRL] = 0x8;

    bool end = is_end_of_time_step();
    if (end) {
        cancel_dmas();
        return false;
    }
    return true;
}

static inline void transfer_buffers(uint32_t time) {
    uint32_t first_ring_buffer = synapse_row_get_first_ring_buffer_index(
            time + 1, synapse_type_index_bits, synapse_delay_mask);
    log_debug("Writing %d bytes to 0x%08x from ring buffer %d at 0x%08x",
             sdram_inputs.size_in_bytes, sdram_inputs.address, first_ring_buffer,
             &ring_buffers[first_ring_buffer]);
    do_fast_dma_write(&ring_buffers[first_ring_buffer], sdram_inputs.address,
            sdram_inputs.size_in_bytes);
}

static inline void read_synaptic_row(spike_t spike, synaptic_row_t row,
        uint32_t n_bytes) {
    dma_buffer *buffer = &dma_buffers[next_buffer_to_fill];
    buffer->sdram_writeback_address = row;
    buffer->originating_spike = spike;
    buffer->n_bytes_transferred = n_bytes;
    do_fast_dma_read(row, buffer->row, n_bytes);
    next_buffer_to_fill = (next_buffer_to_fill + 1) & DMA_BUFFER_MOD_MASK;
}

static inline bool get_next_spike(spike_t *spike) {
    uint32_t n_spikes = in_spikes_size();
    if (biggest_fill_size_of_input_buffer < n_spikes) {
        biggest_fill_size_of_input_buffer = n_spikes;
    }
    return in_spikes_get_next_spike(spike);
}

static inline bool start_first_dma(spike_t *spike) {
    synaptic_row_t row;
    uint32_t n_bytes;

    do {
        if (population_table_get_first_address(*spike, &row, &n_bytes)) {
            read_synaptic_row(*spike, row, n_bytes);
            return true;
        }
    } while (!is_end_of_time_step() && get_next_spike(spike));

    return false;
}

static inline bool get_next_dma(spike_t *spike, synaptic_row_t *row,
        uint32_t *n_bytes) {
    if (population_table_is_next() && population_table_get_next_address(
            spike, row, n_bytes)) {
        return true;
    }

    while (!is_end_of_time_step() && get_next_spike(spike)) {
        if (population_table_get_first_address(*spike, row, n_bytes)) {
            return true;
        }
    }

    return false;
}


//! \brief Do processing related to the end of the time step
static inline void process_end_of_time_step(uint32_t time) {
    // Stop interrupt processing
    uint32_t cspr = spin1_int_disable();

    // Start transferring buffer data for next time step
    transfer_buffers(time);
    wait_for_dma_to_complete();

// TODO: Make this extra provenance
//    uint32_t end = tc[T1_COUNT];
//    if (end > clocks_to_transfer) {
//        log_info("Transfer took too long; clocks now %d", end);
//    }

    spin1_mode_restore(cspr);
}

static inline void handle_row_error(dma_buffer *buffer) {
    log_error(
        "Error processing spike 0x%.8x for address 0x%.8x (local=0x%.8x)",
        buffer->originating_spike, buffer->sdram_writeback_address, buffer->row);

    // Print out the row for debugging
    address_t row = (address_t) buffer->row;
    for (uint32_t i = 0; i < (buffer->n_bytes_transferred >> 2); i++) {
        log_error("    %u: 0x%08x", i, row[i]);
    }

    // Print out parsed data for static synapses
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(buffer->row);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(fixed_region);
    uint32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    log_error("\nFixed-Fixed Region (%u synapses):", fixed_synapse);
    for (; fixed_synapse > 0; fixed_synapse--) {
        uint32_t synaptic_word = *synaptic_words++;

        uint32_t delay = synapse_row_sparse_delay(
                synaptic_word, synapse_type_index_bits, synapse_delay_mask);
        uint32_t type = synapse_row_sparse_type(
                synaptic_word, synapse_index_bits, synapse_type_mask);
        uint32_t neuron = synapse_row_sparse_index(
                synaptic_word, synapse_index_mask);
        log_error("    Delay %u, Synapse Type %u, Neuron %u", delay, type, neuron);
    }
    rt_error(RTE_SWERR);
}

static inline void process_current_row(uint32_t time) {
    bool write_back = false;
    dma_buffer *buffer = &dma_buffers[next_buffer_to_process];

    if (!synapses_process_synaptic_row(time, buffer->row, &write_back)) {
        handle_row_error(buffer);
    }
    spike_processing_count++;
    if (write_back) {
        uint32_t n_bytes = synapse_row_plastic_size(buffer->row) * sizeof(uint32_t);
        void *system_address = synapse_row_plastic_region(
                buffer->sdram_writeback_address);
        void *tcm_address = synapse_row_plastic_region(buffer->row);
        wait_for_dma_to_complete();
        do_fast_dma_write(tcm_address, system_address, n_bytes);
    }
    next_buffer_to_process = (next_buffer_to_process + 1) & DMA_BUFFER_MOD_MASK;
    spikes_processed_this_time_step++;
}

static inline void store_data(uint32_t time) {
    // Record the number of packets still left
    count_input_buffer_packets_late += in_spikes_size();

    // Record the number of packets received last time step
    p_per_ts_struct.time = time;
    recording_record(p_per_ts_region, &p_per_ts_struct, sizeof(p_per_ts_struct));

    if (p_per_ts_struct.packets_this_time_step > max_spikes_received) {
        max_spikes_received = p_per_ts_struct.packets_this_time_step;
    }
    if (spikes_processed_this_time_step > max_spikes_processed) {
        max_spikes_processed = spikes_processed_this_time_step;
    }
}

static inline void measure_transfer_time(void) {
    // Measure the time to do an upload to know when to schedule the timer
    tc[T2_LOAD] = 0xFFFFFFFF;
    tc[T2_CONTROL] = 0x82;
    transfer_buffers(0);
    wait_for_dma_to_complete();
    clocks_to_transfer = (0xFFFFFFFF - tc[T2_COUNT]) + TRANSFER_OVERHEAD_CLOCKS;
    tc[T2_CONTROL] = 0;
    log_info("Transfer of %u bytes to 0x%08x took %u cycles",
            sdram_inputs.size_in_bytes, sdram_inputs.address, clocks_to_transfer);
}

void spike_processing_fast_time_step_loop(uint32_t time) {
    uint32_t cspr = spin1_int_disable();

    // We do this here rather than during init, as it should have similar
    // contention to the expected time of execution
    if (clocks_to_transfer == 0) {
        measure_transfer_time();
    }

    // Start timer2 to tell us when to stop
    uint32_t timer = tc[T1_COUNT];
    uint32_t time_until_stop = timer - clocks_to_transfer;
    tc[T2_CONTROL] = 0;
    tc[T2_LOAD] = time_until_stop;
    tc[T2_CONTROL] = 0xe3;

    log_debug("Start of time step %d, timer = %d, loading with %d",
            time, timer, time_until_stop);

    if (write_data_next) {

        // Store recording data from last time step
        store_data(time - 1);

        // Clear the buffer if needed
        if (clear_input_buffers_of_late_packets) {
            in_spikes_clear();
        }
    }
    p_per_ts_struct.packets_this_time_step = 0;
    spikes_processed_this_time_step = 0;
    write_data_next = true;

    synapses_flush_ring_buffers(time);
    spin1_mode_restore(cspr);

    // Loop until the end of a time step is reached
    while (true) {

        // Wait for a spike, or the timer to expire
        uint32_t spike;
        while (!is_end_of_time_step() && !get_next_spike(&spike)) {
            // TODO: Work out why T2 doesn't cause an interrupt
            // wait_for_interrupt();
        }

        // If the timer has gone off, that takes precedence
        if (is_end_of_time_step()) {
            clear_end_of_time_step();
            process_end_of_time_step(time);
            return;
        }

        // There must be a spike!  Start a DMA processing loop...
        bool dma_in_progress = start_first_dma(&spike);
        while (dma_in_progress && !is_end_of_time_step()) {

            // See if there is another DMA to do
            synaptic_row_t row;
            uint32_t n_bytes;
            dma_in_progress = get_next_dma(&spike, &row, &n_bytes);

            // Finish the current DMA before starting the next
            if (!wait_for_dma_to_complete_or_end()) {
                count_input_buffer_packets_late += 1;
                break;
            }
            dma_complete_count++;
            if (dma_in_progress) {
                read_synaptic_row(spike, row, n_bytes);
            }

            // Process the row we already have while the DMA progresses
            process_current_row(time);
        }

        cancel_dmas();
    }
}

void spike_processing_fast_pause(uint32_t time) {
    store_data(time - 1);
    write_data_next = false;
    log_info("Max packets received = %d", max_spikes_received);
    log_info("Max spikes processed = %d", max_spikes_processed);
}

//! \brief Called when a multicast packet is received
//! \param[in] key: The key of the packet. The spike.
//! \param payload: the payload of the packet. The count.
void multicast_packet_received_callback(uint key, UNUSED uint unused) {
    log_debug("Received spike %x", key);
    p_per_ts_struct.packets_this_time_step++;
    in_spikes_add_spike(key);
}

//! \brief Called when a multicast packet is received
//! \param[in] key: The key of the packet. The spike.
//! \param payload: the payload of the packet. The count.
void multicast_packet_pl_received_callback(uint key, uint payload) {
    log_debug("Received spike %x with payload %d", key, payload);
    p_per_ts_struct.packets_this_time_step++;

    // cycle through the packet insertion
    for (uint count = payload; count > 0; count--) {
        in_spikes_add_spike(key);
    }
}

bool spike_processing_fast_initialise(
        uint32_t row_max_n_words, uint32_t spike_buffer_size,
        bool discard_late_packets, uint32_t pkts_per_ts_rec_region,
        struct sdram_config sdram_inputs_param, weight_t *ring_buffers_param) {
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
    next_buffer_to_fill = 0;
    next_buffer_to_process = 0;

    // Allocate incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(spike_buffer_size)) {
        return false;
    }

    // Store parameters and data
    clear_input_buffers_of_late_packets = discard_late_packets;
    p_per_ts_region = pkts_per_ts_rec_region;
    sdram_inputs = sdram_inputs_param;
    ring_buffers = ring_buffers_param;

    // Configure for multicast reception
    spin1_callback_on(MC_PACKET_RECEIVED, multicast_packet_received_callback, -1);
    spin1_callback_on(MCPL_PACKET_RECEIVED, multicast_packet_pl_received_callback, -1);

    // Wipe the inputs using word writes
    for (uint32_t i = 0; i < (sdram_inputs.size_in_bytes >> 2); i++) {
        sdram_inputs.address[i] = 0;
    }

    return true;
}

void spike_processing_fast_store_provenance(struct synapse_provenance *prov) {
    prov->n_input_buffer_overflows = in_spikes_get_n_buffer_overflows();
    prov->n_dmas_complete = dma_complete_count;
    prov->n_spikes_processed = spike_processing_count;
    prov->n_rewires = n_successful_rewires;
    prov->n_packets_dropped_from_lateness = count_input_buffer_packets_late;
    prov->spike_processing_get_max_filled_input_buffer_size =
            biggest_fill_size_of_input_buffer;
}
