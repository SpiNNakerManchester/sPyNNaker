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

#include "c_main_neuron.h"
#include "c_main_common.h"
#include "profile_tags.h"
extern void spin1_wfi(void);

//! values for the priority for each callback
typedef enum callback_priorities {
    DMA = 0, USER = 0, SDP = 1, TIMER = 2
} callback_priorities;

enum regions {
    SYSTEM_REGION,
    PROVENANCE_DATA_REGION,
    PROFILER_REGION,
    RECORDING_REGION,
    NEURON_PARAMS_REGION,
    NEURON_RECORDING_REGION,
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

const struct neuron_regions NEURON_REGIONS = {
    .neuron_params = NEURON_PARAMS_REGION,
    .neuron_recording = NEURON_RECORDING_REGION
};

//! A region of SDRAM used to transfer synapses
struct sdram_config {
    //! The start address of the input data to be transferred
    uint8_t *address;
    //! The size of the input data to be transferred per core
    uint32_t size_in_bytes;
    //! The number of neurons
    uint32_t n_neurons;
    //! The number of synapse types
    uint32_t n_synapse_types;
    //! The number of synapse cores feeding into here
    uint32_t n_synapse_cores;
    //! The number of bits needed for the neurons
    uint32_t synapse_index_bits;
};

//! The number of buffers for synaptic data (one processing, one in progress)
#define N_SYNAPTIC_BUFFERS 2

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

//! The SDRAM input configuration data
static struct sdram_config sdram_inputs;

//! The inputs from the various synapse cores
static weight_t *synaptic_contributions[N_SYNAPTIC_BUFFERS];

//! Variable to indicate DMA completion
static bool dma_complete;

//! timer count for TDMA of certain models; exported
uint global_timer_count;

static void dma_complete_callback(UNUSED uint unused0, UNUSED uint unused1) {
    dma_complete = true;
}

//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void store_provenance_data(address_t provenance_region) {
    struct neuron_provenance *prov = (void *) provenance_region;
    store_neuron_provenance(prov);
}

//! \brief the function to call when resuming a simulation
void resume_callback(void) {

    // Reset recording
    recording_reset();

    // try resuming neuron
    if (!neuron_resume()) {
        log_error("failed to resume neuron.");
        rt_error(RTE_SWERR);
    }
}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused: unused parameter kept for API consistency
void timer_callback(uint timer_count, UNUSED uint unused) {

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    global_timer_count = timer_count;

    time++;

    log_debug("Timer tick %u \n", time);

    /* if a fixed number of simulation ticks that were specified at startup
     * then do reporting for finishing */
    if (simulation_is_finished()) {

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // Pause neuron processing
        neuron_pause();

        // Pause common functions
        common_pause(recording_flags);

        profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        simulation_ready_to_read();
        return;
    }

    // Start the transfer of the first part of the weight data
    uint8_t *sdram = sdram_inputs.address;
    uint32_t write_index = 0;
    uint32_t read_index = 0;
    dma_complete = false;
    spin1_dma_transfer(0, sdram, synaptic_contributions[write_index], DMA_READ,
            sdram_inputs.size_in_bytes);
    write_index = !write_index;

    for (uint32_t i = 0; i < sdram_inputs.n_synapse_cores; i++) {
        // Wait for the last DMA to complete
        while (!dma_complete) {
            spin1_wfi();
        }

        // Start the next DMA if not finished
        if (i + 1 < sdram_inputs.n_synapse_cores) {
            dma_complete = false;
            sdram += sdram_inputs.size_in_bytes;
            spin1_dma_transfer(0, sdram, synaptic_contributions[write_index],
                    DMA_READ, sdram_inputs.size_in_bytes);
            write_index = !write_index;
        }

        // Read the data while the next transfer happens
        // Transfer the input from the ring buffers into the input buffers
        for (uint32_t neuron_index = 0; neuron_index < sdram_inputs.n_neurons;
                neuron_index++) {
            // Loop through all synapse types
            for (uint32_t synapse_type_index = 0;
                    synapse_type_index < sdram_inputs.n_synapse_types;
                    synapse_type_index++) {
                // Get the index, knowing that there is only the front of the
                // ring buffers here, so use time = 0
                // and synapse_type_index_bits then doesn't matter.
                uint32_t ring_buffer_index = synapse_row_get_ring_buffer_index(
                        0, synapse_type_index, neuron_index,
                        0, sdram_inputs.synapse_index_bits, 0);

                // Convert ring-buffer entry to input and add on to correct
                // input for this synapse type and neuron
                weight_t value = synaptic_contributions[read_index][ring_buffer_index];
                if (value != 0) {
                    neuron_add_inputs(synapse_type_index, neuron_index, value);
                }
            }
        }
        read_index = !read_index;
    }

    // Now do neuron time step update
    neuron_do_timestep_update(time, timer_count);

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

    // Setup neurons
    uint32_t n_rec_regions_used;
    if (!initialise_neuron_regions(
            ds_regions, NEURON_REGIONS,  &n_rec_regions_used)) {
        return false;
    }

    // Setup for reading synaptic inputs at start of each time step
    struct sdram_config * sdram_config = data_specification_get_region(
            SDRAM_PARAMS_REGION, ds_regions);
    spin1_memcpy(&sdram_inputs, sdram_config, sizeof(struct sdram_config));

    log_debug("Transferring ring buffers from 0x%08x for %d neurons (%d bits) "
            "and %d synapse types from %d cores using %d bytes per core",
            sdram_inputs.address, sdram_inputs.n_neurons,
            sdram_inputs.synapse_index_bits, sdram_inputs.n_synapse_types,
            sdram_inputs.n_synapse_cores, sdram_inputs.size_in_bytes);

    for (uint32_t i = 0; i < N_SYNAPTIC_BUFFERS; i++) {
        synaptic_contributions[i] = spin1_malloc(sdram_inputs.size_in_bytes);
        if (synaptic_contributions == NULL) {
            log_error("Could not allocate %d bytes for synaptic contributions %d",
                    sdram_inputs.size_in_bytes, i);
            return false;
        }
    }

    // Add DMA complete callback
    simulation_dma_transfer_done_callback_on(0, dma_complete_callback);

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
