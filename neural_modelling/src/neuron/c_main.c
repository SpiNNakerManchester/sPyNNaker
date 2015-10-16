/*!\file
 *
 * SUMMARY
 *  \brief This file contains the main function of the application framework,
 *  which the application programmer uses to configure and run applications.
 *
 *
 * This is the main entrance class for most of the neural models. The following
 * Figure shows how all of the c code interacts with each other and what classes
 * are used to represent over arching logic
 * (such as plasticity, spike processing, utilities, synapse types, models)
 *
 * @image html spynnaker_c_code_flow.png
 *
 */

#include "../common/in_spikes.h"
#include "neuron.h"
#include "synapses.h"
#include "spike_processing.h"
#include "population_table.h"
#include "plasticity/synapse_dynamics.h"

#include <data_specification.h>
#include <region_defs.h>
#include <simulation.h>
#include <debug.h>

/* validates that the model being compiled does indeed contain a application
   magic number*/
#ifndef APPLICATION_NAME_HASH
#error APPLICATION_NAME_HASH was undefined.  Make sure you define this\
       constant
#endif

//! the number of channels all standard models contain (spikes, voltage, gsyn)
//! for recording
#define N_RECORDING_CHANNELS 3



// Globals

//! the current timer tick value TODO this might be able to be removed with
//! the timer tick callback returning the same value.
uint32_t time;
//! global parameter which contains the number of timer ticks to run for before
//! being expected to exit
static uint32_t simulation_ticks = 0;
//! global paramter which states if this model should run for infinite time
static uint32_t infinite_run;

//! \Initialises the model by reading in the regions and checking recording
//! data.
//! \param[in] *timer_period a pointer for the memory address where the timer
//! period should be stored during the function.
//! \return boolean of True if it successfully read all the regions and set up
//! all its internal data structures. Otherwise returns False
static bool initialize(uint32_t *timer_period) {
    log_info("Initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(address)) {
        return false;
    }

    // Get the timing details
    address_t system_region = data_specification_get_region(
        SYSTEM_REGION, address);
    if (!simulation_read_timing_details(
            system_region, APPLICATION_NAME_HASH, timer_period,
            &simulation_ticks, &infinite_run)) {
        return false;
    }

    // Set up recording
    recording_channel_e channels_to_record[] = {
        e_recording_channel_spike_history,
        e_recording_channel_neuron_potential,
        e_recording_channel_neuron_gsyn
    };
    regions_e regions_to_record[] = {
        BUFFERING_OUT_SPIKE_RECORDING_REGION,
        BUFFERING_OUT_POTENTIAL_RECORDING_REGION,
        BUFFERING_OUT_GSYN_RECORDING_REGION
    };
    uint32_t region_sizes[N_RECORDING_CHANNELS];
    uint32_t recording_flags;
    recording_read_region_sizes(
        &system_region[SIMULATION_N_TIMING_DETAIL_WORDS],
        &recording_flags, &region_sizes[0], &region_sizes[1], &region_sizes[2]);
    for (uint32_t i = 0; i < N_RECORDING_CHANNELS; i++) {
        if (recording_is_channel_enabled(recording_flags,
                                         channels_to_record[i])) {
            if (!recording_initialise_channel(
                    data_specification_get_region(regions_to_record[i],
                                                  address),
                    channels_to_record[i], region_sizes[i])) {
                return false;
            }
        }
    }

    // Set up the neurons
    uint32_t n_neurons;
    if (!neuron_initialise(
            data_specification_get_region(NEURON_PARAMS_REGION, address),
            recording_flags, &n_neurons)) {
        return false;
    }

    // Set up the synapses
    input_t *input_buffers;
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    if (!synapses_initialise(
            data_specification_get_region(SYNAPSE_PARAMS_REGION, address),
            n_neurons, &input_buffers,
            &ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }
    neuron_set_input_buffers(input_buffers);

    // Set up the population table
    uint32_t row_max_n_words;
    if (!population_table_initialise(
            data_specification_get_region(POPULATION_TABLE_REGION, address),
            data_specification_get_region(SYNAPTIC_MATRIX_REGION, address),
            &row_max_n_words)) {
        return false;
    }

    // Set up the synapse dynamics
    if (!synapse_dynamics_initialise(
            data_specification_get_region(SYNAPSE_DYNAMICS_REGION, address),
            n_neurons, ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    if (!spike_processing_initialise(row_max_n_words)) {
        return false;
    }
    log_info("Initialise: finished");
    return true;
}

//! \The callback used when a timer tic interrupt is set off. The result of
//! this is to transmit any spikes that need to be sent at this timer tic,
//! update any recording, and update the state machine's states.
//! If the timer tic is set to the end time, this method will call the
//! spin1api stop command to allow clean exit of the executable.
//! \param[in] timer_count the number of times this call back has been
//! executed since start of simulation
//! \param[in] unused for consistency sake of the API always returning two
//! parameters, this parameter has no semantics currently and thus is set to 0
//! \return None
void timer_callback(uint timer_count, uint unused) {
    use(timer_count);
    use(unused);

    time++;

    log_debug("Timer tick %u \n", time);

    /* if a fixed number of simulation ticks that were specified at startup
       then do reporting for finishing */
    if (infinite_run != TRUE && time >= simulation_ticks) {
        log_info("Simulation complete.\n");

        // print statistics into logging region
        synapses_print_pre_synaptic_events();
        synapses_print_saturation_count();

        spike_processing_print_buffer_overflows();

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        recording_finalise();

        spin1_exit(0);
        return;
    }
    // otherwise do synapse and neuron time step updates
    synapses_do_timestep_update(time);
    neuron_do_timestep_update(time);
}

//! \The only entry point for this model. it initialises the model, sets up the
//! Interrupts for the Timer tic and calls the spin1api for running.
void c_main(void) {

    // Load DTCM data
    uint32_t timer_period;

    // initialise the model
    if (!initialize(&timer_period)){
        rt_error(RTE_API);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    log_info("setting timer tic callback for %d microseconds",
              timer_period);
    spin1_set_timer_tick(timer_period);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, 2);

    log_info("Starting");
    simulation_run();
}
