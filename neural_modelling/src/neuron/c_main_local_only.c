/*
 * Copyright (c) 2021-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "c_main_neuron_common.h"
#include "c_main_common.h"
#include "profile_tags.h"
#include "local_only/local_only_impl.h"
#include "local_only.h"
#include "synapse_row.h"

#define SYNAPSE_TYPE

//! The combined provenance from synapses and neurons
struct combined_provenance {
    struct neuron_provenance neuron_provenance;
    struct local_only_provenance local_only_provenance;
    //! Maximum backgrounds queued
    uint32_t max_backgrounds_queued;
    //! Background queue overloads
    uint32_t n_background_queue_overloads;
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
	CORE_PARAMS_REGION,
    NEURON_PARAMS_REGION,
    CURRENT_SOURCE_PARAMS_REGION,
    NEURON_RECORDING_REGION,
    LOCAL_ONLY_REGION,
    LOCAL_ONLY_PARAMS_REGION,
	NEURON_BUILDER_REGION,
	INITIAL_VALUES_REGION
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

//! From the regions, extract those that are neuron-specific
const struct neuron_regions NEURON_REGIONS = {
	.core_params = CORE_PARAMS_REGION,
    .neuron_params = NEURON_PARAMS_REGION,
    .current_source_params = CURRENT_SOURCE_PARAMS_REGION,
    .neuron_recording = NEURON_RECORDING_REGION,
	.initial_values = INITIAL_VALUES_REGION
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

//! The number of background tasks queued / running
static uint32_t n_backgrounds_queued = 0;

//! The number of times the background couldn't be added
static uint32_t n_background_overloads = 0;

//! The maximum number of background tasks queued
static uint32_t max_backgrounds_queued = 0;

//! The ring buffers to be used in the simulation
static uint16_t *ring_buffers;

void synapse_dynamics_process_post_synaptic_event(
        UNUSED uint32_t time, UNUSED index_t neuron_index) {
}

//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void c_main_store_provenance_data(address_t provenance_region) {
    struct combined_provenance *prov = (void *) provenance_region;
    prov->n_background_queue_overloads = n_background_overloads;
    prov->max_backgrounds_queued = max_backgrounds_queued;
    store_neuron_provenance(&prov->neuron_provenance);
    local_only_store_provenance(&prov->local_only_provenance);
}

//! \brief the function to call when resuming a simulation
void resume_callback(void) {

    // Reset recording
    recording_reset();

    // try resuming neuron
    if (!neuron_resume(time + 1)) {
        log_error("failed to resume neuron.");
        rt_error(RTE_SWERR);
    }
}

//! Process the ring buffers for the next time step
static inline void process_ring_buffers(void) {
    uint32_t first_index = synapse_row_get_first_ring_buffer_index(
            time, synapse_type_index_bits, synapse_delay_mask);
    neuron_transfer(&ring_buffers[first_index]);

    // Print the neuron inputs.
    #if LOG_LEVEL >= LOG_DEBUG
        log_debug("Inputs");
        neuron_print_inputs();
    #endif // LOG_LEVEL >= LOG_DEBUG
}

//! \brief Background activities called from timer
//! \param timer_count the number of times this call back has been
//!        executed since start of simulation
//! \param[in] local_time: The time step being executed
void background_callback(uint timer_count, uint local_time) {
    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    log_debug("Timer tick %u \n", local_time);

    // Now do neuron time step update
    neuron_do_timestep_update(local_time, timer_count);

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);
    n_backgrounds_queued--;
}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused: unused parameter kept for API consistency
void timer_callback(uint timer_count, UNUSED uint unused) {
    // Disable interrupts to stop MC getting in the way of this bit
    uint32_t state = spin1_int_disable();

    // Increment time step
    time++;

    // Clear any outstanding spikes
    local_only_clear_input(time);

    // Allow things to interrupt again
    spin1_mode_restore(state);

    // Process ring buffers for the inputs from last time step
    process_ring_buffers();

    /* if a fixed number of simulation ticks that were specified at startup
     * then do reporting for finishing */
    if (simulation_is_finished()) {

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // Pause neuron processing
        neuron_pause();

        // Pause common functions
        common_pause(recording_flags);

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        simulation_ready_to_read();
        return;
    }

    // Push the rest to the background
    if (!spin1_schedule_callback(background_callback, timer_count, time, BACKGROUND)) {
        // We have failed to do this timer tick!
        n_background_overloads++;
    } else {
        n_backgrounds_queued++;
        if (n_backgrounds_queued > max_backgrounds_queued) {
            max_backgrounds_queued++;
        }
    }
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

    // Setup neurons
    uint32_t n_rec_regions_used;
    if (!initialise_neuron_regions(
            ds_regions, NEURON_REGIONS,  &n_rec_regions_used)) {
        return false;
    }

    if (!local_only_initialise(
            data_specification_get_region(LOCAL_ONLY_REGION, ds_regions),
            data_specification_get_region(LOCAL_ONLY_PARAMS_REGION, ds_regions),
            n_rec_regions_used, &ring_buffers)) {
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
