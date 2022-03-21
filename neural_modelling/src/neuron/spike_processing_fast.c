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
#include "plasticity/synapse_dynamics.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include "dma_common.h"
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

//! The DTCM buffers for the synapse rows
static dma_buffer dma_buffers[N_DMA_BUFFERS];

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

//! The number of CPU cycles taken to transfer spikes (measured later)
static uint32_t clocks_to_transfer = 0;

//! The number of successful rewiring attempts
static uint32_t n_successful_rewires = 0;

//! The number of DMAs successfully completed
static uint32_t dma_complete_count = 0;

//! The number of spikes successfully processed
static uint32_t spike_processing_count = 0;

//! The maximum number of spikes received in a time step
static uint32_t max_spikes_received = 0;

//! The number of spikes processed this time step
static uint32_t spikes_processed_this_time_step = 0;

//! The maximum number of spikes processed in a time step
static uint32_t max_spikes_processed = 0;

//! The number of times the transfer ran to the next time step
static uint32_t transfer_timer_overruns = 0;

//! The maximum overrun of the timer tick
static uint32_t max_transfer_timer_overrun = 0;

//! The number of times the timer tick was skipped entirely
static uint32_t skipped_time_steps = 0;

//! The latest time a spike was received on the clock (which counts down)
static uint32_t latest_spike_received_time = 0xFFFFFFFF;

//! The earliest time a spike was received on the clock (which counts down)
static uint32_t earliest_spike_received_time = 0;

//! The maximum number of spikes left at the end of a time step
static uint32_t max_spikes_overflow = 0;

//! The number of packets received this time step for recording
static struct {
    uint32_t time;
    uint32_t packets_this_time_step;
} p_per_ts_struct;

//! the region to record the packets per time step in
static uint32_t p_per_ts_region;

//! Where synaptic input is to be written
static struct sdram_config sdram_inputs;

//! Key configuration to detect local neuron spikes
static struct key_config key_config;

//! The ring buffers to use
static weight_t *ring_buffers;

//! \brief Determine if this is the end of the time step
//! \return True if end of time step
static inline bool is_end_of_time_step(void) {
    return tc[T2_COUNT] == 0;
}

//! \brief Clear end of time step so it can be detected again
static inline void clear_end_of_time_step(void) {
    tc[T2_INT_CLR] = 1;
}

//! \brief Wait for a DMA to complete or the end of a time step, whichever
//!        happens first.
//! \return True if the DMA is completed first, False if the time step ended first
static inline bool wait_for_dma_to_complete_or_end(void) {
#if LOG_LEVEL >= LOG_DEBUG
    // Useful for checking when things are going wrong, but shouldn't be
    // needed in normal code
    uint32_t n_loops = 0;
    while (!is_end_of_time_step() && !dma_done() && n_loops < 10000) {
        n_loops++;
    }
    if (!is_end_of_time_step() && !dma_done()) {
        log_error("Timeout on DMA loop: DMA stat = 0x%08x!", dma[DMA_STAT]);
        rt_error(RTE_SWERR);
    }
#else
    // This is the normal loop, done without checking
    while (!dma_done()) {
        continue;
    }
#endif
    dma[DMA_CTRL] = 0x8;

    return !is_end_of_time_step();
}

//! \brief Transfer the front of the ring buffers to SDRAM to be read by the
//!        neuron core at the next time step.
//! \param[in] time The current time step being executed.
static inline void transfer_buffers(uint32_t time) {
    uint32_t first_ring_buffer = synapse_row_get_first_ring_buffer_index(
            time + 1, synapse_type_index_bits, synapse_delay_mask);
    log_debug("Writing %d bytes to 0x%08x from ring buffer %d at 0x%08x",
             sdram_inputs.size_in_bytes, sdram_inputs.address, first_ring_buffer,
             &ring_buffers[first_ring_buffer]);
    do_fast_dma_write(&ring_buffers[first_ring_buffer], sdram_inputs.address,
            sdram_inputs.size_in_bytes);
}

//! \brief Do processing related to the end of the time step
//! \param[in] time The time step that is ending.
static inline void process_end_of_time_step(uint32_t time) {
    // Stop interrupt processing
    uint32_t cspr = spin1_int_disable();

    cancel_dmas();

    // Start transferring buffer data for next time step
    transfer_buffers(time);
    wait_for_dma_to_complete();

    // uint32_t end = tc[T1_COUNT];
    if (tc[T1_MASK_INT]) {
        transfer_timer_overruns++;
        uint32_t diff = tc[T1_LOAD] - tc[T1_COUNT];
        if (diff > max_transfer_timer_overrun) {
            max_transfer_timer_overrun = diff;
        }
    }

    spin1_mode_restore(cspr);
}

