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


/*!\file
 *
 * SUMMARY
 *  \brief This file contains the main function of the application framework,
 *  which the application programmer uses to configure and run applications.
 *
 *
 * This is the main entrance class for most of the neural models. The following
 * Figure shows how all of the c code
 * interacts with each other and what classes
 * are used to represent over arching logic
 * (such as plasticity, spike processing, utilities, synapse types, models)
 *
 * @image html spynnaker_c_code_flow.png
 *
 */

#include <common/in_rates.h>
#include "neuron/regions.h"
#include "synapses.h"
#include "spike_processing.h"
#include "population_table/population_table.h"
#include "plasticity/synapse_dynamics.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include "neuron/profile_tags.h"

#include <data_specification.h>
#include <simulation.h>
#include <profiler.h>
#include <debug.h>

/* validates that the model being compiled does indeed contain a application
   magic number*/
#ifndef APPLICATION_NAME_HASH
#define APPLICATION_NAME_HASH 0
#error APPLICATION_NAME_HASH was undefined.  Make sure you define this\
       constant
#endif

struct synapse_provenance {
    uint32_t n_pre_synaptic_events;
    uint32_t n_synaptic_weight_saturations;
    uint32_t n_input_buffer_overflows;
    uint32_t current_timer_tick;
    uint32_t n_plastic_synaptic_weight_saturations;
    uint32_t flushed_spikes;
    uint32_t max_flushed_spikes;
    uint32_t max_time;
    uint32_t cb_calls;
    uint32_t read_cb_calls;
};

//! values for the priority for each callback
typedef enum callback_priorities{
    MC = -1, TIMER = 0, DMA = 0, USER = 0, SDP = 2 //User was 1 for US
} callback_priorities;

//! The number of regions that are to be used for recording
#define NUMBER_OF_REGIONS_TO_RECORD 4

// Globals

//! the current timer tick value
//! the timer tick callback returning the same value.
uint32_t time;

//! The number of timer ticks to run for before being expected to exit
static uint32_t simulation_ticks = 0;

//! Determines if this model should run for infinite time
static uint32_t infinite_run;

//! The recording flags
static uint32_t recording_flags = 0;

// Load DTCM data
static uint32_t timer_period;

// FOR DEBUGGING!
uint32_t count_rewires = 0;

static uint32_t max_spikes_remaining = 0;
static uint32_t spikes_remaining = 0;
uint32_t spikes_remaining_this_tick = 0;
static uint32_t max_time = UINT32_MAX;
static uint32_t cb_calls = 0;
static bool has_plastic_synapses = false;

//! \brief Initialises the recording parts of the model
//! \param[in] recording_address: the address in SDRAM where to store
//! recordings
//! \return True if recording initialisation is successful, false otherwise
static bool initialise_recording(address_t recording_address){
    bool success = recording_initialize(recording_address, &recording_flags);
    log_debug("Recording flags = 0x%08x", recording_flags);
    return success;
}

void c_main_store_provenance_data(address_t provenance_region){
    log_debug("writing other provenance data");

    struct synapse_provenance *prov = (void *) provenance_region;

    // store the data into the provenance data region
    prov->n_pre_synaptic_events = synapses_get_pre_synaptic_events();
    prov->n_synaptic_weight_saturations = synapses_get_saturation_count();
    prov->n_input_buffer_overflows = spike_processing_get_buffer_overflows();
    prov->current_timer_tick = time;
    prov->n_plastic_synaptic_weight_saturations =
            synapse_dynamics_get_plastic_saturation_count();
    prov->flushed_spikes = spikes_remaining;
    prov->max_flushed_spikes = max_spikes_remaining;
    prov->max_time = max_time;
    prov->cb_calls = cb_calls;
    prov->read_cb_calls = spike_processing_read_cb_calls();
    log_debug("finished other provenance data");
}

//! \brief Callback used to write the synaptic contributions for the neuron core
//! \param[in] unused1 unused parameter kept for API consistency
//! \param[in] unused2 unused parameter kept for API consistency
//! \return None
void write_contributions(uint unused1, uint unused2) {

        use(unused1);
        use(unused2);

        uint32_t state = spin1_int_disable();

        cb_calls++;

        //Start DMA Writing procedure for the contribution of this timestep
        synapses_do_timestep_update(time);

        // Set DMA busy true for plastic synapses to force the post_buffer download
        // before the spike processing
        set_dma_busy(has_plastic_synapses);

        spikes_remaining_this_tick = spike_processing_flush_in_buffer();
        spikes_remaining += spikes_remaining_this_tick;

        if(spikes_remaining_this_tick > max_spikes_remaining) {
            max_spikes_remaining = spikes_remaining_this_tick;
            max_time = time;
        }

        spin1_mode_restore(state);
}

//! \brief Callback used to read the postsynaptic buffer from the neuron core
//!        for plastic synapses
//! \param[in] unused1 unused parameter kept for API consistency
//! \param[in] unused2 unused parameter kept for API consistency
//! \return None
void read_contributions(uint unused1, uint unused2) {

    use(unused1);
    use(unused2);

    synapse_dynamics_read_post_buffer();
}

