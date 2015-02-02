#include "../../common/key_conversion.h"
#include "../../common/out_spikes.h"
#include "../../common/recording.h"
#include "../../common/maths-util.h"

#include <data_specification.h>
#include <debug.h>
#include <random.h>
#include <simulation.h>
#include <spin1_api.h>
#include <string.h>

#define APPLICATION_MAGIC_NUMBER 0xAC3

typedef struct slow_spike_source_t {
    uint32_t neuron_id;
    uint32_t start_ticks;
    uint32_t end_ticks;

    REAL mean_isi_ticks;
    REAL time_to_spike_ticks;
} slow_spike_source_t;

typedef struct fast_spike_source_t {
    uint32_t neuron_id;
    uint32_t start_ticks;
    uint32_t end_ticks;
    UFRACT exp_minus_lambda;
} fast_spike_source_t;

// Globals
static slow_spike_source_t *slow_spike_source_array = NULL;
static fast_spike_source_t *fast_spike_source_array = NULL;
static uint32_t num_slow_spike_sources = 0;
static uint32_t num_fast_spike_sources = 0;
static mars_kiss64_seed_t spike_source_seed;
static uint32_t key;
static uint32_t recording_flags = 0;
static uint32_t time;
static uint32_t simulation_ticks = 0;

static inline REAL slow_spike_source_get_time_to_spike(REAL mean_isi_ticks) {
    return exponential_dist_variate(mars_kiss64_seed, spike_source_seed)
            * mean_isi_ticks;
}

static inline uint32_t fast_spike_source_get_num_spikes(
        UFRACT exp_minus_lambda) {
    return poisson_dist_variate_exp_minus_lambda(
        mars_kiss64_seed, spike_source_seed, exp_minus_lambda);
}

bool read_parameters(address_t address) {

    log_info("read_parameters: starting");

    key = address[0];
    log_info("\tkey = %08x, (x: %u, y: %u) proc: %u", key,
             key_x(key), key_y(key), key_p(key));

    uint32_t seed_size = sizeof(mars_kiss64_seed_t) / sizeof(uint32_t);
    memcpy(spike_source_seed, &address[1], seed_size * sizeof(uint32_t));
    validate_mars_kiss64_seed(spike_source_seed);

    log_info("\tSeed (%u) = %u %u %u %u", seed_size, spike_source_seed[0],
             spike_source_seed[1], spike_source_seed[2], spike_source_seed[3]);

    num_slow_spike_sources = address[1 + seed_size];
    num_fast_spike_sources = address[2 + seed_size];
    log_info("\tslow spike sources = %u, fast spike sources = %u,",
             num_slow_spike_sources, num_fast_spike_sources);

    // Allocate DTCM for array of slow spike sources and copy block of data
    slow_spike_source_array = (slow_spike_source_t*) spin1_malloc(
        num_slow_spike_sources * sizeof(slow_spike_source_t));
    if (slow_spike_source_array == NULL) {
        log_error("Failed to allocate slow_spike_source_array");
        return false;
    }
    memcpy(slow_spike_source_array, &address[3 + seed_size],
           num_slow_spike_sources * sizeof(slow_spike_source_t));

    // Loop through slow spike sources and initialise 1st time to spike
    for (index_t s = 0; s < num_slow_spike_sources; s++) {
        slow_spike_source_array[s].time_to_spike_ticks =
            slow_spike_source_get_time_to_spike(
                slow_spike_source_array[s].mean_isi_ticks);
    }

    // Allocate DTCM for array of fast spike sources and copy block of data
    uint32_t fast_spike_source_offset =
        3 + seed_size + (num_slow_spike_sources
                         * (sizeof(slow_spike_source_t) / sizeof(uint32_t)));
    fast_spike_source_array = (fast_spike_source_t*) spin1_malloc(
        num_fast_spike_sources * sizeof(fast_spike_source_t));
    if (fast_spike_source_array == NULL) {
        log_error("Failed to allocate fast_spike_source_array");
        return false;
    }
    memcpy(fast_spike_source_array, &address[fast_spike_source_offset],
           num_fast_spike_sources * sizeof(fast_spike_source_t));

    for (index_t s = 0; s < num_fast_spike_sources; s++) {
        log_debug("\t\tNeuron id %d, exp(-k) = %0.8x",
                  fast_spike_source_array[s].neuron_id,
                  fast_spike_source_array[s].exp_minus_lambda);
    }
    log_info("read_parameters: completed successfully");
    return true;
}

static bool initialize(uint32_t *timer_period) {
    log_info("initialize: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    uint32_t version;
    if (!data_specification_read_header(address, &version)) {
        return false;
    }

    // Get the timing details
    if (!simulation_read_timing_details(
            data_specification_get_region(0, address),
            APPLICATION_MAGIC_NUMBER,
            timer_period, &simulation_ticks)) {
        return false;
    }

    // Get the recording information
    uint32_t spike_history_region_size;
    recording_read_region_sizes(
        &data_specification_get_region(0, address)[3], &recording_flags,
        &spike_history_region_size, NULL, NULL);
    if (recording_is_channel_enabled(
            recording_flags, e_recording_channel_spike_history)) {
        if (!recording_initialze_channel(
                data_specification_get_region(2, address),
                e_recording_channel_spike_history, spike_history_region_size)) {
            return false;
        }
    }

    // Setup regions that specify spike source array data
    if (!read_parameters(data_specification_get_region(1, address))) {
        return false;
    }

    log_info("initialize: completed successfully");

    return true;
}

// Callbacks
void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    time++;

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (simulation_ticks != UINT32_MAX && time >= simulation_ticks) {
        log_info("Simulation complete.\n");

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        recording_finalise();
        spin1_exit(0);
    }

    // Loop through slow spike sources
    for (index_t s = 0; s < num_slow_spike_sources; s++) {

        // If this spike source is active this tick
        slow_spike_source_t *slow_spike_source = &slow_spike_source_array[s];
        if ((time >= slow_spike_source->start_ticks)
                && (time < slow_spike_source->end_ticks)) {

            // If this spike source should spike now
            if (slow_spike_source->time_to_spike_ticks <= REAL_CONST(0.0)) {

                // Write spike to out spikes
                out_spikes_set_spike(slow_spike_source->neuron_id);

                // Send package
                spin1_send_mc_packet(key | slow_spike_source->neuron_id, 0,
                                     NO_PAYLOAD);

                log_debug("Sending spike packet %x at %d\n",
                        key | slow_spike_source->neuron_id, time);

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
    for (index_t f = 0; f < num_fast_spike_sources; f++) {

        // If this spike source is active this tick
        fast_spike_source_t *fast_spike_source = &fast_spike_source_array[f];
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
                for (uint32_t s = 0; s < num_spikes; s++) {
                    log_debug("Sending spike packet %x at %d\n", spike_key,
                              time);
                    while (!spin1_send_mc_packet(spike_key, 0, NO_PAYLOAD)) {
                        spin1_delay_us(1);
                    }
                }
            }
        }
    }

    // Record output spikes if required
    out_spikes_record(recording_flags);
    out_spikes_reset();
}

// Entry point
void c_main(void) {

    // Load DTCM data
    uint32_t timer_period;
    if (!initialize(&timer_period)) {
        return;
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Initialize out spikes buffer to support number of neurons
    if (!out_spikes_initialize(num_fast_spike_sources
                               + num_slow_spike_sources)) {
        return;
    }

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(TIMER_TICK, timer_callback, 2);

    log_info("Starting");
    simulation_run();
}
