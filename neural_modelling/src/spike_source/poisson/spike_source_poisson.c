/*! \file
 *
 *  \brief This file contains the main functions for a poisson spike generator.
 *
 *
 */

#include "../../common/out_spikes.h"
#include "../../common/maths-util.h"

#include <data_specification.h>
#include <recording.h>
#include <debug.h>
#include <random.h>
#include <simulation.h>
#include <spin1_api.h>
#include <string.h>

//! data structure for poisson sources
typedef struct spike_source_t {
    uint32_t start_ticks;
    uint32_t end_ticks;
    bool is_fast_source;

    UFRACT exp_minus_lambda;
    REAL mean_isi_ticks;
    REAL time_to_spike_ticks;
} spike_source_t;

//! spike source array region ids in human readable form
typedef enum region {
    SYSTEM, POISSON_PARAMS,
    SPIKE_HISTORY_REGION,
    PROVENANCE_REGION
} region;

#define NUMBER_OF_REGIONS_TO_RECORD 1

typedef enum callback_priorities{
    SDP = 0, TIMER = 2
} callback_priorities;

//! what each position in the poisson parameter region actually represent in
//! terms of data (each is a word)
typedef enum poisson_region_parameters_before_seed{
    HAS_KEY, TRANSMISSION_KEY, RANDOM_BACKOFF, PARAMETER_SEED_START_POSITION
} poisson_region_parameters_before_seed;

// Globals
//! global variable which contains all the data for neurons
static spike_source_t *spike_source_array = NULL;


//! counter for how many neurons exhibit slow spike generation
static uint32_t num_spike_sources = 0;

//! a variable that will contain the seed to initiate the poisson generator.
static mars_kiss64_seed_t spike_source_seed;

//! a variable which checks if there has been a key allocated to this spike
//! source Poisson
static bool has_been_given_key;

//! A variable that contains the key value that this model should transmit with
static uint32_t key;

//! An amount of microseconds to back off before starting the timer, in an
//! attempt to avoid overloading the network
static uint32_t random_backoff_us;

//! keeps track of which types of recording should be done to this model.
static uint32_t recording_flags = 0;

//! the time interval parameter TODO this variable could be removed and use the
//! timer tick callback timer value.
static uint32_t time;

//! the number of timer ticks that this model should run for before exiting.
static uint32_t simulation_ticks = 0;

//! the int that represents the bool for if the run is infinite or not.
static uint32_t infinite_run;

//! the number of ticks per second
static REAL ticks_per_second;

//! the number of seconds per tick
static UFRACT seconds_per_tick;

//! the rate per tick below which a source is considered slow
static REAL slow_rate_per_tick_cutoff;

//! \brief deduces the time in timer ticks until the next spike is to occur
//!        given the mean inter-spike interval
//! \param[in] mean_inter_spike_interval_in_ticks The mean number of ticks
//!            before a spike is expected to occur in a slow process.
//! \return a real which represents time in timer ticks until the next spike is
//!         to occur
static inline REAL slow_spike_source_get_time_to_spike(
        REAL mean_inter_spike_interval_in_ticks) {
    return exponential_dist_variate(mars_kiss64_seed, spike_source_seed)
            * mean_inter_spike_interval_in_ticks;
}

//! \brief Determines how many spikes to transmit this timer tick.
//! \param[in] exp_minus_lambda The amount of spikes expected to be produced
//!            this timer interval (timer tick in real time)
//! \return a uint32_t which represents the number of spikes to transmit
//!         this timer tick
static inline uint32_t fast_spike_source_get_num_spikes(
        UFRACT exp_minus_lambda) {
    if (bitsulr(exp_minus_lambda) == bitsulr(UFRACT_CONST(0.0))) {
        return 0;
    }
    else {
        return poisson_dist_variate_exp_minus_lambda(
            mars_kiss64_seed, spike_source_seed, exp_minus_lambda);
    }
}

void print_spike_sources(){
    if (num_spike_sources > 0) {
        for (index_t s = 0; s < num_spike_sources; s++) {
            log_info("atom %d", s);
            log_info("scaled_start = %d", spike_source_array[s].start_ticks);
            log_info("scaled end = %d", spike_source_array[s].end_ticks);
            log_info("is_fast_source = %b", spike_source_array[s].is_fast_source);
            log_info("exp_minus_lamda = %f", spike_source_array[s].exp_minus_lambda);
            log_info("isi_val = %f", spike_source_array[s].mean_isi_ticks);
            log_info("time_to_spike = %f", spike_source_array[s].time_to_spike_ticks);
        }
    }

}

