/*! \file
 *
 *  \brief This file contains the main functions for a poisson spike generator.
 *
 *
 */

#include "../../common/maths-util.h"

#include <bit_field.h>
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
//! tick; this is separated from spikes which have multiple timer ticks
//! between firings as there are separate algorithms for each type.
typedef struct fast_spike_source_t {
    uint32_t neuron_id;
    uint32_t start_ticks;
    uint32_t end_ticks;
    UFRACT exp_minus_lambda;
} fast_spike_source_t;

//! spike source array region ids in human readable form
typedef enum region {
    SYSTEM, POISSON_PARAMS,
    BUFFERING_OUT_SPIKE_RECORDING_REGION,
    BUFFERING_OUT_CONTROL_REGION,
    PROVENANCE_REGION
} region;

#define NUMBER_OF_REGIONS_TO_RECORD 1

typedef enum callback_priorities{
    SDP = 0, TIMER = 2
} callback_priorities;

//! what each position in the poisson parameter region actually represent in
//! terms of data (each is a word)
typedef enum poisson_region_parameters{
    HAS_KEY, TRANSMISSION_KEY, RANDOM_BACKOFF, TIME_BETWEEN_SPIKES,
    PARAMETER_SEED_START_POSITION,
} poisson_region_parameters;

typedef struct timed_out_spikes{
    uint32_t time;
    uint32_t n_buffers;
    uint32_t out_spikes[];
} timed_out_spikes;

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

//! An amount of microseconds to back off before starting the timer, in an
//! attempt to avoid overloading the network
static uint32_t random_backoff_us;

//! The number of clock ticks between sending each spike
static uint32_t time_between_spikes;

//! The expected current clock tick of timer_1
static uint32_t expected_time;

//! keeps track of which types of recording should be done to this model.
static uint32_t recording_flags = 0;

//! the time interval parameter TODO this variable could be removed and use the
//! timer tick callback timer value.
static uint32_t time;

//! the number of timer ticks that this model should run for before exiting.
static uint32_t simulation_ticks = 0;

//! the int that represents the bool for if the run is infinite or not.
static uint32_t infinite_run;

//! The recorded spikes
static timed_out_spikes *spikes = NULL;

//! The number of recording spike buffers that have been allocated
static uint32_t n_spike_buffers_allocated;

//! The size of each spike buffer in bytes
static uint32_t spike_buffer_size;

static uint32_t n_spike_buffer_words;

static inline bit_field_t _out_spikes(uint32_t n) {
    return &(spikes->out_spikes[n * n_spike_buffer_words]);
}

static inline void _reset_spikes() {
    spikes->n_buffers = 0;
    for (uint32_t n = n_spike_buffers_allocated; n > 0; n--) {
        clear_bit_field(_out_spikes(n - 1), n_spike_buffer_words);
    }
}

static inline void _mark_spike(uint32_t neuron_id, uint32_t n_spikes) {
    if (recording_flags > 0) {
        if (n_spike_buffers_allocated < n_spikes) {
            uint32_t new_size = 8 + (n_spikes * spike_buffer_size);
            timed_out_spikes *new_spikes = (timed_out_spikes *) spin1_malloc(
                new_size);
            if (new_spikes == NULL) {
                log_error("Cannot reallocate spike buffer");
                rt_error(RTE_SWERR);
            }
            uint32_t *data = (uint32_t *) new_spikes;
            for (uint32_t n = new_size >> 2; n > 0; n--) {
                data[n - 1] = 0;
            }
            if (spikes != NULL) {
                uint32_t old_size =
                    8 + (n_spike_buffers_allocated * spike_buffer_size);
                spin1_memcpy(new_spikes, spikes, old_size);
                sark_free(spikes);
            }
            spikes = new_spikes;
            n_spike_buffers_allocated = n_spikes;
        }
        if (spikes->n_buffers < n_spikes) {
            spikes->n_buffers = n_spikes;
        }
        for (uint32_t n = n_spikes; n > 0; n--) {
            bit_field_set(_out_spikes(n - 1), neuron_id);
        }
    }
}

static inline void _record_spikes(uint32_t time) {
    if ((spikes != NULL) && (spikes->n_buffers > 0)) {
        spikes->time = time;
        recording_record(
            0, spikes, 8 + (spikes->n_buffers * spike_buffer_size));
        _reset_spikes();
    }
}

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
    random_backoff_us = address[RANDOM_BACKOFF];
    time_between_spikes = address[TIME_BETWEEN_SPIKES] * sv->cpu_clk;
    log_info("\t key = %08x, back off = %u", key, random_backoff_us);

    uint32_t seed_size = sizeof(mars_kiss64_seed_t) / sizeof(uint32_t);
    memcpy(spike_source_seed, &address[PARAMETER_SEED_START_POSITION],
        seed_size * sizeof(uint32_t));
    validate_mars_kiss64_seed(spike_source_seed);

    log_info("\tSeed (%u) = %u %u %u %u", seed_size, spike_source_seed[0],
             spike_source_seed[1], spike_source_seed[2], spike_source_seed[3]);

    num_slow_spike_sources = address[PARAMETER_SEED_START_POSITION + seed_size];
    num_fast_spike_sources = address[PARAMETER_SEED_START_POSITION +
                                     seed_size + 1];
    log_info("\t slow spike sources = %u, fast spike sources = %u,",
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
        recording_flags_from_system_conf, state_region, &recording_flags);
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

    // Set up recording buffer
    n_spike_buffers_allocated = 0;
    n_spike_buffer_words = get_bit_field_size(
        num_fast_spike_sources + num_slow_spike_sources);
    spike_buffer_size = n_spike_buffer_words * sizeof(uint32_t);

    log_info("Initialise: completed successfully");

    return true;
}

void resume_callback() {

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
        recording_flags_from_system_conf, state_region,
        &recording_flags);
}

void _send_spike(uint spike_key) {

    // Wait until the expected time to send
    while (tc[T1_COUNT] > expected_time) {

        // Do Nothing
    }
    expected_time -= time_between_spikes;

    // Send the spike
    log_debug("Sending spike packet %x at %d\n", spike_key, time);
    while (!spin1_send_mc_packet(spike_key, 0, NO_PAYLOAD)) {
        spin1_delay_us(1);
    }
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

    // Set the next expected time to wait for between spike sending
    expected_time = tc[T1_COUNT] - time_between_spikes;

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

                _mark_spike(slow_spike_source->neuron_id, 1);

                // if no key has been given, do not send spike to fabric.
                if (has_been_given_key) {

                    // Send package
                    _send_spike(key | slow_spike_source->neuron_id);
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

                _mark_spike(fast_spike_source->neuron_id, num_spikes);

                // Send spikes
                if (has_been_given_key) {
                    const uint32_t spike_key =
                        key | fast_spike_source->neuron_id;
                    for (uint32_t s = num_spikes; s > 0; s--) {

                        // if no key has been given, do not send spike to fabric.
                        _send_spike(spike_key);
                    }
                }
            }
        }
    }

    // Record output spikes if required
    if (recording_flags > 0) {
        _record_spikes(time);
    }

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
