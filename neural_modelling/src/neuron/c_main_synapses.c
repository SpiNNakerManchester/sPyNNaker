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
    MC = -1, DMA = 0, USER = 0, SDP = 1, TIMER = 2
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

//! The inverse of the number of clock cycles per ms (note assumes 200Mhz clock)
#define INVERSE_CLOCK_CYCLES 0.005k

//! A tag to indicate that the DMA of synaptic inputs is complete
#define DMA_COMPLETE_TAG 10

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

void process_ring_buffers(timer_t time, UNUSED uint32_t n_neurons,
        UNUSED uint32_t n_synapse_types, weight_t *ring_buffers) {
    // Get the index of the first ring buffer for the next time step
    uint32_t first_ring_buffer = synapse_row_get_ring_buffer_index(time + 1,
            0, 0, synapse_type_index_bits, synapse_index_bits, synapse_delay_mask);
    // Do the DMA transfer
    // log_info("Writing %d bytes to 0x%08x from ring buffer %d", sdram_inputs.size_in_bytes, sdram_inputs.address, first_ring_buffer);
    spin1_dma_transfer(DMA_COMPLETE_TAG, sdram_inputs.address,
            &ring_buffers[first_ring_buffer], DMA_WRITE,
            sdram_inputs.size_in_bytes);
}

//! \brief writes synaptic inputs to SDRAM
INT_HANDLER write_contributions(void) {
    tc[T2_INT_CLR] = (uint) tc;         // Clear interrupt in timer
    // Copy things out of DTCM
    synapses_do_timestep_update(time);
    vic[VIC_VADDR] = (uint) vic;        // Ack the VIC
}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused: unused parameter kept for API consistency
void timer_callback(UNUSED uint timer_count, UNUSED uint unused) {

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    time++;

    log_debug("Timer tick %u \n", time);

    /* if a fixed number of simulation ticks that were specified at startup
     * then do reporting for finishing */
    if (simulation_is_finished()) {
        // Finally, clear the ring buffers

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // Pause common functions
        common_pause(recording_flags);

        profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        simulation_ready_to_read();
        return;
    }

    // Setup to call back enough before the end of the timestep to transfer
    // synapses to SDRAM for the next timestep
    uint32_t cspr = spin1_int_disable();
    uint32_t timer = tc[T1_COUNT];
    uint32_t time_to_transfer = timer - (sdram_inputs.time_for_transfer * 200);
    tc[T2_LOAD] = time_to_transfer;
    tc[T2_CONTROL] = 0xe3;
    spin1_mode_restore(cspr);
    
    synapses_flush_ring_buffers(time);

    // Do rewiring as needed
    synaptogenesis_do_timestep_update();

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);
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
    if (!initialise_synapse_regions(
            ds_regions, SYNAPSE_REGIONS, SYNAPSE_PRIORITIES, 0)) {
        return false;
    }

    // Setup for writing synaptic inputs at the end of each run
    struct sdram_config * sdram_config = data_specification_get_region(
            SDRAM_PARAMS_REGION, ds_regions);
    spin1_memcpy(&sdram_inputs, sdram_config, sizeof(struct sdram_config));

    // Wipe the inputs using word writes
    for (uint32_t i = 0; i < sdram_inputs.size_in_bytes >> 2; i++) {
        sdram_inputs.address[i] = 0;
    }

    // Prepare to receive the timer
    tc[T2_CONTROL] = 0;                     // Disable timer
    event.vic_enable |= 1 << TIMER2_INT;    // Disabled by event_stop
    sark_vic_set(TIMER2_PRIORITY, TIMER2_INT, 1, write_contributions);

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
