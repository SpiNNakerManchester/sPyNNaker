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

/*!
 * @dir
 * @brief Implementation of simulator for a single neural population on a
 *      SpiNNaker CPU core. Or rather of a slice of a population.
 *
 * @file
 * @brief This file contains the main function of the application framework,
 *      which the application programmer uses to configure and run applications.
 *
 * This is the main entrance class for most of the neural models. The following
 * Figure shows how all of the c code
 * interacts with each other and what classes
 * are used to represent over arching logic
 * (such as plasticity, spike processing, utilities, synapse types, models)
 *
 * @image html spynnaker_c_code_flow.png
 */

#include "c_main_synapse.h"
#include "c_main_common.h"
#include <spin1_api_params.h>

//! values for the priority for each callback
typedef enum callback_priorities {
    MC = -1, DMA = 0, USER = 0, TIMER = 0, SDP = 0
} callback_priorities;

enum regions {
    SYSTEM_REGION,
    PROVENANCE_DATA_REGION,
    PROFILER_REGION,
    RECORDING_REGION,
    SYNAPSE_PARAMS_REGION,
    DIRECT_MATRIX_REGION,
    SYNAPTIC_MATRIX_REGION,
    POPULATION_TABLE_REGION,
    SYNAPSE_DYNAMICS_REGION,
    STRUCTURAL_DYNAMICS_REGION,
    BIT_FIELD_FILTER_REGION,
    SDRAM_PARAMS_REGION
};

const struct common_regions COMMON_REGIONS = {
    .system = SYSTEM_REGION,
    .provenance = PROVENANCE_DATA_REGION,
    .profiler = PROFILER_REGION,
    .recording = RECORDING_REGION
};

const struct common_priorities COMMON_PRIORITIES = {
    .sdp = SDP,
    .dma = DMA,
    .timer = TIMER
};

const struct synapse_regions SYNAPSE_REGIONS = {
    .synapse_params = SYNAPSE_PARAMS_REGION,
    .direct_matrix = DIRECT_MATRIX_REGION,
    .synaptic_matrix = SYNAPTIC_MATRIX_REGION,
    .pop_table = POPULATION_TABLE_REGION,
    .synapse_dynamics = SYNAPSE_DYNAMICS_REGION,
    .structural_dynamics = STRUCTURAL_DYNAMICS_REGION,
    .bitfield_filter = BIT_FIELD_FILTER_REGION
};

const struct synapse_priorities SYNAPSE_PRIORITIES = {
    .process_synapses = USER,
    .receive_packet = MC
};

//! A region of SDRAM used to transfer synapses
struct sdram_config {
    //! The address of the input data to be transferred
    uint32_t *address;
    //! The size of the input data to be transferred
    uint32_t size_in_bytes;
    //! The time of the transfer in us
    uint32_t time_for_transfer;
};

static const uint32_t DMA_FLAGS = DMA_WIDTH << 24 | DMA_BURST_SIZE << 21
        | DMA_WRITE << 19;

//! A tag to indicate that the DMA of synaptic inputs is complete
#define DMA_COMPLETE_TAG 10

//! The number of clock cycles of overhead for the callback
#define CALLBACK_OVERHEAD_CLOCKS 20

// Globals

//! The current timer tick value.
// the timer tick callback returning the same value.
uint32_t time;

//! timer tick period (in microseconds)
static uint32_t timer_period;

//! The number of timer ticks to run for before being expected to exit
static uint32_t simulation_ticks = 0;

//! Determines if this model should run for infinite time
static uint32_t infinite_run;

//! The recording flags indicating if anything is recording
static uint32_t recording_flags = 0;

//! Where synaptic input is to be written
static struct sdram_config sdram_inputs;

// The ring buffers to use
static weight_t *ring_buffers;

// The time to transfer
static uint32_t clocks_to_transfer;

// The number of words in the ring buffer to skip to get to the next time
static uint32_t ring_buffer_skip_words;

static inline void write(weight_t *tcm_address, uint32_t *system_address,
        uint32_t length) {
    dma[DMA_CTRL] = 0x1f;
    dma[DMA_CTRL] = 0x0d;
    uint32_t desc = DMA_FLAGS | length;
    dma[DMA_ADRS] = (uint32_t) system_address;
    dma[DMA_ADRT] = (uint32_t) tcm_address;
    dma[DMA_DESC] = desc;
}

//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void store_provenance_data(address_t provenance_region) {
    struct synapse_provenance *prov = (void *) provenance_region;
    store_synapse_provenance(prov);
}

//! \brief the function to call when resuming a simulation
void resume_callback(void) {

    // Reset recording
    recording_reset();

    // Resume synapses
    // NOTE: at reset, time is set to UINT_MAX ahead of timer_callback(...)
    synapses_resume(time + 1);
}

extern cback_t callback[NUM_EVENTS];

