/*
 * Copyright (c) 2021-2022 The University of Manchester
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

#include "c_main_common.h"
#include "profile_tags.h"
#include "local_only/local_only_impl.h"
#include "local_only_fast.h"
#include "synapse_row.h"

#define SYNAPSE_TYPE

//! The combined provenance from synapses and neurons
struct combined_provenance {
    struct local_only_provenance local_only_provenance;
};

//! Identify the priorities for all tasks
typedef enum callback_priorities {
    MC = -1, DMA = 0, USER = 0, TIMER = 0, SDP = 1, BACKGROUND = 1
} callback_priorities;

//! Overall regions used by the synapse core
enum regions {
    SYSTEM_REGION,
    PROVENANCE_DATA_REGION,
    PROFILER_REGION,
    RECORDING_REGION,
    LOCAL_ONLY_REGION,
    LOCAL_ONLY_PARAMS_REGION,
	SDRAM_PARAMS_REGION
};

//! From the regions, extract those that are common
const struct common_regions COMMON_REGIONS = {
    .system = SYSTEM_REGION,
    .provenance = PROVENANCE_DATA_REGION,
    .profiler = PROFILER_REGION,
    .recording = RECORDING_REGION
};

//! Identify the priorities of the common tasks
const struct common_priorities COMMON_PRIORITIES = {
    .sdp = SDP,
    .dma = DMA,
    .timer = TIMER
};

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

//! The ring buffers to be used in the simulation
static uint16_t *ring_buffers;

//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void c_main_store_provenance_data(address_t provenance_region) {
    struct combined_provenance *prov = (void *) provenance_region;
    local_only_store_provenance(&prov->local_only_provenance);
}

//! \brief the function to call when resuming a simulation
void resume_callback(void) {

    // Reset recording
    recording_reset();
}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused: unused parameter kept for API consistency
void timer_callback(UNUSED uint timer_count, UNUSED uint unused) {

    // Increment time step
    time++;

    /* if a fixed number of simulation ticks that were specified at startup
     * then do reporting for finishing */
    if (simulation_is_finished()) {

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // Pause common functions
        common_pause(recording_flags);

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        simulation_ready_to_read();
        return;
    }

    local_only_fast_processing_loop(time);
}

//! \brief Initialises the model by reading in the regions and checking
//!        recording data.
//! \return True if it successfully initialised, false otherwise
static bool initialise(void) {
    log_debug("Initialise: started");

    data_specification_metadata_t *ds_regions;
    if (!initialise_common_regions(
            &timer_period, &simulation_ticks, &infinite_run, &time,
            &recording_flags, c_main_store_provenance_data, timer_callback,
            COMMON_REGIONS, COMMON_PRIORITIES, &ds_regions)) {
        return false;
    }

    // Setup for writing synaptic inputs at the end of each run
	struct sdram_config *sdram_config = data_specification_get_region(
			SDRAM_PARAMS_REGION, ds_regions);

    if (!local_only_initialise(
            data_specification_get_region(LOCAL_ONLY_REGION, ds_regions),
            data_specification_get_region(LOCAL_ONLY_PARAMS_REGION, ds_regions),
			*sdram_config, 0, &ring_buffers)) {
        return false;
    }

    // Set timer tick (in microseconds)
    log_debug("setting timer tick callback for %d microseconds", timer_period);
    spin1_set_timer_tick(timer_period);

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
