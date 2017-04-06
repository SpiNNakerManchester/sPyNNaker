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

// sPyNNaker class definitions
#include "synapse_type.h"

#include "common/in_spikes.h"
#include "neuron/neuron.h"
#include "neuron/synapses.h"
#include "neuron/spike_processing.h"
#include "neuron/population_table/population_table.h"
#include "neuron/plasticity/synapse_dynamics.h"

#include <data_specification.h>
#include <simulation.h>
#include <debug.h>

/* validates that the model being compiled does indeed contain a application
   magic number*/
#ifndef APPLICATION_NAME_HASH
#define APPLICATION_NAME_HASH 0
#error APPLICATION_NAME_HASH was undefined.  Make sure you define this\
       constant
#endif

//! human readable definitions of each region in SDRAM
typedef enum regions_e{
    SYSTEM_REGION,
    NEURON_PARAMS_REGION,
    SYNAPSE_PARAMS_REGION,
    POPULATION_TABLE_REGION,
    SYNAPTIC_MATRIX_REGION,
    SYNAPSE_DYNAMICS_REGION,
    RECORDING_REGION,
    PROVENANCE_DATA_REGION
} regions_e;

typedef enum extra_provenance_data_region_entries{
    NUMBER_OF_PRE_SYNAPTIC_EVENT_COUNT = 0,
    SYNAPTIC_WEIGHT_SATURATION_COUNT = 1,
    INPUT_BUFFER_OVERFLOW_COUNT = 2,
    CURRENT_TIMER_TICK = 3,
} extra_provenance_data_region_entries;

//! values for the priority for each callback
typedef enum callback_priorities{
    MC = -1, SDP_AND_DMA_AND_USER = 0, TIMER_AND_BUFFERING = 2
} callback_priorities;

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
//! \param[in] recording_address: the address in sdram where to store
//! recordings
//! \return True if recording initialisation is successful, false otherwise
static bool initialise_recording(address_t recording_address){
    bool success = recording_initialize(recording_address, &recording_flags);
    log_info("Recording flags = 0x%08x", recording_flags);
    return success;
}

void c_main_store_provenance_data(address_t provenance_region){
    log_debug("writing other provenance data");

    // store the data into the provenance data region
    provenance_region[NUMBER_OF_PRE_SYNAPTIC_EVENT_COUNT] =
        synapses_get_pre_synaptic_events();
    provenance_region[SYNAPTIC_WEIGHT_SATURATION_COUNT] =
        synapses_get_saturation_count();
    provenance_region[INPUT_BUFFER_OVERFLOW_COUNT] =
        spike_processing_get_buffer_overflows();
    provenance_region[CURRENT_TIMER_TICK] = time;
    log_debug("finished other provenance data");
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

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM_REGION, address),
            APPLICATION_NAME_HASH, timer_period, &simulation_ticks,
            &infinite_run, SDP_AND_DMA_AND_USER, c_main_store_provenance_data,
            data_specification_get_region(PROVENANCE_DATA_REGION, address))) {
        return false;
    }

    // setup recording region
    if (!initialise_recording(
            data_specification_get_region(RECORDING_REGION, address))){
        return false;
    }

    // Set up the neurons
    uint32_t n_neurons;
    uint32_t incoming_spike_buffer_size;
    if (!neuron_initialise(
            data_specification_get_region(NEURON_PARAMS_REGION, address),
            recording_flags, &n_neurons, &incoming_spike_buffer_size)) {
        return false;
    }

    // Set up the synapses
    input_t *input_buffers;
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    address_t indirect_synapses_address;
    address_t direct_synapses_address;
    if (!synapses_initialise(
            data_specification_get_region(SYNAPSE_PARAMS_REGION, address),
            data_specification_get_region(SYNAPTIC_MATRIX_REGION, address),
            n_neurons, &input_buffers,
            &ring_buffer_to_input_buffer_left_shifts,
            &indirect_synapses_address, &direct_synapses_address)) {
        return false;
    }
    neuron_set_input_buffers(input_buffers);

    // Set up the population table
    uint32_t row_max_n_words;
    if (!population_table_initialise(
            data_specification_get_region(POPULATION_TABLE_REGION, address),
            indirect_synapses_address, direct_synapses_address,
            &row_max_n_words)) {
        return false;
    }

    // Set up the synapse dynamics
    if (!synapse_dynamics_initialise(
            data_specification_get_region(SYNAPSE_DYNAMICS_REGION, address),
            n_neurons, ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    if (!spike_processing_initialise(
            row_max_n_words, MC, SDP_AND_DMA_AND_USER, SDP_AND_DMA_AND_USER,
            incoming_spike_buffer_size)) {
        return false;
    }
    log_info("Initialise: finished");
    return true;
}

//! \brief the function to call when resuming a simulation
//! return None
void resume_callback() {
    recording_reset();

    // try reloading neuron parameters
    address_t address = data_specification_get_data_address();
    if(!neuron_reload_neuron_parameters(
            data_specification_get_region(
                NEURON_PARAMS_REGION, address))){
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
    use(timer_count);
    use(unused);

    time++;

    log_debug("Timer tick %u \n", time);

    /* if a fixed number of simulation ticks that were specified at startup
       then do reporting for finishing */
    if (infinite_run != TRUE && time >= simulation_ticks) {

        log_info("Completed a run");

        // rewrite neuron params to sdram for reading out if needed
        address_t address = data_specification_get_data_address();
        neuron_store_neuron_parameters(
            data_specification_get_region(NEURON_PARAMS_REGION, address));

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        if (recording_flags > 0) {
            log_info("updating recording regions");
            recording_finalise();
        }

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time -= 1;
        return;
    }

    // otherwise do synapse and neuron time step updates
    synapses_do_timestep_update(time);
    neuron_do_timestep_update(time);

    // trigger buffering_out_mechanism
    if (recording_flags > 0) {
        recording_do_timestep_update(time);
    }
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
    log_info("setting timer tick callback for %d microseconds",
              timer_period);
    spin1_set_timer_tick(timer_period);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER_AND_BUFFERING);

    simulation_run();
}