//! \brief Read a synaptic row from SDRAM into a local buffer.
static inline void read_synaptic_row(spike_t spike, synaptic_row_t row,
        uint32_t n_bytes) {
    dma_buffer *buffer = &dma_buffers[next_buffer_to_fill];
    buffer->sdram_writeback_address = row;
    buffer->originating_spike = spike;
    buffer->n_bytes_transferred = n_bytes;
    do_fast_dma_read(row, buffer->row, n_bytes);
    next_buffer_to_fill = (next_buffer_to_fill + 1) & DMA_BUFFER_MOD_MASK;
}

//! \brief Get the next spike, keeping track of provenance data
//! \param[in] time Simulation time step
//! \param[out] spike Pointer to receive the next spike
//! \return True if a spike was retrieved
static inline bool get_next_spike(uint32_t time, spike_t *spike) {
    uint32_t n_spikes = in_spikes_size();
    if (biggest_fill_size_of_input_buffer < n_spikes) {
        biggest_fill_size_of_input_buffer = n_spikes;
    }
    if (!in_spikes_get_next_spike(spike)) {
        return false;
    }
    // Detect a looped back spike
    if ((*spike & key_config.mask) == key_config.key) {
        synapse_dynamics_process_post_synaptic_event(
                time, *spike & key_config.spike_id_mask);
        return key_config.self_connected;
    }
    return true;
}

//! \brief Start the first DMA after awaking from spike reception.  Loops over
//!        available spikes until one causes a DMA.
//! \param[in] time Simulation time step
//! \param[in/out] spike Starts as the first spike received, but might change
//!                      if the first spike doesn't cause a DMA
//! \return True if a DMA was started
static inline bool start_first_dma(uint32_t time, spike_t *spike) {
    synaptic_row_t row;
    uint32_t n_bytes;

    do {
        if (population_table_get_first_address(*spike, &row, &n_bytes)) {
            read_synaptic_row(*spike, row, n_bytes);
            return true;
        }
    } while (!is_end_of_time_step() && get_next_spike(time, spike));

    return false;
}

//! \brief Get the details for the next DMA, but don't start it.
//! \param[in] time Simulation time step
//! \param[out] spike Pointer to receive the spike the DMA relates to
//! \param[out] row Pointer to receive the address to be transferred
//! \param[out] n_bytes Pointer to receive the number of bytes to transfer
//! \return True if there is a DMA to do
static inline bool get_next_dma(uint32_t time, spike_t *spike, synaptic_row_t *row,
        uint32_t *n_bytes) {
    if (population_table_is_next() && population_table_get_next_address(
            spike, row, n_bytes)) {
        return true;
    }

    while (!is_end_of_time_step() && get_next_spike(time, spike)) {
        if (population_table_get_first_address(*spike, row, n_bytes)) {
            return true;
        }
    }

    return false;
}

//! \brief Handle a synapse processing error.
//! \param[in] buffer The DMA buffer that was being processed
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
    if (fixed_synapse > (buffer->n_bytes_transferred >> 2)) {
        log_error("Too many fixed synapses: %u", fixed_synapse);
        rt_error(RTE_SWERR);
    }
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

//! \brief Process a row that has been transferred
//! \param[in] time The current time step of the simulation
//! \param[in] dma_in_progress Whether there was a DMA started and not checked
static inline void process_current_row(uint32_t time, bool dma_in_progress) {
    bool write_back = false;
    dma_buffer *buffer = &dma_buffers[next_buffer_to_process];

    if (!synapses_process_synaptic_row(time, buffer->row, &write_back)) {
        handle_row_error(buffer);
    }
    synaptogenesis_spike_received(time, buffer->originating_spike);
    spike_processing_count++;
    if (write_back) {
        uint32_t n_bytes = synapse_row_plastic_size(buffer->row) * sizeof(uint32_t);
        void *system_address = synapse_row_plastic_region(
                buffer->sdram_writeback_address);
        void *tcm_address = synapse_row_plastic_region(buffer->row);
        // Make sure an outstanding DMA is completed before starting this one
        if (dma_in_progress) {
            wait_for_dma_to_complete();
        }
        do_fast_dma_write(tcm_address, system_address, n_bytes);
        // Only wait for this DMA to complete if there isn't another running,
        // as otherwise the next wait will fail!
        if (!dma_in_progress) {
            wait_for_dma_to_complete();
        }
    }
    next_buffer_to_process = (next_buffer_to_process + 1) & DMA_BUFFER_MOD_MASK;
    spikes_processed_this_time_step++;
}

