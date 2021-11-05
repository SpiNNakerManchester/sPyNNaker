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
#include "regions.h"
#include "neuron.h"
#include "synapse/synapses.h"
#include "synapse/spike_processing.h"
#include "synapse/plasticity/synapse_dynamics.h"
#include "synapse/structural_plasticity/synaptogenesis_dynamics.h"
#include "profile_tags.h"
#include <round.h>

#include <data_specification.h>
#include <simulation.h>
#include <profiler.h>
#include <debug.h>

/* validates that the model being compiled does indeed contain a application
 * magic number*/
#ifndef APPLICATION_NAME_HASH
#define APPLICATION_NAME_HASH 0
#error APPLICATION_NAME_HASH was undefined.  Make sure you define this\
	constant
#endif

struct neuron_provenance {
    uint32_t current_timer_tick;
};

//! values for the priority for each callback
typedef enum callback_priorities {
    DMA = -1, USER = 1, SDP = 2, TIMER = 1
} callback_priorities;

//! The number of regions that are to be used for recording
#define NUMBER_OF_REGIONS_TO_RECORD 4

// Globals

//! the current timer tick value
//! the timer tick callback returning the same value.
uint32_t time;

static uint32_t timer_period;
static uint32_t timer_offset;

//! The number of timer ticks to run for before being expected to exit
static uint32_t simulation_ticks = 0;

//! Determines if this model should run for infinite time
static uint32_t infinite_run;

//! The recording flags
static uint32_t recording_flags = 0;

//! Timer callbacks since last rewiring
int32_t last_rewiring_time = 0;

//! Rewiring period represented as an integer
int32_t rewiring_period = 0;

//! Flag representing whether rewiring is enabled
bool rewiring = false;

// FOR DEBUGGING!
uint32_t count_rewires = 0;


//! \brief Initialises the recording parts of the model
//! \param[in] recording_address: the address in SDRAM where to store
//! recordings
//! \return True if recording initialisation is successful, false otherwise
static bool initialise_recording(address_t recording_address) {
    bool success = recording_initialize(recording_address, &recording_flags);
    log_debug("Recording flags = 0x%08x", recording_flags);
    return success;
}

void c_main_store_provenance_data(address_t provenance_region) {
    log_debug("writing other provenance data");
    struct neuron_provenance *prov = (void *) provenance_region;

    // store the data into the provenance data region
    prov->current_timer_tick = time;
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

    // setup recording region
    if (!initialise_recording(
            data_specification_get_region(RECORDING_REGION, ds_regions))) {
        return false;
    }

    if (!neuron_initialise(
            data_specification_get_region(NEURON_PARAMS_REGION, ds_regions),
            &timer_offset)) {
        return false;
    }

    rewiring_period = get_p_rew();
    rewiring = rewiring_period != -1;

    // Setup profiler
    profiler_init(data_specification_get_region(PROFILER_REGION, ds_regions));

    log_debug("Initialise: finished");
    return true;
}

//! \brief the function to call when resuming a simulation
//! \return None
void resume_callback(void) {
    recording_reset();

    // try reloading neuron parameters
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();
    if (!neuron_reload_neuron_parameters(
            data_specification_get_region(NEURON_PARAMS_REGION, ds_regions))) {
        log_error("failed to reload the neuron parameters.");
        rt_error(RTE_SWERR);
    }
}

//! \brief Timer interrupt callback
//! \param[in] timer_count the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused unused parameter kept for API consistency
//! \return None
void timer_callback(uint timer_count, uint unused) {
    use(unused);

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    time++;
    last_rewiring_time++;

    // This is the part where I save the input and output indices
    //   from the circular buffer
    // If time == 0 as well as output == input == 0  then no rewire is
    //   supposed to happen. No spikes yet
    //log_debug("Timer tick %u \n", time);

    /* if a fixed number of simulation ticks that were specified at startup
     * then do reporting for finishing */
    if (infinite_run != TRUE && time >= simulation_ticks) {
        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        log_debug("Completed a run");

        // rewrite neuron params to SDRAM for reading out if needed
        data_specification_metadata_t *ds_regions =
                data_specification_get_data_address();
        neuron_store_neuron_parameters(
                data_specification_get_region(NEURON_PARAMS_REGION, ds_regions));

        profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

        /* Finalise any recordings that are in progress, writing back the final
         * amounts of samples recorded to SDRAM */
        if (recording_flags > 0) {
            log_debug("updating recording regions");
            recording_finalise();
        }
        profiler_finalise();

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        log_debug("Rewire tries = %d", count_rewires);
        simulation_ready_to_read();
        return;
    }

    uint cpsr = 0;
    // Do rewiring
    if (rewiring &&
            ((last_rewiring_time >= rewiring_period && !is_fast()) || is_fast())) {
        update_goal_posts(time);
        last_rewiring_time = 0;
        // put flag in spike processing to do synaptic rewiring
#if 0
        synaptogenesis_dynamics_rewire(time);
#endif
        if (is_fast()) {
            do_rewiring(rewiring_period);
        } else {
            do_rewiring(1);
        }
        // disable interrupts
        cpsr = spin1_int_disable();
        /* If we're not already processing synaptic DMAs,
         * flag pipeline as busy and trigger a feed event */
        if (!get_dma_busy()) {
            log_debug("Sending user event for new spike");
            if (spin1_trigger_user_event(0, 0)) {
                set_dma_busy(true);
            } else {
                log_debug("Could not trigger user event\n");
            }
        }
        // enable interrupts
        spin1_mode_restore(cpsr);
        count_rewires++;
    }
    // otherwise do synapse and neuron time step updates

    //io_printf(IO_BUF, "\n\ntimestep %d\n", time);

    neuron_do_timestep_update(time, timer_count, timer_period);

    // trigger buffering_out_mechanism
    if (recording_flags > 0) {
        recording_do_timestep_update(time);
    }

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
    spin1_set_timer_tick(timer_period);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    simulation_run();
}
