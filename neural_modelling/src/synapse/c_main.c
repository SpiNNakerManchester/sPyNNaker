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

#include <common/in_spikes.h>
#include "neuron/regions.h"
#include "synapses.h"
#include "spike_processing.h"
#include "population_table/population_table.h"
#include "plasticity/synapse_dynamics.h"
#include "synapse/structural_plasticity/synaptogenesis_dynamics.h"
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

typedef enum extra_provenance_data_region_entries{
    NUMBER_OF_PRE_SYNAPTIC_EVENT_COUNT = 0,
    SYNAPTIC_WEIGHT_SATURATION_COUNT = 1,
    INPUT_BUFFER_OVERFLOW_COUNT = 2,
    CURRENT_TIMER_TICK = 3,
    PLASTIC_SYNAPTIC_WEIGHT_SATURATION_COUNT = 4
} extra_provenance_data_region_entries;

//! values for the priority for each callback
typedef enum callback_priorities{
    MC = -1, TIMER = 0, DMA = 0, USER = 0, SDP = 1
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

//! Timer callbacks since last rewiring
int32_t last_rewiring_time = 0;

//! Rewiring period represented as an integer
int32_t rewiring_period = 0;

//! Flag representing whether rewiring is enabled
bool rewiring = false;

// FOR DEBUGGING!
uint32_t count_rewires = 0;

//! Flag for synaptic contribution writing in SDRAM
//bool contribution_written;



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

    // store the data into the provenance data region
    provenance_region[NUMBER_OF_PRE_SYNAPTIC_EVENT_COUNT] =
        synapses_get_pre_synaptic_events();
    provenance_region[SYNAPTIC_WEIGHT_SATURATION_COUNT] =
        synapses_get_saturation_count();
    provenance_region[INPUT_BUFFER_OVERFLOW_COUNT] =
        spike_processing_get_buffer_overflows();
    provenance_region[CURRENT_TIMER_TICK] = time;
    provenance_region[PLASTIC_SYNAPTIC_WEIGHT_SATURATION_COUNT] =
            synapse_dynamics_get_plastic_saturation_count();
    log_debug("finished other provenance data");
}

void write_contributions(uint unused1, uint unused2) {

        use(unused1);
        use(unused2);

        uint32_t spikes_remaining = spike_processing_flush_in_buffer();

        //Start DMA Writing procedure for the contribution of this timestep
        synapses_do_timestep_update(time);
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
    address_t address = data_specification_get_data_address();
    // Read the header
    if (!data_specification_read_header(address)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM_REGION, address),
            APPLICATION_NAME_HASH, timer_period, &simulation_ticks,
            &infinite_run, SDP, DMA)) {
        return false;
    }
    simulation_set_provenance_function(
        c_main_store_provenance_data,
        data_specification_get_region(PROVENANCE_DATA_REGION, address));

    // setup recording region
    //if (!initialise_recording(
    //        data_specification_get_region(RECORDING_REGION, address))){
    //    return false;
    //}

    // Set up the synapses
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    address_t indirect_synapses_address = data_specification_get_region(
        SYNAPTIC_MATRIX_REGION, address);

    address_t direct_synapses_address;
    if (!synapses_initialise(
            data_specification_get_region(SYNAPSE_PARAMS_REGION, address),
            data_specification_get_region(DIRECT_MATRIX_REGION, address),
            &n_neurons, &n_synapse_types,
            &incoming_spike_buffer_size,
            &ring_buffer_to_input_buffer_left_shifts,
            &direct_synapses_address)) {
        return false;
    }

    // Set up the population table
    uint32_t row_max_n_words;
    if (!population_table_initialise(
            data_specification_get_region(POPULATION_TABLE_REGION, address),
            indirect_synapses_address, direct_synapses_address,
            &row_max_n_words)) {
        return false;
    }
    // Set up the synapse dynamics
    address_t synapse_dynamics_region_address =
        data_specification_get_region(SYNAPSE_DYNAMICS_REGION, address);
    address_t syn_dyn_end_address = synapse_dynamics_initialise(
            synapse_dynamics_region_address, n_neurons, n_synapse_types,
            ring_buffer_to_input_buffer_left_shifts);

    if (synapse_dynamics_region_address && !syn_dyn_end_address) {
        return false;
    }

    // Set up structural plasticity dynamics
    if (synapse_dynamics_region_address &&
        !synaptogenesis_dynamics_initialise(syn_dyn_end_address)){
        return false;
    }

    rewiring_period = get_p_rew();
    rewiring = rewiring_period != -1;

    if (!spike_processing_initialise(
            row_max_n_words, MC, USER,
            incoming_spike_buffer_size)) {
        return false;
    }

    //contribution_written = false;

    // Setup profiler
    profiler_init(
        data_specification_get_region(PROFILER_REGION, address));

    log_debug("Initialise: finished");

    // Register timer2 for periodic events
    event_register_timer(SLOT_8);

    return true;
}

void resume_callback() {

    //FILL THIS!!!!!

}

//! \brief Timer interrupt callback
//! \param[in] timer_count the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused unused parameter kept for API consistency
//! \return None
void timer_callback(uint timer_count, uint unused) {

    use(timer_count);
    use(unused);

    //Schedule event in 800 micro-sec from now
    if(!timer_schedule_proc(write_contributions, 0, 0, 800)) {

        rt_error(RTE_API);
    }

    time++;

    io_printf(IO_BUF, "Time %d\n", time);

    //If first timer tick retrieve the address of the buffer for synaptic contribution
    if(time == 0) {

        synapses_set_contribution_region();
    }
    else {

        //Flush the buffer containing the written contribution
        synapses_flush_ring_buffer(time-1);
    }

    if(infinite_run != TRUE && time >= simulation_ticks) {

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        log_debug("Completed a run");

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        simulation_ready_to_read();

        return;
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

    io_printf(IO_BUF, "Returned from initialise\n");

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
