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

#include "c_main_synapse_common.h"
#include "c_main_common.h"
#include "spike_processing_fast.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include <spin1_api_params.h>

//! values for the priority for each callback
typedef enum callback_priorities {
    MC = -1, DMA = -2, TIMER = 0, SDP = 0
} callback_priorities;

//! Provenance data region layout
struct provenance_data {
    struct synapse_provenance synapse_prov;
    struct spike_processing_fast_provenance spike_processing_prov;
};

//! Overall regions used by the synapse core
enum regions {
    SYSTEM_REGION,
    PROVENANCE_DATA_REGION,
    PROFILER_REGION,
    RECORDING_REGION,
    SYNAPSE_PARAMS_REGION,
    SYNAPTIC_MATRIX_REGION,
    POPULATION_TABLE_REGION,
    SYNAPSE_DYNAMICS_REGION,
    STRUCTURAL_DYNAMICS_REGION,
    BIT_FIELD_FILTER_REGION,
    SDRAM_PARAMS_REGION,
    KEY_REGION
};

//! From the regions, select those that are common
const struct common_regions COMMON_REGIONS = {
    .system = SYSTEM_REGION,
    .provenance = PROVENANCE_DATA_REGION,
    .profiler = PROFILER_REGION,
    .recording = RECORDING_REGION
};

//! Identify the priority of common tasks
const struct common_priorities COMMON_PRIORITIES = {
    .sdp = SDP,
    .dma = DMA,
    .timer = TIMER
};

//! From the regions, select those that are used for synapse-specific things
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

//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void store_provenance_data(address_t provenance_region) {
    struct provenance_data *prov = (void *) provenance_region;
    store_synapse_provenance(&prov->synapse_prov);
    spike_processing_fast_store_provenance(&prov->spike_processing_prov);
}

//! \brief the function to call when resuming a simulation
void resume_callback(void) {

    // Reset recording
    recording_reset();

    // Resume synapses
    // NOTE: at reset, time is set to UINT_MAX ahead of timer_callback(...)
    synapses_resume(time + 1);
}

//! \brief Timer event callback.
//! \param[in] unused0: unused
//! \param[in] unused1: unused
void timer_callback(UNUSED uint unused0, UNUSED uint unused1) {
    time++;
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

    uint32_t n_rewires = synaptogenesis_n_updates();
    spike_processing_fast_time_step_loop(time, n_rewires);
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

    // Setup synapses
    uint32_t incoming_spike_buffer_size;
    uint32_t row_max_n_words;
    bool clear_input_buffer_of_late_packets;
    weight_t *ring_buffers;
    uint32_t n_rec_regions_used = 0;
    if (!initialise_synapse_regions(
            ds_regions, SYNAPSE_REGIONS, &ring_buffers, &row_max_n_words,
            &incoming_spike_buffer_size,
            &clear_input_buffer_of_late_packets, &n_rec_regions_used)) {
        return false;
    }

    // Setup for writing synaptic inputs at the end of each run
    struct sdram_config *sdram_config = data_specification_get_region(
            SDRAM_PARAMS_REGION, ds_regions);
    struct key_config *key_config = data_specification_get_region(
            KEY_REGION, ds_regions);

    if (!spike_processing_fast_initialise(
            row_max_n_words, incoming_spike_buffer_size,
            clear_input_buffer_of_late_packets, n_rec_regions_used, MC,
            *sdram_config, *key_config, ring_buffers)) {
        return false;
    }

    // Do bitfield configuration last to only use any unused memory
    if (!population_table_load_bitfields(data_specification_get_region(
            SYNAPSE_REGIONS.bitfield_filter, ds_regions))) {
        return false;
    }

    // Set timer tick (in microseconds)
    log_debug("setting timer tick callback for %d microseconds", timer_period);
    spin1_set_timer_tick(timer_period);

    recording_reset();

    return true;
}

//! \brief The entry point for this model.
void c_main(void) {

    // initialise the model
    if (!initialise()) {
        rt_error(RTE_API);
    }

    simulation_run();
}
