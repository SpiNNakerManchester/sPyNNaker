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

//! data structure for spikes which have multiple timer tick between firings
//! this is separated from spikes which fire at least once every timer tick as
//! there are separate algorithms for each type.
typedef struct slow_spike_source_t {
    uint32_t neuron_id;
    uint32_t start_ticks;
    uint32_t end_ticks;

    REAL mean_isi_ticks;
    REAL time_to_spike_ticks;
} slow_spike_source_t;

//! data structure for spikes which have at least one spike fired per timer
//! tick; this is separated from spikes which have multiple timer ticks\
//! between firings as there are separate algorithms for each type.
typedef struct fast_spike_source_t {
    uint32_t neuron_id;
    uint32_t start_ticks;
    uint32_t end_ticks;
    UFRACT exp_minus_lambda;
} fast_spike_source_t;

//! spike source array region ids in human readable form
typedef enum region{
    SYSTEM, POISSON_PARAMS,
    BUFFERING_OUT_SPIKE_RECORDING_REGION,
    BUFFERING_OUT_CONTROL_REGION
}region;

#define NUMBER_OF_REGIONS_TO_RECORD 1

typedef enum callback_priorities{
    SDP = 0, TIMER = 2
} callback_priorities;

//! what each position in the poisson parameter region actually represent in
//! terms of data (each is a word)
typedef enum poisson_region_parameters{
    HAS_KEY, TRANSMISSION_KEY, PARAMETER_SEED_START_POSITION,
} poisson_region_parameters;

// Globals
//! global variable which contains all the data for neurons which are expected
//! to exhibit slow spike generation (less than 1 per timer tick)
//! (separated for efficiently purposes)
static slow_spike_source_t *slow_spike_source_array = NULL;

//! global variable which contains all the data for neurons which are expected
//! to exhibit fast spike generation (more than than 1 per timer tick)
//! (separated for efficiently purposes)
static fast_spike_source_t *fast_spike_source_array = NULL;

//! counter for how many neurons exhibit slow spike generation
static uint32_t num_slow_spike_sources = 0;

//! counter for how many neurons exhibit fast spike generation
static uint32_t num_fast_spike_sources = 0;

//! a variable that will contain the seed to initiate the poisson generator.
static mars_kiss64_seed_t spike_source_seed;

//! a variable which checks if there has been a key allocated to this spike
//! source Poisson
static bool has_been_given_key;

//! A variable that contains the key value that this model should transmit with
static uint32_t key;

//! keeps track of which types of recording should be done to this model.
static uint32_t recording_flags = 0;

//! the time interval parameter TODO this variable could be removed and use the
//! timer tick callback timer value.
static uint32_t time;

//! the number of timer ticks that this model should run for before exiting.
static uint32_t simulation_ticks = 0;

//! the int that represents the bool for if the run is infinite or not.
static uint32_t infinite_run;

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

