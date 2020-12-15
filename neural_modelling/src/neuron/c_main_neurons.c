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
    NEURON_RECORDING_REGION
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