//! \brief Store data for provenance and recordings
//! \param[in] time The time step of the simulation
static inline void store_data(uint32_t time) {
    // Record the number of packets still left
    uint32_t n_spikes_left = in_spikes_size();
    count_input_buffer_packets_late += n_spikes_left;
    if (n_spikes_left > max_spikes_overflow) {
        max_spikes_overflow = n_spikes_left;
    }

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

//! \brief Measure how long it takes to transfer buffers
static inline void measure_transfer_time(void) {
    // Measure the time to do an upload to know when to schedule the timer
    tc[T2_LOAD] = 0xFFFFFFFF;
    tc[T2_CONTROL] = 0x82;
    transfer_buffers(0);
    wait_for_dma_to_complete();
    clocks_to_transfer = (0xFFFFFFFF - tc[T2_COUNT])
            + sdram_inputs.time_for_transfer_overhead;
    tc[T2_CONTROL] = 0;
    log_info("Transfer of %u bytes to 0x%08x took %u cycles",
            sdram_inputs.size_in_bytes, sdram_inputs.address, clocks_to_transfer);
}

//! \brief Prepare the start of a time step
//! \param[in] time The time step being executed
//! \return Whether we should proceed or not
static inline bool prepare_timestep(uint32_t time) {
    uint32_t cspr = spin1_int_disable();

    // Reset these to ensure consistency
    next_buffer_to_fill = 0;
    next_buffer_to_process = 0;

    // We do this here rather than during init, as it should have similar
    // contention to the expected time of execution
    if (clocks_to_transfer == 0) {
        measure_transfer_time();
    }

    // Start timer2 to tell us when to stop
    uint32_t timer = tc[T1_COUNT];
    if (timer < clocks_to_transfer) {
        return false;
    }
    uint32_t time_until_stop = timer - clocks_to_transfer;
    tc[T2_CONTROL] = 0;
    tc[T2_LOAD] = time_until_stop;
    tc[T2_CONTROL] = 0xe3;

    log_debug("Start of time step %d, timer = %d, loading with %d",
            time, timer, time_until_stop);

    // Store recording data from last time step
    store_data(time);

    // Clear the buffer if needed
    if (clear_input_buffers_of_late_packets) {
        in_spikes_clear();
    }
    p_per_ts_struct.packets_this_time_step = 0;
    spikes_processed_this_time_step = 0;

    synapses_flush_ring_buffers(time);
    spin1_mode_restore(cspr);
    return true;
}

//! \brief Perform synaptic rewiring for this time step
//! \param[in] time The current time step
//! \param[in] n_rewires The number of rewirings to try
static inline void do_rewiring(uint32_t time, uint32_t n_rewires) {
    uint32_t spike;
    synaptic_row_t row;
    uint32_t n_bytes;

    uint32_t current_buffer = 0;
    uint32_t next_buffer = 0;
    bool dma_in_progress = false;

    // Start the first transfer
    uint32_t rewires_to_go = n_rewires;
    while (rewires_to_go > 0 && !dma_in_progress) {
        if (synaptogenesis_dynamics_rewire(time, &spike, &row, &n_bytes)) {
            dma_buffers[next_buffer].sdram_writeback_address = row;
            dma_buffers[next_buffer].n_bytes_transferred = n_bytes;
            do_fast_dma_read(row, dma_buffers[next_buffer].row, n_bytes);
            next_buffer = (next_buffer + 1) & DMA_BUFFER_MOD_MASK;
            dma_in_progress = true;
        }
        rewires_to_go--;
    }

    // Go in a loop until all done
    while (dma_in_progress) {

        // Start the next DMA if possible
        dma_in_progress = false;
        while (rewires_to_go > 0 && !dma_in_progress) {
            if (synaptogenesis_dynamics_rewire(time, &spike, &row, &n_bytes)) {
                dma_in_progress = true;
            }
            rewires_to_go--;
        }

        // Wait for the last DMA to complete
        wait_for_dma_to_complete();

        // Start the next DMA read
        if (dma_in_progress) {
            dma_buffers[next_buffer].sdram_writeback_address = row;
            dma_buffers[next_buffer].n_bytes_transferred = n_bytes;
            do_fast_dma_read(row, dma_buffers[next_buffer].row, n_bytes);
            next_buffer = (next_buffer + 1) & DMA_BUFFER_MOD_MASK;
        }

        // If the row has been restructured, transfer back to SDRAM
        if (synaptogenesis_row_restructure(
                time, dma_buffers[current_buffer].row)) {
            n_successful_rewires++;
            if (dma_in_progress) {
                wait_for_dma_to_complete();
            }
            do_fast_dma_write(
                    dma_buffers[current_buffer].row,
                    dma_buffers[current_buffer].sdram_writeback_address,
                    dma_buffers[current_buffer].n_bytes_transferred);
            if (!dma_in_progress) {
                wait_for_dma_to_complete();
            }
        }
        current_buffer = (current_buffer + 1) & DMA_BUFFER_MOD_MASK;
    }
}

void spike_processing_fast_time_step_loop(uint32_t time, uint32_t n_rewires) {

    // Prepare for the start
    if (!prepare_timestep(time)) {
        skipped_time_steps++;
        process_end_of_time_step(time);
        return;
    }

    // Do rewiring
    do_rewiring(time, n_rewires);

    // Loop until the end of a time step is reached
    while (true) {

        // Wait for a spike, or the timer to expire
        uint32_t spike;
        while (!is_end_of_time_step() && !get_next_spike(time, &spike)) {
            // This doesn't wait for interrupt currently because there isn't
            // a way to have a T2 interrupt without a callback function, and
            // a callback function is too slow!  This is therefore a busy wait.
            // wait_for_interrupt();
        }

        // If the timer has gone off, that takes precedence
        if (is_end_of_time_step()) {
            clear_end_of_time_step();
            process_end_of_time_step(time);
            return;
        }

        // There must be a spike!  Start a DMA processing loop...
        bool dma_in_progress = start_first_dma(time, &spike);
        while (dma_in_progress && !is_end_of_time_step()) {

            // See if there is another DMA to do
            synaptic_row_t row;
            uint32_t n_bytes;
            dma_in_progress = get_next_dma(time, &spike, &row, &n_bytes);

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
            process_current_row(time, dma_in_progress);
        }
    }
}

static inline void check_times(void) {
    uint32_t tc_time = tc[T1_COUNT];
    if (tc_time > earliest_spike_received_time) {
        earliest_spike_received_time = tc_time;
    }
    if (tc_time < latest_spike_received_time) {
        latest_spike_received_time = tc_time;
    }
}

//! \brief Called when a multicast packet is received
//! \param[in] key: The key of the packet. The spike.
//! \param payload: the payload of the packet. The count.
void multicast_packet_received_callback(uint key, UNUSED uint unused) {
    log_debug("Received spike %x", key);
    p_per_ts_struct.packets_this_time_step++;
    in_spikes_add_spike(key);
    check_times();
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
    check_times();
}

bool spike_processing_fast_initialise(
        uint32_t row_max_n_words, uint32_t spike_buffer_size,
        bool discard_late_packets, uint32_t pkts_per_ts_rec_region,
        uint32_t multicast_priority, struct sdram_config sdram_inputs_param,
        struct key_config key_config_param, weight_t *ring_buffers_param) {
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
    key_config = key_config_param;
    ring_buffers = ring_buffers_param;

    // Configure for multicast reception
    spin1_callback_on(MC_PACKET_RECEIVED, multicast_packet_received_callback,
            multicast_priority);
    spin1_callback_on(MCPL_PACKET_RECEIVED, multicast_packet_pl_received_callback,
            multicast_priority);

    // Wipe the inputs using word writes
    for (uint32_t i = 0; i < (sdram_inputs.size_in_bytes >> 2); i++) {
        sdram_inputs.address[i] = 0;
    }

    return true;
}

void spike_processing_fast_store_provenance(
        struct spike_processing_fast_provenance *prov) {
    prov->n_input_buffer_overflows = in_spikes_get_n_buffer_overflows();
    prov->n_dmas_complete = dma_complete_count;
    prov->n_spikes_processed = spike_processing_count;
    prov->n_rewires = n_successful_rewires;
    prov->n_packets_dropped_from_lateness = count_input_buffer_packets_late;
    prov->max_filled_input_buffer_size = biggest_fill_size_of_input_buffer;
    prov->max_spikes_processed = max_spikes_processed;
    prov->max_spikes_received = max_spikes_received;
    prov->n_transfer_timer_overruns = transfer_timer_overruns;
    prov->n_skipped_time_steps = skipped_time_steps;
    prov->max_transfer_timer_overrun = max_transfer_timer_overrun;
    prov->earliest_receive = earliest_spike_received_time;
    prov->latest_receive = latest_spike_received_time;
    prov->max_spikes_overflow = max_spikes_overflow;
}
