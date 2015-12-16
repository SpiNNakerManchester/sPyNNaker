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
#include <simulation.h>
#include <debug.h>

/* validates that the model being compiled does indeed contain a application
   magic number*/
#ifndef APPLICATION_NAME_HASH
#error APPLICATION_NAME_HASH was undefined.  Make sure you define this\
       constant
#endif

//! human readable definitions of each region in SDRAM
typedef enum regions_e {
    SYSTEM_REGION,
    NEURON_PARAMS_REGION,
    SYNAPSE_PARAMS_REGION,
    POPULATION_TABLE_REGION,
    SYNAPTIC_MATRIX_REGION,
    SYNAPSE_DYNAMICS_REGION,
    BUFFERING_OUT_SPIKE_RECORDING_REGION,
    BUFFERING_OUT_POTENTIAL_RECORDING_REGION,
    BUFFERING_OUT_GSYN_RECORDING_REGION,
    BUFFERING_OUT_CONTROL_REGION
} regions_e;

//! values for the priority for each callback
typedef enum callback_priorities{
    MC = -1, SDP_AND_DMA_AND_USER = 0, TIMER = 2
}callback_priorities;

//! The number of regions that are to be used for recording
#define NUMBER_OF_REGIONS_TO_RECORD 3

// Globals

//! the current timer tick value TODO this might be able to be removed with
//! the timer tick callback returning the same value.
uint32_t time;

//! The number of timer ticks to run for before being expected to exit
static uint32_t simulation_ticks = 0;

//! Determines if this model should run for infinite time
static uint32_t infinite_run;

//! The recording flags
static uint32_t recording_flags = 0;

//! \brief Initialises the recording parts of the model
//! \return True if recording initisation is successful, false otherwise
static bool initialise_recording(){
    address_t address = data_specification_get_data_address();
    address_t system_region = data_specification_get_region(
        SYSTEM_REGION, address);
    regions_e regions_to_record[] = {
        BUFFERING_OUT_SPIKE_RECORDING_REGION,
        BUFFERING_OUT_POTENTIAL_RECORDING_REGION,
        BUFFERING_OUT_GSYN_RECORDING_REGION
    };
    uint8_t n_regions_to_record = NUMBER_OF_REGIONS_TO_RECORD;
    uint32_t *recording_flags_from_system_conf =
        &system_region[SIMULATION_N_TIMING_DETAIL_WORDS];
    regions_e state_region = BUFFERING_OUT_CONTROL_REGION;

    bool success = recording_initialize(
        n_regions_to_record, regions_to_record,
        recording_flags_from_system_conf, state_region, 2, &recording_flags);
    log_info("Recording flags = 0x%08x", recording_flags);
    return success;
}

//! \brief Initialises the model by reading in the regions and checking
//!        recording data.
//! \param[in] timer_period a pointer for the memory address where the timer
//!            period should be stored during the function.
//! \return True if it successfully initialised, false otherwise
static bool initialise(uint32_t *timer_period) {
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

    // setup recording region
    if (!initialise_recording()){
        return false;
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

    if (!spike_processing_initialise(row_max_n_words, MC, SDP_AND_DMA_AND_USER,
                                     SDP_AND_DMA_AND_USER)) {
        return false;
    }
    log_info("Initialise: finished");
    return true;
}

//! \brief Timer interrupt callback
//! \param[in] timer_count the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused unused parameter kept for API consistency
//! \return None
void timer_callback(uint timer_count, uint unused) {
    use(timer_count);
    use(unused);

    time++;

    log_debug("Timer tick %u \n", time);

    /* if a fixed number of simulation ticks that were specified at startup
       then do reporting for finishing */
    if (infinite_run != TRUE && time >= simulation_ticks) {
        // print statistics into logging region
        synapses_print_pre_synaptic_events();
        synapses_print_saturation_count();

        spike_processing_print_buffer_overflows();

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        if (recording_flags > 0) {
            recording_finalise();
        }

        // falls into the apuse resume mode of operating
        simulation_handle_pause_resume(timer_callback, TIMER);

        // restart the recording status
        if (!initialise_recording()) {
            log_error("I couldnt resetup recording");
            spin1_exit(0);
        }
    }
    // otherwise do synapse and neuron time step updates
    synapses_do_timestep_update(time);
    neuron_do_timestep_update(time);

    // trigger buffering_out_mechanism
    if (recording_flags > 0) {
        recording_do_timestep_update(time);
    }
}

void reload_parameters() {
    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    neuron_reload(data_specification_get_region(NEURON_PARAMS_REGION, address));
}

//! \brief The entry point for this model.
void c_main(void) {

    // Load DTCM data
    uint32_t timer_period;

    // initialise the model
    if (!initialise(&timer_period)){
        rt_error(RTE_API);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    log_info("setting timer tic callback for %d microseconds",
              timer_period);
    spin1_set_timer_tick(timer_period);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    // Set up callback listening to SDP messages
    simulation_register_simulation_sdp_callback(&simulation_ticks, 
                                                reload_parameters,
                                                SDP_AND_DMA_AND_USER);

    log_info("Starting");
    simulation_run();
}