static inline void process_ring_buffers(uint32_t local_time) {
    // Get the index of the first ring buffer for the next time step
    uint32_t first_ring_buffer = synapse_row_get_first_ring_buffer_index(local_time,
            synapse_type_index_bits, synapse_delay_mask);
    // Make sure we don't do a DMA complete callback for this bit
    cback_t cback = callback[DMA_TRANSFER_DONE];
    spin1_callback_off(DMA_TRANSFER_DONE);
    // Do the DMA transfer
    log_debug("Writing %d bytes to 0x%08x from ring buffer %d",
             sdram_inputs.size_in_bytes, sdram_inputs.address, first_ring_buffer);
    write(&ring_buffers[first_ring_buffer], sdram_inputs.address,
            sdram_inputs.size_in_bytes);
    // Wait for completion of DMAs and then restore the callback
    while (!(dma[DMA_STAT] & (1 << 10))) {
        continue;
    }
    dma[DMA_CTRL] = 0x1f;
    dma[DMA_CTRL] = 0x0d;
    spin1_callback_on(DMA_TRANSFER_DONE, cback.cback, cback.priority);
}

static inline void write_contributions(uint32_t local_time) {
    // Clear any outstanding spikes
    spike_processing_clear_input_buffer(local_time);
    // Copy things out of DTCM
    process_ring_buffers(local_time + 1);
    // Now clear the ring buffers
    synapses_flush_ring_buffers(local_time);
}

//! \brief writes synaptic inputs to SDRAM
INT_HANDLER timer2_callback(void) {
    // Disable interrupts to stop DMAs and MC getting in the way of this bit
    uint32_t state = spin1_int_disable();
    // Clear interrupt in timer and ACK the vic (safe as interrupts off anyway)
    tc[T2_INT_CLR] = (uint) tc;
    vic[VIC_VADDR] = (uint) vic;

    // Write the contributions
    write_contributions(time);

    // Restore interrupts
    spin1_mode_restore(state);
}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused: unused parameter kept for API consistency
void timer_callback(UNUSED uint timer_count, UNUSED uint unused) {
    time++;
    uint32_t state = spin1_int_disable();

    /* if a fixed number of simulation ticks that were specified at startup
     * then do reporting for finishing */
    if (simulation_is_finished()) {
        // Finally, clear the ring buffers

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // Pause common functions
        common_pause(recording_flags);

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        simulation_ready_to_read();
        spin1_mode_restore(state);
        return;
    }

    // Setup to call back enough before the end of the timestep to transfer
    // synapses to SDRAM for the next timestep
    tc[T2_CONTROL] = 0;
    uint32_t time_to_wait = tc[T1_COUNT] - clocks_to_transfer;
    tc[T2_LOAD] = time_to_wait;
    tc[T2_CONTROL] = 0xe3;

    // Do rewiring as needed
    synaptogenesis_do_timestep_update();

    spin1_mode_restore(state);
}

//! \brief Initialises the model by reading in the regions and checking
//!        recording data.
//! \return True if it successfully initialised, false otherwise
static bool initialise(void) {
    log_debug("Initialise: started");

    data_specification_metadata_t *ds_regions;
    if (!initialise_common_regions(
            &timer_period, &simulation_ticks, &infinite_run, &time,
            &recording_flags, store_provenance_data, timer_callback,
            COMMON_REGIONS, COMMON_PRIORITIES, &ds_regions)) {
        return false;
    }

    // Setup synapses
    uint32_t n_neurons;
    uint32_t n_synapse_types;
    if (!initialise_synapse_regions(
            ds_regions, SYNAPSE_REGIONS, SYNAPSE_PRIORITIES, 0,
            &n_neurons, &n_synapse_types, &ring_buffers)) {
        return false;
    }

    // Setup for writing synaptic inputs at the end of each run
    struct sdram_config * sdram_config = data_specification_get_region(
            SDRAM_PARAMS_REGION, ds_regions);
    spin1_memcpy(&sdram_inputs, sdram_config, sizeof(struct sdram_config));

    // Measure the time to do an upload
    tc[T2_LOAD] = 0xFFFFFFFF;
    tc[T2_CONTROL] = 0x82;
    write_contributions(0);
    clocks_to_transfer = (0xFFFFFFFF - tc[T2_COUNT]) + CALLBACK_OVERHEAD_CLOCKS;
    log_info("Transfer of %u bytes took %u cycles", sdram_inputs.size_in_bytes,
            clocks_to_transfer);
    recording_reset();

    // Prepare to receive the timer (disable timer then enable VIC entry)
    tc[T2_CONTROL] = 0;
    sark_vic_set(TIMER2_PRIORITY, TIMER2_INT, 1, timer2_callback);

    // Wipe the inputs using word writes
    for (uint32_t i = 0; i < sdram_inputs.size_in_bytes >> 2; i++) {
        sdram_inputs.address[i] = 0;
    }

    // Work out how many ring buffer entries between time steps.
    // Take the number of ring buffer entries per time step which is
    // identified by the number of bits needed by all the synapse types and
    // neuron indicies.  The number of words is this divided by 2 (the size
    // of each ring buffer entry) which is the same as shifting by 1 less.
    ring_buffer_skip_words = 1 << (synapse_type_index_bits - 1);


    log_debug("Initialise: finished");
    return true;
}


//! \brief The entry point for this model.
void c_main(void) {

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // initialise the model
    if (!initialise()) {
        rt_error(RTE_API);
    }

    simulation_run();
}