//! \brief Initialises the model by reading in the regions and checking
//!        recording data.
//! \param[in] timer_period a pointer for the memory address where the timer
//!            period should be stored during the function.
//! \return True if it successfully initialised, false otherwise
static bool initialise(uint32_t *timer_period) {

    uint32_t n_neurons;
    uint32_t n_synapse_types;
    uint32_t incoming_spike_buffer_size;

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
            APPLICATION_NAME_HASH, timer_period, &simulation_ticks,
            &infinite_run, &time, SDP, DMA)) {
        return false;
    }
    simulation_set_provenance_function(
        c_main_store_provenance_data,
        data_specification_get_region(PROVENANCE_DATA_REGION, ds_regions));

    if(!initialise_recording(
           data_specification_get_region(RECORDING_REGION, ds_regions))) {
        return false;
    }

    // Set up the synapses
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    address_t indirect_synapses_address = data_specification_get_region(
        SYNAPTIC_MATRIX_REGION, ds_regions);

    address_t direct_synapses_address;

    if (!synapses_initialise(
            data_specification_get_region(SYNAPSE_PARAMS_REGION, ds_regions),
            data_specification_get_region(DIRECT_MATRIX_REGION, ds_regions),
            &n_neurons, &n_synapse_types,
            &incoming_spike_buffer_size,
            &ring_buffer_to_input_buffer_left_shifts,
            &direct_synapses_address)) {
        return false;
    }

    // Set up the population table
    uint32_t row_max_n_words;
    if (!population_table_initialise(
            data_specification_get_region(POPULATION_TABLE_REGION, ds_regions),
            indirect_synapses_address, direct_synapses_address,
            &row_max_n_words)) {
        return false;
    }

    // Set up the synapse dynamics
    address_t synapse_dynamics_region_address =
        data_specification_get_region(SYNAPSE_DYNAMICS_REGION, ds_regions);
    address_t syn_dyn_end_address = synapse_dynamics_initialise(
            synapse_dynamics_region_address, n_neurons, n_synapse_types,
            ring_buffer_to_input_buffer_left_shifts, &has_plastic_synapses);

    if (synapse_dynamics_region_address && !syn_dyn_end_address) {
        return false;
    }

    // Set up structural plasticity dynamics
    if (synapse_dynamics_region_address &&
        !synaptogenesis_dynamics_initialise(syn_dyn_end_address)){
        return false;
    }

    if (!spike_processing_initialise(
            row_max_n_words, MC, USER, 
            incoming_spike_buffer_size,
            has_plastic_synapses)) {
        return false;
    }

    // Setup profiler
    profiler_init(
        data_specification_get_region(PROFILER_REGION, ds_regions));

    log_debug("Initialise: finished");

    // Register timer2 for periodic events(used to write contributions in SDRAM)
    tc[T2_INT_CLR] = 1; // clear any interrupts on T2
    event_register_timer(SLOT_9);

//    io_printf(IO_BUF, "timer period: %u\n", *timer_period);

    return true;
}

void resume_callback() {

}

//! \brief Timer interrupt callback
//! \param[in] timer_count the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused unused parameter kept for API consistency
//! \return None
void timer_callback(uint timer_count, uint unused) {

//	io_printf(IO_BUF, "t_c s: %u, %u\n", tc[T1_COUNT], tc[T2_COUNT]);
//	io_printf(IO_BUF, "t_c s: %u\n", timer_period-40);

    use(timer_count);
    use(unused);

//    if(!timer_schedule_proc(write_contributions, 0, 0, timer_period-40)) {
//
//        rt_error(RTE_API);
//    }

//    Sould this be done in a safer way?
    uint32_t state = spin1_int_disable();
    
    // 40 for test purposes, to add prints. It was 10 before
    uint32_t wc_reg = tc[T1_COUNT] * 0.005 - 40;
    // Overallocate 60 microseconds from the beginning of the timestep
    // Max time required with 8 neurons and 14 partitions was 52 microseconds
    uint32_t rc_reg = 60;

    //Schedule event for post buffer read
    if(has_plastic_synapses) {
        
        if(!timer_schedule_proc(read_contributions, 0, 0, rc_reg)) {

            rt_error(RTE_API);
        }
    }

    //Schedule event 10 microseconds before the end of the timer period
    if(!timer_schedule_proc(write_contributions, 0, 0, wc_reg)) {

    	rt_error(RTE_API);
    }
    spin1_mode_restore(state);

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    time++;

    log_debug("Timer tick %u \n", time);

    //Flush the buffer containing the written contribution
    synapses_flush_ring_buffer(time);

    if(infinite_run != TRUE && time >= simulation_ticks) {

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        log_debug("Completed a run");

        profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        if (recording_flags > 0) {
            log_debug("updating recording regions");
            recording_finalise();
        }

        profiler_finalise();

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        simulation_ready_to_read();

        return;
    }

    // trigger buffering_out_mechanism
    if (recording_flags > 0) {
        recording_do_timestep_update(time);
    }

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);
}

//! \brief The entry point for this model.
void c_main(void) {

    // initialise the model
    if (!initialise(&timer_period)){
        rt_error(RTE_API);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    log_debug("setting timer tick callback for %d microseconds",
              timer_period);
    spin1_set_timer_tick(timer_period);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);
    //SPIKE PROCESSING PIPELINE CALLBACKS ARE MANAGED IN spike_processing.c

    simulation_run();
}