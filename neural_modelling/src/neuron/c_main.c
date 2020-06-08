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

#include <common/in_spikes.h>
#include "regions.h"
#include "neuron.h"
#include "synapses.h"
#include "spike_processing.h"
#include "population_table/population_table.h"
#include "plasticity/synapse_dynamics.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include "profile_tags.h"
#include "direct_synapses.h"
#include "bit_field_filter.h"

#include <data_specification.h>
#include <simulation.h>
#include <profiler.h>
#include <debug.h>
#include <bit_field.h>
#include <filter_info.h>

/* validates that the model being compiled does indeed contain a application
 * magic number*/
#ifndef APPLICATION_NAME_HASH
#error APPLICATION_NAME_HASH was undefined.  Make sure you define this\
    constant
#endif

//! The provenance information written on application shutdown.
struct neuron_provenance {
    //! A count of presynaptic events.
    uint32_t n_pre_synaptic_events;
    //! A count of synaptic saturations.
    uint32_t n_synaptic_weight_saturations;
    //! A count of the times that the synaptic input circular buffers overflowed
    uint32_t n_input_buffer_overflows;
    //! The current time.
    uint32_t current_timer_tick;
    //! The number of STDP weight saturations.
    uint32_t n_plastic_synaptic_weight_saturations;
    uint32_t n_ghost_pop_table_searches;
    uint32_t n_failed_bitfield_reads;
    uint32_t n_dmas_complete;
    uint32_t n_spikes_processed;
    uint32_t n_invalid_master_pop_table_hits;
    uint32_t n_filtered_by_bitfield;
    //! The number of rewirings performed.
    uint32_t n_rewires;
};

//! values for the priority for each callback
typedef enum callback_priorities {
    MC = -1, DMA = 0, USER = 0, SDP = 1, TIMER = 2
} callback_priorities;

//! The number of regions that are to be used for recording
#define NUMBER_OF_REGIONS_TO_RECORD 4

// Globals

//! The current timer tick value.
// the timer tick callback returning the same value.
uint32_t time;

//! timer tick period (in microseconds)
static uint32_t timer_period;

//! timer phase offset (in microseconds)
static uint32_t timer_offset;

//! The number of timer ticks to run for before being expected to exit
static uint32_t simulation_ticks = 0;

//! Determines if this model should run for infinite time
static uint32_t infinite_run;

//! Timer callbacks since last rewiring
int32_t last_rewiring_time = 0;

//! Rewiring period represented as an integer
int32_t rewiring_period = 0;

//! Flag representing whether rewiring is enabled
bool rewiring = false;

//! Count the number of rewiring attempts
uint32_t count_rewire_attempts = 0;

//! The number of neurons on the core
static uint32_t n_neurons;

//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void c_main_store_provenance_data(address_t provenance_region) {
    log_debug("writing other provenance data");
    struct neuron_provenance *prov = (void *) provenance_region;

    // store the data into the provenance data region
    prov->n_pre_synaptic_events = synapses_get_pre_synaptic_events();
    prov->n_synaptic_weight_saturations = synapses_get_saturation_count();
    prov->n_input_buffer_overflows = spike_processing_get_buffer_overflows();
    prov->current_timer_tick = time;
    prov->n_plastic_synaptic_weight_saturations =
        synapse_dynamics_get_plastic_saturation_count();
    prov->n_ghost_pop_table_searches =
        spike_processing_get_ghost_pop_table_searches();
    prov->n_failed_bitfield_reads = failed_bit_field_reads;
    prov->n_dmas_complete = spike_processing_get_dma_complete_count();
    prov->n_spikes_processed = spike_processing_get_spike_processing_count();
    prov->n_invalid_master_pop_table_hits =
        spike_processing_get_invalid_master_pop_table_hits();
    prov->n_filtered_by_bitfield = population_table_get_filtered_packet_count();
    prov->n_rewires = spike_processing_get_successful_rewires();

    log_debug("finished other provenance data");
}