//! \entry method for reading the parameters stored in Poisson parameter region
//! \param[in] address the absolute SDRAm memory address to which the
//!            Poisson parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
bool read_poisson_parameters(address_t address) {

    log_info("read_parameters: starting");

    has_been_given_key = address[HAS_KEY];
    key = address[TRANSMISSION_KEY];
    random_backoff_us = address[RANDOM_BACKOFF];
    log_info("\t key = %08x, back off = %u", key, random_backoff_us);

    uint32_t seed_size = sizeof(mars_kiss64_seed_t) / sizeof(uint32_t);
    memcpy(spike_source_seed, &address[PARAMETER_SEED_START_POSITION],
        seed_size * sizeof(uint32_t));
    validate_mars_kiss64_seed(spike_source_seed);

    log_info("\tSeed (%u) = %u %u %u %u", seed_size, spike_source_seed[0],
             spike_source_seed[1], spike_source_seed[2], spike_source_seed[3]);

    num_spike_sources = address[PARAMETER_SEED_START_POSITION + seed_size];
    log_info("\tspike sources = %u", num_spike_sources);

    memcpy(
        &seconds_per_tick,
        &address[PARAMETER_SEED_START_POSITION + seed_size + 1],
        sizeof(UFRACT));

    memcpy(
        &ticks_per_second,
        &address[PARAMETER_SEED_START_POSITION + seed_size + 2],
        sizeof(REAL));

    memcpy(
        &slow_rate_per_tick_cutoff,
        &address[PARAMETER_SEED_START_POSITION + seed_size + 3],
        sizeof(REAL));

    // Allocate DTCM for array of spike sources and copy block of data
    if (num_spike_sources > 0) {

        // the first time around, the array is set to NULL, afterwards,
        // assuming all goes well, there's an address here.
        if (spike_source_array == NULL){
            spike_source_array = (spike_source_t*) spin1_malloc(
                num_spike_sources * sizeof(spike_source_t));
        }

        // if failed to alloc memory, report and fail.
        if (spike_source_array == NULL) {
            log_error("Failed to allocate spike_source_array");
            return false;
        }

        // store spike source data into DTCM
        uint32_t spikes_offset = PARAMETER_SEED_START_POSITION + seed_size + 5;
        memcpy(
            spike_source_array, &address[spikes_offset],
            num_spike_sources * sizeof(spike_source_t));

        // Loop through slow spike sources and initialise 1st time to spike
        for (index_t s = 0; s < num_spike_sources; s++) {
            if (!spike_source_array[s].is_fast_source) {
                spike_source_array[s].time_to_spike_ticks =
                    slow_spike_source_get_time_to_spike(
                        spike_source_array[s].mean_isi_ticks);
            }
        }

        // print spike sources for debug purposes
        print_spike_sources();
    }

    log_info("read_parameters: completed successfully");
    return true;
}

//! \brief Initialises the recording parts of the model
//! \return True if recording initialisation is successful, false otherwise
static bool initialise_recording(){

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Get the system region
    address_t recording_region = data_specification_get_region(
        SPIKE_HISTORY_REGION, address);

    bool success = recording_initialize(recording_region, &recording_flags);
    log_info("Recording flags = 0x%08x", recording_flags);

    return success;
}

//! Initialises the model by reading in the regions and checking recording
//! data.
//! \param[out] timer_period a pointer for the memory address where the timer
//!            period should be stored during the function.
//! \return boolean of True if it successfully read all the regions and set up
//!         all its internal data structures. Otherwise returns False
static bool initialize(uint32_t *timer_period) {
    log_info("Initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(address)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM, address),
            APPLICATION_NAME_HASH, timer_period, &simulation_ticks,
            &infinite_run, SDP, NULL,
            data_specification_get_region(PROVENANCE_REGION, address))) {
        return false;
    }

    // setup recording region
    if (!initialise_recording()){
        return false;
    }

    // Setup regions that specify spike source array data
    if (!read_poisson_parameters(
            data_specification_get_region(POISSON_PARAMS, address))) {
        return false;
    }

    log_info("Initialise: completed successfully");

    return true;
}

//! \brief runs any functions needed at resume time.
//! \return None
void resume_callback() {
    initialise_recording();

    address_t address = data_specification_get_data_address();

    if(!read_poisson_parameters(
            data_specification_get_region(POISSON_PARAMS, address))){
        log_error("failed to reread the poisson parameters from SDRAM")   ;
        rt_error(RTE_SWERR);
    }
}

