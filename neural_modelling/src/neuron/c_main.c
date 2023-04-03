/*
 * Copyright (c) 2014 The University of Manchester
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
#include "c_main_synapse_common.h"
#include "c_main_common.h"
#include "regions.h"
#include "profile_tags.h"
#include "spike_processing.h"

//! The combined provenance from synapses and neurons
struct combined_provenance {
    struct neuron_provenance neuron_provenance;
    struct synapse_provenance synapse_provenance;
    struct spike_processing_provenance spike_processing_provenance;
    //! Maximum backgrounds queued
    uint32_t max_backgrounds_queued;
    //! Background queue overloads
    uint32_t n_background_queue_overloads;
};

//! Identify the priorities for all tasks
typedef enum callback_priorities {
    MC = -1, DMA = 0, USER = 0, TIMER = 0, SDP = 1, BACKGROUND = 1
} callback_priorities;

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

//! From the regions, extract those that are synapse-specific
const struct synapse_regions SYNAPSE_REGIONS = {
    .synapse_params = SYNAPSE_PARAMS_REGION,
    .synaptic_matrix = SYNAPTIC_MATRIX_REGION,
    .pop_table = POPULATION_TABLE_REGION,
    .synapse_dynamics = SYNAPSE_DYNAMICS_REGION,
    .structural_dynamics = STRUCTURAL_DYNAMICS_REGION,
    .bitfield_filter = BIT_FIELD_FILTER_REGION
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
static weight_t *ring_buffers;

//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void c_main_store_provenance_data(address_t provenance_region) {
    struct combined_provenance *prov = (void *) provenance_region;
    prov->n_background_queue_overloads = n_background_overloads;
    prov->max_backgrounds_queued = max_backgrounds_queued;
    store_neuron_provenance(&prov->neuron_provenance);
    store_synapse_provenance(&prov->synapse_provenance);
    spike_processing_store_provenance(&prov->spike_processing_provenance);
}

//! \brief the function to call when resuming a simulation
void resume_callback(void) {

    // Reset recording
    recording_reset();

    // try resuming neuron
    // NOTE: at reset, time is set to UINT_MAX ahead of timer_callback(...)
    if (!neuron_resume(time + 1)) {
        log_error("failed to resume neuron.");
        rt_error(RTE_SWERR);
    }

    // Resume synapses
    // NOTE: at reset, time is set to UINT_MAX ahead of timer_callback(...)
    synapses_resume(time + 1);
}

//! Process the ring buffers for the next time step
static inline void process_ring_buffers(void) {
    uint32_t first_index = synapse_row_get_first_ring_buffer_index(
            time, synapse_type_index_bits, synapse_delay_mask);
//	log_info("process_ring_buffers, synapse_delay_mask is %u first_index %u ring_buffer %d",
//			synapse_delay_mask, first_index, ring_buffers[first_index]);
    neuron_transfer(&ring_buffers[first_index]);

    // Print the neuron inputs.
    #if LOG_LEVEL >= LOG_DEBUG
        neuron_print_inputs();
    #endif // LOG_LEVEL >= LOG_DEBUG
}

//! \brief Background activities called from timer
//! \param timer_count the number of times this call back has been
//!        executed since start of simulation
//! \param[in] local_time: The time step being executed
void background_callback(uint timer_count, uint local_time) {
    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    spike_processing_do_rewiring(synaptogenesis_n_updates());

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
    // Disable interrupts to stop DMAs and MC getting in the way of this bit
    uint32_t state = spin1_int_disable();

    // Increment time step
    time++;

    // Clear any outstanding spikes
    spike_processing_clear_input_buffer(time);

    // Next bit without DMA, but with MC
    spin1_mode_restore(state);
    state = spin1_irq_disable();

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
        spin1_mode_restore(state);
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

    spin1_mode_restore(state);
}

//! \brief Initialises the model by reading in the regions and checking
//!        recording data.
//! \return True if it successfully initialised, false otherwise
static bool initialise(void) {
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

    // Setup synapses
    uint32_t incoming_spike_buffer_size;
    bool clear_input_buffer_of_late_packets;
    uint32_t row_max_n_words;
    if (!initialise_synapse_regions(
            ds_regions, SYNAPSE_REGIONS, &ring_buffers, &row_max_n_words,
            &incoming_spike_buffer_size,
            &clear_input_buffer_of_late_packets, &n_rec_regions_used)) {
        return false;
    }

    // Setup spike processing
    if (!spike_processing_initialise(
            row_max_n_words, MC, USER, incoming_spike_buffer_size,
            clear_input_buffer_of_late_packets, n_rec_regions_used)) {
        return false;
    }

    // Do bitfield configuration last to only use any unused memory
    if (!population_table_load_bitfields(data_specification_get_region(
            SYNAPSE_REGIONS.bitfield_filter, ds_regions))) {
        return false;
    }

    // Set timer tick (in microseconds)
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
