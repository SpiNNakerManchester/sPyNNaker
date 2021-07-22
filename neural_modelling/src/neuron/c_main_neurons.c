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

#include "c_main_neuron_common.h"
#include "c_main_common.h"
#include "profile_tags.h"
#include "dma_common.h"
#include <tdma_processing.h>
#include <spin1_api_params.h>

//! values for the priority for each callback
typedef enum callback_priorities {
    DMA = -2, SDP = 0, TIMER = 0
} callback_priorities;

//! Overall regions to be used by the neuron core
enum regions {
    SYSTEM_REGION,
    PROVENANCE_DATA_REGION,
    PROFILER_REGION,
    RECORDING_REGION,
    NEURON_PARAMS_REGION,
    NEURON_RECORDING_REGION,
    SDRAM_PARAMS_REGION
};

//! From the regions, select those that are common
const struct common_regions COMMON_REGIONS = {
    .system = SYSTEM_REGION,
    .provenance = PROVENANCE_DATA_REGION,
    .profiler = PROFILER_REGION,
    .recording = RECORDING_REGION
};

//! Identify the priority of certain tasks
const struct common_priorities COMMON_PRIORITIES = {
    .sdp = SDP,
    .dma = DMA,
    .timer = TIMER
};

/**
 * From the regions, select those that are used for neuron-specific things
 */
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

//! Provenance for this specific core
struct neurons_provenance {
    uint32_t n_timer_overruns;
};

//! The number of buffers for synaptic data (one processing, one in progress)
#define N_SYNAPTIC_BUFFERS 2

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

//! The timer overruns
static uint32_t timer_overruns = 0;

//! All the synaptic contributions for adding up in 2 formats
static union {
    uint32_t *as_int;
    weight_t *as_weight;
} all_synaptic_contributions;


//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void store_provenance_data(address_t provenance_region) {
    struct neuron_provenance *prov = (void *) provenance_region;
    store_neuron_provenance(prov);
    struct neurons_provenance *n_prov = (void *) &prov[1];
    n_prov->n_timer_overruns = timer_overruns;

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

//! \brief Add up all the synaptic contributions into a global buffer
//! \param[in] syns The weights to be added
static inline void sum(weight_t *syns) {
    uint32_t n_words = sdram_inputs.size_in_bytes >> 2;
    const uint32_t *src = (const uint32_t *) syns;
    uint32_t *tgt = all_synaptic_contributions.as_int;
    for (uint32_t i = n_words; i > 0; i--) {
        *tgt++ += *src++;
    }
}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused: unused parameter kept for API consistency
void timer_callback(uint timer_count, UNUSED uint unused) {

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    uint32_t start_time = tc[T1_COUNT];

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

    // Start the first DMA
    do_fast_dma_read(sdram, synaptic_contributions[write_index],
            sdram_inputs.size_in_bytes);
    write_index = !write_index;

    for (uint32_t i = 0; i < sdram_inputs.n_synapse_cores; i++) {
        // Wait for the last DMA to complete
        wait_for_dma_to_complete();

        // Start the next DMA if not finished
        if (i + 1 < sdram_inputs.n_synapse_cores) {
            sdram += sdram_inputs.size_in_bytes;
            do_fast_dma_read(sdram, synaptic_contributions[write_index],
                    sdram_inputs.size_in_bytes);
            write_index = !write_index;
        }

        // Add in the contributions from the last read item
        sum(synaptic_contributions[read_index]);
        read_index = !read_index;
    }

    neuron_transfer(all_synaptic_contributions.as_weight);

    // Now do neuron time step update
    neuron_do_timestep_update(time, timer_count);

    uint32_t end_time = tc[T1_COUNT];
    if (end_time > start_time) {
        timer_overruns += 1;
    }

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);
}

//! \brief Initialises the model by reading in the regions and checking
//!        recording data.
//! \return True if it successfully initialised, false otherwise
static bool initialise(void) {
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

    log_info("Transferring ring buffers from 0x%08x for %d neurons (%d bits) "
            "and %d synapse types from %d cores using %d bytes per core",
            sdram_inputs.address, sdram_inputs.n_neurons,
            sdram_inputs.synapse_index_bits, sdram_inputs.n_synapse_types,
            sdram_inputs.n_synapse_cores, sdram_inputs.size_in_bytes);

    uint32_t n_words = sdram_inputs.size_in_bytes >> 2;
    for (uint32_t i = 0; i < N_SYNAPTIC_BUFFERS; i++) {
        synaptic_contributions[i] = spin1_malloc(sdram_inputs.size_in_bytes);
        if (synaptic_contributions == NULL) {
            log_error("Could not allocate %d bytes for synaptic contributions %d",
                    sdram_inputs.size_in_bytes, i);
            return false;
        }
        for (uint32_t j = 0; j < n_words; j++) {
            synaptic_contributions[i][j] = 0;
        }
    }
    all_synaptic_contributions.as_int = spin1_malloc(sdram_inputs.size_in_bytes);
    if (all_synaptic_contributions.as_int == NULL) {
        log_error("Could not allocate %d bytes for all synaptic contributions",
                sdram_inputs.size_in_bytes);
        return false;
    }
    for (uint32_t j = 0; j < n_words; j++) {
        all_synaptic_contributions.as_int[j] = 0;
    }
    uint32_t *sdram_word = (void *) sdram_inputs.address;
    for (uint32_t i = 0; i < sdram_inputs.n_synapse_cores; i++) {
        for (uint32_t j = 0; j < n_words; j++) {
            *(sdram_word++) = 0;
        }
    }
    // Set timer tick (in microseconds)
    log_debug("setting timer tick callback for %d microseconds", timer_period);
    spin1_set_timer_tick(timer_period);

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