//! \brief stores the poisson parameters back into sdram for reading by the
//! host when needed
//! \return None
bool store_poisson_parameters(){
    log_info("stored_parameters: starting");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();
    address = data_specification_get_region(POISSON_PARAMS, address);
    uint32_t seed_size = sizeof(mars_kiss64_seed_t) / sizeof(uint32_t);

    num_spike_sources = address[PARAMETER_SEED_START_POSITION + seed_size];
    log_info("\t spike sources = %u", num_spike_sources);

    // store array of spike sources into sdram for reading by the host
    if (num_spike_sources > 0) {
        uint32_t spikes_offset = PARAMETER_SEED_START_POSITION + seed_size + 4;
        memcpy(
            &address[spikes_offset], spike_source_array,
            num_spike_sources * sizeof(spike_source_t));
    }

    log_info("stored_parameters : completed successfully");
    return true;
}

//! \brief Timer interrupt callback
//! \param[in] timer_count the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused for consistency sake of the API always returning two
//!            parameters, this parameter has no semantics currently and thus
//!            is set to 0
//! \return None
void timer_callback(uint timer_count, uint unused) {
    use(timer_count);
    use(unused);
    time++;

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (infinite_run != TRUE && time >= simulation_ticks) {

        // rewrite poisson params to sdram for reading out if needed
        address_t address = data_specification_get_data_address();
        if (!store_poisson_parameters()){
            log_error("Failed to write poisson parameters to sdram");
            rt_error(RTE_SWERR);
        }

        // go into pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        if (recording_flags > 0) {
            recording_finalise();
        }

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time -= 1;
        return;
    }

    // Sleep for a random time
    spin1_delay_us(random_backoff_us);

    // Loop through spike sources
    for (index_t s = 0; s < num_spike_sources; s++) {

        // If this spike source is active this tick
        spike_source_t *spike_source = &spike_source_array[s];

        if (spike_source->is_fast_source) {
            if (time >= spike_source->start_ticks
                    && time < spike_source->end_ticks) {

                // Get number of spikes to send this tick
                uint32_t num_spikes = fast_spike_source_get_num_spikes(
                    spike_source->exp_minus_lambda);
                log_debug("Generating %d spikes", num_spikes);

                // If there are any
                if (num_spikes > 0) {

                    // Write spike to out spikes
                    out_spikes_set_spike(s);

                    // Send spikes
                    const uint32_t spike_key = key | s;
                    for (uint32_t s = 0; s < num_spikes; s++) {

                        // if no key has been given, do not send spike to fabric.
                        if (has_been_given_key){
                            log_debug("Sending spike packet %x at %d\n",
                                      spike_key, time);
                            while (!spin1_send_mc_packet(spike_key, 0,
                                                         NO_PAYLOAD)) {
                                spin1_delay_us(1);
                            }
                        }
                    }
                }
            }
        } else {
            if ((time >= spike_source->start_ticks)
                    && (time < spike_source->end_ticks)
                    && (spike_source->mean_isi_ticks != 0)) {

                // If this spike source should spike now
                if (REAL_COMPARE(
                        spike_source->time_to_spike_ticks, <=,
                        REAL_CONST(0.0))) {

                    // Write spike to out spikes
                    out_spikes_set_spike(s);

                    // if no key has been given, do not send spike to fabric.
                    if (has_been_given_key) {

                        // Send package
                        while (!spin1_send_mc_packet(
                                key | s, 0,
                                NO_PAYLOAD)) {
                            spin1_delay_us(1);
                        }
                        log_debug("Sending spike packet %x at %d\n",
                            key | s, time);
                    }

                    // Update time to spike
                    spike_source->time_to_spike_ticks +=
                        slow_spike_source_get_time_to_spike(
                            spike_source->mean_isi_ticks);
                }

                // Subtract tick
                spike_source->time_to_spike_ticks -= REAL_CONST(1.0);
            }
        }
    }

    // Record output spikes if required
    if (recording_flags > 0) {
        out_spikes_record(0, time);
    }
    out_spikes_reset();

    if (recording_flags > 0) {
        recording_do_timestep_update(time);
    }
}

//! The entry point for this model
void c_main(void) {

    // Load DTCM data
    uint32_t timer_period;
    if (!initialize(&timer_period)) {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    simulation_run();
}