//! \entry method for reading the parameters stored in Poisson parameter region
//! \param[in] address the absolute SDRAm memory address to which the
//!            Poisson parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
bool read_poisson_parameters(address_t address) {

    log_info("read_parameters: starting");

    has_been_given_key = address[HAS_KEY];
    key = address[TRANSMISSION_KEY];
    log_info("\tkey = %08x", key);

    uint32_t seed_size = sizeof(mars_kiss64_seed_t) / sizeof(uint32_t);
    memcpy(spike_source_seed, &address[PARAMETER_SEED_START_POSITION],
        seed_size * sizeof(uint32_t));
    validate_mars_kiss64_seed(spike_source_seed);

    log_info("\tSeed (%u) = %u %u %u %u", seed_size, spike_source_seed[0],
             spike_source_seed[1], spike_source_seed[2], spike_source_seed[3]);

    num_slow_spike_sources = address[PARAMETER_SEED_START_POSITION + seed_size];
    num_fast_spike_sources = address[PARAMETER_SEED_START_POSITION +
                                     seed_size + 1];
    log_info("\tslow spike sources = %u, fast spike sources = %u,",
             num_slow_spike_sources, num_fast_spike_sources);

    // Allocate DTCM for array of slow spike sources and copy block of data
    if (num_slow_spike_sources > 0) {
        slow_spike_source_array = (slow_spike_source_t*) spin1_malloc(
            num_slow_spike_sources * sizeof(slow_spike_source_t));
        if (slow_spike_source_array == NULL) {
            log_error("Failed to allocate slow_spike_source_array");
            return false;
        }
        uint32_t slow_spikes_offset = PARAMETER_SEED_START_POSITION +
                                    seed_size + 2;
        memcpy(slow_spike_source_array,
                &address[slow_spikes_offset],
               num_slow_spike_sources * sizeof(slow_spike_source_t));

        // Loop through slow spike sources and initialise 1st time to spike
        for (index_t s = 0; s < num_slow_spike_sources; s++) {
            slow_spike_source_array[s].time_to_spike_ticks =
                slow_spike_source_get_time_to_spike(
                    slow_spike_source_array[s].mean_isi_ticks);
        }
    }

    // Allocate DTCM for array of fast spike sources and copy block of data
    if (num_fast_spike_sources > 0) {
        fast_spike_source_array = (fast_spike_source_t*) spin1_malloc(
            num_fast_spike_sources * sizeof(fast_spike_source_t));
        if (fast_spike_source_array == NULL) {
            log_error("Failed to allocate fast_spike_source_array");
            return false;
        }
        // locate offset for the fast spike sources in the SDRAM from where the
        // seed finished.
        uint32_t fast_spike_source_offset =
                PARAMETER_SEED_START_POSITION + seed_size + 2 +
            + (num_slow_spike_sources * (sizeof(slow_spike_source_t)
                / sizeof(uint32_t)));
        memcpy(fast_spike_source_array, &address[fast_spike_source_offset],
               num_fast_spike_sources * sizeof(fast_spike_source_t));

        for (index_t s = 0; s < num_fast_spike_sources; s++) {
            log_debug("\t\tNeuron id %d, exp(-k) = %0.8x",
                      fast_spike_source_array[s].neuron_id,
                      fast_spike_source_array[s].exp_minus_lambda);
        }
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
    address_t system_region = data_specification_get_region(
            SYSTEM, address);

    // Get the recording information
    uint8_t regions_to_record[] = {
        BUFFERING_OUT_SPIKE_RECORDING_REGION,
    };
    uint8_t n_regions_to_record = NUMBER_OF_REGIONS_TO_RECORD;
    uint32_t *recording_flags_from_system_conf =
        &system_region[SIMULATION_N_TIMING_DETAIL_WORDS];
    uint8_t state_region = BUFFERING_OUT_CONTROL_REGION;

    bool success = recording_initialize(
        n_regions_to_record, regions_to_record,
        recording_flags_from_system_conf, state_region, 2, &recording_flags);
    log_info("Recording flags = 0x%08x", recording_flags);
    return success;
}

//! Initialises the model by reading in the regions and checking recording
//! data.
//! \param[in] *timer_period a pointer for the memory address where the timer
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

    // Get the timing details
    address_t system_region = data_specification_get_region(
            SYSTEM, address);
    if (!simulation_read_timing_details(
            system_region, APPLICATION_NAME_HASH, timer_period,
            &simulation_ticks, &infinite_run)) {
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

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        if (recording_flags > 0) {
            recording_finalise();
        }
        // go into pause and resume state
        simulation_handle_pause_resume(timer_callback, TIMER);

        // handle resetting the recording state
        // Get the recording information
        address_t address = data_specification_get_data_address();
        address_t system_region = data_specification_get_region(
            SYSTEM, address);
        uint8_t regions_to_record[] = {
            BUFFERING_OUT_SPIKE_RECORDING_REGION,
        };
        uint8_t n_regions_to_record = NUMBER_OF_REGIONS_TO_RECORD;
        uint32_t *recording_flags_from_system_conf =
            &system_region[SIMULATION_N_TIMING_DETAIL_WORDS];
        uint8_t state_region = BUFFERING_OUT_CONTROL_REGION;

        recording_initialize(
            n_regions_to_record, regions_to_record,
            recording_flags_from_system_conf, state_region, 2,
            &recording_flags);
        }

    // Loop through slow spike sources
    slow_spike_source_t *slow_spike_sources = slow_spike_source_array;
    for (index_t s = num_slow_spike_sources; s > 0; s--) {

        // If this spike source is active this tick
        slow_spike_source_t *slow_spike_source = slow_spike_sources++;
        if ((time >= slow_spike_source->start_ticks)
                && (time < slow_spike_source->end_ticks)
                && (REAL_COMPARE(slow_spike_source->mean_isi_ticks, !=,
                    REAL_CONST(0.0)))) {

            // If this spike source should spike now
            if (REAL_COMPARE(slow_spike_source->time_to_spike_ticks, <=,
                             REAL_CONST(0.0))) {

                // Write spike to out spikes
                out_spikes_set_spike(slow_spike_source->neuron_id);

                // if no key has been given, do not send spike to fabric.
                if (has_been_given_key) {

                    // Send package
                    while (!spin1_send_mc_packet(
                            key | slow_spike_source->neuron_id, 0,
                            NO_PAYLOAD)) {
                        spin1_delay_us(1);
                    }
                    log_debug("Sending spike packet %x at %d\n",
                        key | slow_spike_source->neuron_id, time);
                }

                // Update time to spike
                slow_spike_source->time_to_spike_ticks +=
                    slow_spike_source_get_time_to_spike(
                        slow_spike_source->mean_isi_ticks);
            }

            // Subtract tick
            slow_spike_source->time_to_spike_ticks -= REAL_CONST(1.0);
        }
    }

    // Loop through fast spike sources
    fast_spike_source_t *fast_spike_sources = fast_spike_source_array;
    for (index_t f = num_fast_spike_sources; f > 0; f--) {
        fast_spike_source_t *fast_spike_source = fast_spike_sources++;

        if (time >= fast_spike_source->start_ticks
                && time < fast_spike_source->end_ticks) {

            // Get number of spikes to send this tick
            uint32_t num_spikes = fast_spike_source_get_num_spikes(
                fast_spike_source->exp_minus_lambda);
            log_debug("Generating %d spikes", num_spikes);

            // If there are any
            if (num_spikes > 0) {

                // Write spike to out spikes
                out_spikes_set_spike(fast_spike_source->neuron_id);

                // Send spikes
                const uint32_t spike_key = key | fast_spike_source->neuron_id;
                for (uint32_t s = num_spikes; s > 0; s--) {

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
        rt_error(RTE_SWERR);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Initialise out spikes buffer to support number of neurons
    if (!out_spikes_initialize(num_fast_spike_sources
                               + num_slow_spike_sources)) {
         rt_error(RTE_SWERR);
    }

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

        // Set up callback listening to SDP messages
    simulation_register_simulation_sdp_callback(&simulation_ticks, SDP);

    log_info("Starting");
    simulation_run();
}
