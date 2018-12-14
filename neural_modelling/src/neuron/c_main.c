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
#include "regions.h"
#include "neuron.h"
#include "synapses.h"
#include "spike_processing.h"
#include "population_table/population_table.h"
#include "plasticity/synapse_dynamics.h"
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include "profile_tags.h"
#include "direct_synapses.h"

#include <data_specification.h>
#include <simulation.h>
#include <profiler.h>
#include <debug.h>
#include <bit_field.h>

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
    PLASTIC_SYNAPTIC_WEIGHT_SATURATION_COUNT = 4,
	GHOST_POP_TABLE_SEARCHES = 5,
	FAILED_TO_READ_BIT_FIELDS = 6,
	EMPTY_ROW_READS = 7,
	DMA_COMPLETES = 8,
	SPIKE_PROGRESSING_COUNT = 9
} extra_provenance_data_region_entries;

//! values for the priority for each callback
typedef enum callback_priorities{
    MC = -1, DMA = 0, USER = 0, SDP = 1, TIMER = 2
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

bit_field_t *connectivity_lookup;

// FOR DEBUGGING!
uint32_t count_rewires = 0;

//! the number of bit fields which were not able to be read in due to DTCM
//! limits
uint32_t failed_bit_field_reads = 0;


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
    provenance_region[GHOST_POP_TABLE_SEARCHES] =
    	spike_processing_get_ghost_pop_table_searches();
    provenance_region[FAILED_TO_READ_BIT_FIELDS] = failed_bit_field_reads;
    provenance_region[EMPTY_ROW_READS] = synapses_get_empty_row_count();
    provenance_region[DMA_COMPLETES] =
        spike_processing_get_dma_complete_count();
    provenance_region[SPIKE_PROGRESSING_COUNT] =
        spike_processing_get_spike_processing_count();
    log_debug("finished other provenance data");
}

static bool bit_field_filter_initialise(address_t bitfield_region){

    uint32_t position = 0;
    uint32_t n_bit_fields = bitfield_region[position];

    // try allocating dtcm for starting array for bitfields
    connectivity_lookup = spin1_malloc(sizeof(bit_field_t) * n_bit_fields);
    if (connectivity_lookup == NULL){
        log_warning(
            "couldn't  initialise basic bit field holder. Will end up doing "
            "possibly more DMA's during the execution than required");
        return true;
    }
    position += 1;

    // try allocating dtcm for each bit field
    for (uint32_t cur_bit_field = 0; cur_bit_field < n_bit_fields;
            cur_bit_field++){
        // get the key associated with this bitfield
        uint32_t key = bitfield_region[position];
        uint32_t n_words_for_bit_field = bitfield_region[position + 1];
        position += 2;

        // locate the position in the array to match the master pop element.
        int position_in_array =
            population_table_position_in_the_master_pop_array(key);

        // alloc sdram into right region
        connectivity_lookup[position_in_array] = spin1_malloc(
            sizeof(bit_field_t) * n_words_for_bit_field);
        if (connectivity_lookup[position_in_array] == NULL){
            log_warning(
                "could not initialise bit field for key %d, packets with"
                " that key will use a DMA to check if the packet targets "
                "anything within this core. Potentially slowing down the "
                "execution of neurons on this core.");
            failed_bit_field_reads ++;
        } else{  // read in bit field into correct location

            // read in the bits for the bitfield (think this avoids a for loop)
            spin1_memcpy(
                connectivity_lookup[position_in_array],
                &bitfield_region[position],
                sizeof(uint32_t) * n_words_for_bit_field);

            // print out the bit field for debug purposes
            log_debug("bit field for key %d is :", key);
            for (uint32_t bit_field_word_index = 0;
                    bit_field_word_index < n_words_for_bit_field;
                    bit_field_word_index++){
                log_debug("%x", connectivity_lookup[position_in_array]
                                                   [bit_field_word_index]);
            }
        }
        position += n_words_for_bit_field;
    }
    population_table_set_connectivity_lookup(connectivity_lookup);
    return true;
}

//! \brief Initialises the model by reading in the regions and checking
//!        recording data.
//! \param[in] timer_period a pointer for the memory address where the timer
//!            period should be stored during the function.
//! \return True if it successfully initialised, false otherwise
static bool initialise(uint32_t *timer_period) {
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
    if (!initialise_recording(
            data_specification_get_region(RECORDING_REGION, address))){
        return false;
    }

    // Set up the neurons
    uint32_t n_neurons;
    uint32_t n_synapse_types;
    uint32_t incoming_spike_buffer_size;
    if (!neuron_initialise(
            data_specification_get_region(NEURON_PARAMS_REGION, address),
            &n_neurons, &n_synapse_types, &incoming_spike_buffer_size)) {
        return false;
    }

    // Set up the synapses
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    if (!synapses_initialise(
            data_specification_get_region(SYNAPSE_PARAMS_REGION, address),
            n_neurons, n_synapse_types,
            &ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    // set up direct synapses
    address_t direct_synapses_address;
    if (!direct_synapses_initialise(
            data_specification_get_region(DIRECT_MATRIX_REGION, address),
            &direct_synapses_address)){
        return false;
    }

    // Set up the population table
    uint32_t row_max_n_words;
    if (!population_table_initialise(
            data_specification_get_region(POPULATION_TABLE_REGION, address),
            data_specification_get_region(SYNAPTIC_MATRIX_REGION, address),
            direct_synapses_address, &row_max_n_words)) {
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

    // Setup profiler
    profiler_init(
        data_specification_get_region(PROFILER_REGION, address));

    log_info("initialising the bit field region");
    if (!bit_field_filter_initialise(
            data_specification_get_region(BIT_FIELD_FILTER_REGION, address))){
        return false;
    }

    log_debug("Initialise: finished");
    return true;
}

//! \brief the function to call when resuming a simulation
//! \return None
void resume_callback() {
    recording_reset();

    // try reloading neuron parameters
    address_t address = data_specification_get_data_address();
    if (!neuron_reload_neuron_parameters(
            data_specification_get_region(
                NEURON_PARAMS_REGION, address))) {
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

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    time++;
    last_rewiring_time++;

    // This is the part where I save the input and output indices
    //   from the circular buffer
    // If time == 0 as well as output == input == 0  then no rewire is
    //   supposed to happen. No spikes yet
    log_debug("Timer tick %u \n", time);

    /* if a fixed number of simulation ticks that were specified at startup
       then do reporting for finishing */
    if (infinite_run != TRUE && time >= simulation_ticks) {

        // Enter pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        log_debug("Completed a run");

        // rewrite neuron params to SDRAM for reading out if needed
        address_t address = data_specification_get_data_address();
        neuron_store_neuron_parameters(
            data_specification_get_region(NEURON_PARAMS_REGION, address));

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
        time -= 1;

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
//        synaptogenesis_dynamics_rewire(time);
        if (is_fast()) {
            do_rewiring(rewiring_period);
        } else {
            do_rewiring(1);
        }
        // disable interrupts
        cpsr = spin1_int_disable();
//       // If we're not already processing synaptic DMAs,
//        // flag pipeline as busy and trigger a feed event
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
    synapses_do_timestep_update(time);
    neuron_do_timestep_update(time);

    // trigger buffering_out_mechanism
    if (recording_flags > 0) {
        recording_do_timestep_update(time);
    }

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);
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
    log_debug("setting timer tick callback for %d microseconds",
              timer_period);
    spin1_set_timer_tick(timer_period);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    simulation_run();
}