//! \brief Initialises the model by reading in the regions and checking
//!        recording data.
//! \return True if it successfully initialised, false otherwise
static bool initialise(void) {
    log_debug("Initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(ds_regions)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM_REGION, ds_regions),
            APPLICATION_NAME_HASH, &timer_period, &simulation_ticks,
            &infinite_run, &time, SDP, DMA)) {
        return false;
    }
    simulation_set_provenance_function(
            c_main_store_provenance_data,
            data_specification_get_region(PROVENANCE_DATA_REGION, ds_regions));

    // Set up the neurons
    uint32_t n_synapse_types;
    uint32_t incoming_spike_buffer_size;
    if (!neuron_initialise(
            data_specification_get_region(NEURON_PARAMS_REGION, ds_regions),
            data_specification_get_region(NEURON_RECORDING_REGION, ds_regions),
            &n_neurons, &n_synapse_types, &incoming_spike_buffer_size,
            &timer_offset)) {
        return false;
    }

    // Set up the synapses
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    if (!synapses_initialise(
            data_specification_get_region(SYNAPSE_PARAMS_REGION, ds_regions),
            n_neurons, n_synapse_types,
            &ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    // set up direct synapses
    address_t direct_synapses_address;
    if (!direct_synapses_initialise(
            data_specification_get_region(DIRECT_MATRIX_REGION, ds_regions),
            &direct_synapses_address)) {
        return false;
    }

    // Set up the population table
    uint32_t row_max_n_words;
    if (!population_table_initialise(
            data_specification_get_region(POPULATION_TABLE_REGION, ds_regions),
            data_specification_get_region(SYNAPTIC_MATRIX_REGION, ds_regions),
            direct_synapses_address, &row_max_n_words)) {
        return false;
    }
    // Set up the synapse dynamics
    if (!synapse_dynamics_initialise(
            data_specification_get_region(SYNAPSE_DYNAMICS_REGION, ds_regions),
            n_neurons, n_synapse_types,
            ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    // Set up structural plasticity dynamics
    if (!synaptogenesis_dynamics_initialise(data_specification_get_region(
            STRUCTURAL_DYNAMICS_REGION, ds_regions))) {
        return false;
    }

    rewiring_period = synaptogenesis_rewiring_period();
    rewiring = rewiring_period != -1;

    if (!spike_processing_initialise(
            row_max_n_words, MC, USER, incoming_spike_buffer_size)) {
        return false;
    }

    // Setup profiler
    profiler_init(data_specification_get_region(PROFILER_REGION, ds_regions));

    log_info("initialising the bit field region");
    print_post_to_pre_entry();
    if (!bit_field_filter_initialise(data_specification_get_region(
            BIT_FIELD_FILTER_REGION, ds_regions))) {
        return false;
    }

    log_debug("Initialise: finished");
    return true;
}

//! \brief the function to call when resuming a simulation
void resume_callback(void) {
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    // try resuming neuron
    if (!neuron_resume(
            data_specification_get_region(NEURON_PARAMS_REGION, ds_regions))) {
        log_error("failed to resume neuron.");
        rt_error(RTE_SWERR);
    }

    // If the time has been reset to zero then the ring buffers need to be
    // flushed in case there is a delayed spike left over from a previous run
    // NOTE: at reset, time is set to UINT_MAX ahead of timer_callback(...)
    if ((time+1) == 0) {
    	synapses_flush_ring_buffers();
    }

}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused: unused parameter kept for API consistency
void timer_callback(uint timer_count, uint unused) {
    use(unused);

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    time++;
    last_rewiring_time++;

    // This is the part where I save the input and output indices
    //   from the circular buffer
    // If time == 0 as well as output == input == 0  then no rewire is
    //   supposed to happen. No spikes yet
    log_debug("Timer tick %u \n", time);

    /* if a fixed number of simulation ticks that were specified at startup
     * then do reporting for finishing */
    if (infinite_run != TRUE && time >= simulation_ticks) {

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        log_debug("Completed a run");

        // rewrite neuron params to SDRAM for reading out if needed
        data_specification_metadata_t *ds_regions =
                data_specification_get_data_address();
        neuron_pause(data_specification_get_region(NEURON_PARAMS_REGION, ds_regions));

        profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

        profiler_finalise();

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        log_debug("Rewire tries = %d", count_rewire_attempts);
        simulation_ready_to_read();
        return;
    }

    // Do rewiring
    if (rewiring &&
            ((last_rewiring_time >= rewiring_period && !synaptogenesis_is_fast())
                || synaptogenesis_is_fast())) {
        last_rewiring_time = 0;
        // put flag in spike processing to do synaptic rewiring
        if (synaptogenesis_is_fast()) {
            spike_processing_do_rewiring(rewiring_period);
        } else {
            spike_processing_do_rewiring(1);
        }
        count_rewire_attempts++;
    }

    // Now do synapse and neuron time step updates
    synapses_do_timestep_update(time);
    neuron_do_timestep_update(time, timer_count, timer_period);

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);
}

//! \brief The entry point for this model.
void c_main(void) {

    // initialise the model
    if (!initialise()) {
        rt_error(RTE_API);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    log_debug("setting timer tick callback for %d microseconds",
              timer_period);
    spin1_set_timer_tick_and_phase(timer_period, timer_offset);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    simulation_run();
}
