/*! \file
 *
 *  \brief This file contains the main functions for a poisson spike generator.
 *
 *
 */

#include <common/maths-util.h>

#include <data_specification.h>
#include <recording.h>
#include <debug.h>
#include <random.h>
#include <simulation.h>
#include <spin1_api.h>
#include <bit_field.h>

// Declare spin1_wfi
extern void spin1_wfi(void);

// Spin1 API ticks - to know when the timer wraps
extern uint ticks;

//! data structure for poisson sources
typedef struct spike_source_t {
    uint32_t start_ticks;
    uint32_t end_ticks;
    bool is_fast_source;

    UFRACT exp_minus_lambda;
    REAL mean_isi_ticks;
    REAL time_to_spike_ticks;
} spike_source_t;

//! \brief data structure for recording spikes
typedef struct timed_out_spikes {
    uint32_t time;
    uint32_t n_buffers;
    uint32_t out_spikes[];
} timed_out_spikes;

//! spike source array region IDs in human readable form
enum region {
    SYSTEM,
    POISSON_PARAMS,
    SPIKE_HISTORY_REGION,
    PROVENANCE_REGION
};

#define NUMBER_OF_REGIONS_TO_RECORD 1
#define BYTE_TO_WORD_CONVERTER 4

enum callback_priorities {
    MULTICAST = -1,
    SDP = 0,
    DMA = 1,
    TIMER = 2
};

//! Parameters of the SpikeSourcePoisson
typedef struct global_parameters_t {
    //! True if there is a key to transmit, False otherwise
    bool has_key;
    //! The base key to send with (neuron ID to be added to it), or 0 if no key
    uint32_t key;
    //! The mask to work out the neuron ID when setting the rate
    uint32_t set_rate_neuron_id_mask;
    //! The offset of the timer ticks to desynchronize sources
    uint32_t timer_offset;
    //! The expected time to wait between spikes
    uint32_t time_between_spikes;
    //! The time between ticks in seconds for setting the rate
    UFRACT seconds_per_tick;
    //! The number of ticks per second for setting the rate
    REAL ticks_per_second;
    //! The border rate between slow and fast sources
    REAL slow_rate_per_tick_cutoff;
    //! The ID of the first source relative to the population as a whole
    uint32_t first_source_id;
    //! The number of sources in this sub-population
    uint32_t n_spike_sources;
    //! The seed for the Poisson generation process
    mars_kiss64_seed_t spike_source_seed;
} global_parameters_t;

typedef struct sdram_globals_t {
    global_parameters_t globals;
    spike_source_t spike_sources[];
} sdram_globals_t;

//! The global parameters for the sub-population
static global_parameters_t globals;

//! global variable which contains all the data for neurons
static spike_source_t *poisson_params = NULL;

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

//! The number of words needed for 1 bit per source
static uint32_t n_spike_buffer_words;

//! The size of each spike buffer in bytes
static uint32_t spike_buffer_size;

//! True if DMA recording is currently in progress
static bool recording_in_progress = false;

//! The timer period
static uint32_t timer_period;

//! \brief Helper that makes getting a region easier
static inline void *get_region(enum region region_id) {
    static address_t address = data_specification_get_data_address();

    return data_specification_get_region(region_id, address);
}

//! \brief ??????????????
//! \param[in] n ?????????????????
//! \return bit field of the ???????????????
static inline bit_field_t _out_spikes(uint32_t n) {
    return &spikes->out_spikes[n * n_spike_buffer_words];
}

//! \brief ??????????????
//! \return None
static inline void _reset_spikes(void) {
    spikes->n_buffers = 0;
    for (uint32_t n = n_spike_buffers_allocated; n > 0; n--) {
        clear_bit_field(_out_spikes(n - 1), n_spike_buffer_words);
    }
}

//! \brief deduces the time in timer ticks until the next spike is to occur
//!        given the mean inter-spike interval
//! \param[in] mean_inter_spike_interval_in_ticks The mean number of ticks
//!            before a spike is expected to occur in a slow process.
//! \return a real which represents time in timer ticks until the next spike is
//!         to occur
static inline REAL get_slow_time_to_spike(
        REAL mean_inter_spike_interval_in_ticks) {
    return exponential_dist_variate(
            mars_kiss64_seed, globals.spike_source_seed)
        * mean_inter_spike_interval_in_ticks;
}

//! \brief Determines how many spikes to transmit this timer tick.
//! \param[in] exp_minus_lambda The amount of spikes expected to be produced
//!            this timer interval (timer tick in real time)
//! \return a uint32_t which represents the number of spikes to transmit
//!         this timer tick
static inline uint32_t get_fast_num_spikes(
        UFRACT exp_minus_lambda) {
    if (bitsulr(exp_minus_lambda) == bitsulr(UFRACT_CONST(0.0))) {
        return 0;
    }

    return poisson_dist_variate_exp_minus_lambda(
            mars_kiss64_seed, globals.spike_source_seed, exp_minus_lambda);
}

static void print_spike_sources(void) {
#ifdef PRINT_SPIKE_SOURCES
    for (index_t s = 0; s < globals.n_spike_sources; s++) {
        log_info("atom %d", s);
        log_info("scaled_start = %u", poisson_params[s].start_ticks);
        log_info("scaled end = %u", poisson_params[s].end_ticks);
        log_info("is_fast_source = %d", poisson_params[s].is_fast_source);
        log_info("exp_minus_lamda = %k",
                (REAL) (poisson_params[s].exp_minus_lambda));
        log_info("isi_val = %k", poisson_params[s].mean_isi_ticks);
        log_info("time_to_spike = %k",
                poisson_params[s].time_to_spike_ticks);
    }
#endif // PRINT_SPIKE_SOURCES
}

//! \brief entry method for reading the global parameters stored in Poisson
//!        parameter region
//! \param[in] address the absolute SDRAm memory address to which the
//!            Poisson parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
static bool read_global_parameters(sdram_globals_t *address) {
    log_info("read_global_parameters: starting");

    spin1_memcpy(&globals, &address->globals, sizeof(global_parameters_t));

    log_info("\tkey = %08x, set rate mask = %08x, timer offset = %u",
            globals.key, globals.set_rate_neuron_id_mask,
            globals.timer_offset);
    log_info("\tseed = %u %u %u %u",
            globals.spike_source_seed[0], globals.spike_source_seed[1],
            globals.spike_source_seed[2], globals.spike_source_seed[3]);

    validate_mars_kiss64_seed(globals.spike_source_seed);

    log_info("\tspike sources = %u, starting at %u",
            globals.n_spike_sources, globals.first_source_id);
    log_info("seconds_per_tick = %k\n", (REAL) globals.seconds_per_tick);
    log_info("ticks_per_second = %k\n", globals.ticks_per_second);
    log_info("slow_rate_per_tick_cutoff = %k\n",
            globals.slow_rate_per_tick_cutoff);

    log_info("read_global_parameters: completed successfully");
    return true;
}

//! \brief method for reading the parameters stored in Poisson parameter region
//! \param[in] sdram_globals the absolute SDRAM memory address to which the
//!            Poisson parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
static bool read_poisson_parameters(sdram_globals_t *sdram_globals) {
    // Allocate DTCM for array of spike sources and copy block of data
    if (globals.n_spike_sources > 0) {
        // the first time around, the array is set to NULL, afterwards,
        // assuming all goes well, there's an address here.
        if (poisson_params == NULL) {
            poisson_params = spin1_malloc(
                    globals.n_spike_sources * sizeof(spike_source_t));
            // if failed to alloc memory, report and fail.
            if (poisson_params == NULL) {
                log_error("Failed to allocate poisson_params");
                return false;
            }
        }

        // store spike source data into DTCM
        spin1_memcpy(poisson_params, &sdram_globals->spike_sources,
                globals.n_spike_sources * sizeof(spike_source_t));
    }
    log_info("read_poisson_parameters: completed successfully");
    return true;
}

//! \brief Initialises the recording parts of the model
//! \return True if recording initialisation is successful, false otherwise
static bool initialise_recording(void) {
    // Get the system region
    address_t recording_region = get_region(SPIKE_HISTORY_REGION);

    bool success = recording_initialize(recording_region, &recording_flags);
    log_info("Recording flags = 0x%08x", recording_flags);

    return success;
}

//! Initialises the model by reading in the regions and checking recording
//! data.
//! \param[out] timer_period a pointer for the memory address where the timer
//!            period should be stored during the function.
//! \param[out] update_sdp_port The SDP port on which to listen for rate
//!             updates
//! \return boolean of True if it successfully read all the regions and set up
//!         all its internal data structures. Otherwise returns False
static bool initialize(void) {
    log_info("Initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(address)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            get_region(SYSTEM), APPLICATION_NAME_HASH,
            &timer_period, &simulation_ticks, &infinite_run, SDP, DMA)) {
        return false;
    }
    simulation_set_provenance_data_address(get_region(PROVENANCE_REGION));

    // setup recording region
    if (!initialise_recording()) {
        return false;
    }

    // Setup regions that specify spike source array data
    if (!read_global_parameters(get_region(POISSON_PARAMS))) {
        return false;
    }

    if (!read_poisson_parameters(get_region(POISSON_PARAMS))) {
        return false;
    }

    // Loop through slow spike sources and initialise 1st time to spike
    for (index_t s = 0; s < globals.n_spike_sources; s++) {
        if (!poisson_params[s].is_fast_source) {
            poisson_params[s].time_to_spike_ticks =
                    get_slow_time_to_spike(poisson_params[s].mean_isi_ticks);
        }
    }

    // print spike sources for debug purposes
    print_spike_sources();

    // Set up recording buffer
    n_spike_buffers_allocated = 0;
    n_spike_buffer_words = get_bit_field_size(globals.n_spike_sources);
    spike_buffer_size = n_spike_buffer_words * sizeof(uint32_t);

    log_info("Initialise: completed successfully");
    return true;
}

//! \brief runs any functions needed at resume time.
//! \return None
static void resume_callback(void) {
    recording_reset();

    if (!read_poisson_parameters(get_region(POISSON_PARAMS))) {
        log_error("failed to reread the Poisson parameters from SDRAM");
        rt_error(RTE_SWERR);
    }

    // Loop through slow spike sources and initialise 1st time to spike
    for (index_t s = 0; s < globals.n_spike_sources; s++) {
        if (!poisson_params[s].is_fast_source &&
                poisson_params[s].time_to_spike_ticks == 0) {
            poisson_params[s].time_to_spike_ticks =
                    get_slow_time_to_spike(poisson_params[s].mean_isi_ticks);
        }
    }

    log_info("Successfully resumed Poisson spike source at time: %u", time);

    // print spike sources for debug purposes
    print_spike_sources();
}

//! \brief stores the Poisson parameters back into SDRAM for reading by the
//! host when needed
//! \return None
static bool store_poisson_parameters(void) {
    log_info("stored_parameters: starting");

    // Get the address this core's DTCM data starts at from SRAM
    sdram_globals_t *sdram_globals = get_region(POISSON_PARAMS);

    // Copy the globals back to SDRAM
    spin1_memcpy(&sdram_globals->globals, &globals,
            sizeof(global_parameters_t));

    // store spike source parameters into array into SDRAM for reading by
    // the host
    if (globals.n_spike_sources > 0) {
        spin1_memcpy(&sdram_globals->spike_sources, poisson_params,
                globals.n_spike_sources * sizeof(spike_source_t));
    }

    log_info("stored_parameters : completed successfully");
    return true;
}

//! \brief handles spreading of Poisson spikes for even packet reception at
//! destination
//! \param[in] spike_key: the key to transmit
//! \return None
static void _send_spike(uint spike_key, uint timer_count) {
    // Wait until the expected time to send
    while ((ticks == timer_count) && (tc[T1_COUNT] > expected_time)) {
        // Do Nothing
    }
    expected_time -= time_between_spikes;

    // Send the spike
    log_debug("Sending spike packet %x at %d\n", spike_key, time);
    while (!spin1_send_mc_packet(spike_key, 0, NO_PAYLOAD)) {
        spin1_delay_us(1);
    }
}

//! \brief expand the space for storing spikes
//! \param[in] n_spikes: the number of times a neuron has spiked
//!
static void _expand_spike_buffer(uint32_t n_spikes) {
    uint32_t new_size = 8 + (n_spikes * spike_buffer_size);

    timed_out_spikes *new_spikes = spin1_malloc(new_size);
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

//! \brief records spikes as needed
//! \param[in] neuron_id: the neurons to store spikes from
//! \param[in] n_spikes: the number of times this neuron has spiked
//!
static inline void _mark_spike(uint32_t neuron_id, uint32_t n_spikes) {
    if (recording_flags > 0) {
        if (n_spike_buffers_allocated < n_spikes) {
            _expand_spike_buffer(n_spikes);
        }
        if (spikes->n_buffers < n_spikes) {
            spikes->n_buffers = n_spikes;
        }
        for (uint32_t n = n_spikes; n > 0; n--) {
            bit_field_set(_out_spikes(n - 1), neuron_id);
        }
    }
}

static void recording_complete_callback(void) {
    recording_in_progress = false;
}

//! \brief writing spikes to SDRAM
//! \param[in] time: the time to which these spikes are being recorded
static inline void _record_spikes(uint32_t timestamp) {
    while (recording_in_progress) {
        spin1_wfi();
    }
    if ((spikes != NULL) && (spikes->n_buffers > 0)) {
        recording_in_progress = true;
        spikes->time = timestamp;
        recording_record_and_notify(
                0, spikes, 8 + (spikes->n_buffers * spike_buffer_size),
                recording_complete_callback);
        _reset_spikes();
    }
}

static inline void handle_fast_source(
        spike_source_t *spike_source, index_t s, uint timer_count) {
    if (time < spike_source->start_ticks || time >= spike_source->end_ticks) {
        return;
    }

    // Get number of spikes to send this tick
    uint32_t num_spikes = get_fast_num_spikes(spike_source->exp_minus_lambda);
    log_debug("Generating %d spikes", num_spikes);

    // If there are any
    if (num_spikes > 0) {
        // Write spike to out spikes
        _mark_spike(s, num_spikes);

        // only send spike to fabric if a key has been given
        if (globals.has_key) {
            const uint32_t spike_key = globals.key | s;
            for (uint32_t index = 0; index < num_spikes; index++) {
                _send_spike(spike_key, timer_count);
            }
        }
    }
}

static inline void handle_slow_source(
        spike_source_t *spike_source, index_t s, uint timer_count) {
    if ((time < spike_source->start_ticks)
            || (time >= spike_source->end_ticks)
            || (spike_source->mean_isi_ticks == 0)) {
        return;
    }
    // If this spike source should spike now
    if (REAL_COMPARE(spike_source->time_to_spike_ticks, <=, REAL_CONST(0.0))) {
        // Write spike to out spikes
        _mark_spike(s, 1);

        // if no key has been given, do not send spike to fabric.
        if (globals.has_key) {
            // Send packet
            _send_spike(globals.key | s, timer_count);
        }

        // Update time to spike
        spike_source->time_to_spike_ticks +=
                get_slow_time_to_spike(spike_source->mean_isi_ticks);
    }

    // Subtract tick
    spike_source->time_to_spike_ticks -= REAL_CONST(1.0);
}

//! \brief Timer interrupt callback
//! \param[in] timer_count the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused for consistency sake of the API always returning two
//!            parameters, this parameter has no semantics currently and thus
//!            is set to 0
//! \return None
static void timer_callback(uint timer_count, uint unused) {
    use(unused);
    time++;

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (infinite_run != TRUE && time >= simulation_ticks) {
        // go into pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // rewrite poisson params to SDRAM for reading out if needed
        if (!store_poisson_parameters()) {
            log_error("Failed to write poisson parameters to SDRAM");
            rt_error(RTE_SWERR);
        }

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        if (recording_flags > 0) {
            recording_finalise();
        }

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time -= 1;
        simulation_ready_to_read();
        return;
    }

    // Set the next expected time to wait for between spike sending
    expected_time = sv->cpu_clk * timer_period;

    // Loop through spike sources
    for (index_t s = 0; s < globals.n_spike_sources; s++) {
        // If this spike source is active this tick
        spike_source_t *spike_source = &poisson_params[s];

        if (spike_source->is_fast_source) {
            // handle fast spike sources
            handle_fast_source(spike_source, s, timer_count);
        } else {
            // handle slow sources
            handle_slow_source(spike_source, s, timer_count);
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

static void set_spike_source_rate(uint32_t id, REAL rate) {
    if (id < globals.first_source_id) {
        return;
    }
    uint32_t i = id - globals.first_source_id;
    if (i >= globals.n_spike_sources) {
        return;
    }

    log_debug("Setting rate of %u (%u) to %kHz", id, i, rate);
    REAL rate_per_tick = rate * globals.seconds_per_tick;
    if (rate > globals.slow_rate_per_tick_cutoff) {
        poisson_params[i].is_fast_source = true;
        poisson_params[i].exp_minus_lambda = (UFRACT) EXP(-rate_per_tick);
    } else {
        poisson_params[i].is_fast_source = false;
        poisson_params[i].mean_isi_ticks = rate * globals.ticks_per_second;
    }
}

typedef struct spike_source_poisson_sdp_pkt_t {
    uint32_t n_items;
    struct {
        uint32_t id;
        REAL rate;
    } data[];
} spike_source_poisson_sdp_pkt_t;

static void sdp_packet_callback(uint mailbox, uint port) {
    use(port);
    sdp_msg_t *msg = (sdp_msg_t *) mailbox;
    spike_source_poisson_sdp_pkt_t *payload =
            (spike_source_poisson_sdp_pkt_t *) &msg->cmd_rc;

    uint32_t n_items = payload->n_items;
    for (uint32_t item = 0; item < n_items; item++) {
        set_spike_source_rate(payload->data[item].id,
                kbits(payload->data[item].rate));
    }
    spin1_msg_free(msg);
}

static void multicast_packet_callback(uint key, uint payload) {
    uint32_t id = key & globals.set_rate_neuron_id_mask;
    REAL rate = kbits(payload);
    set_spike_source_rate(id, rate);
}

//! The entry point for this model
void c_main(void) {
    // Load DTCM data
    if (!initialize()) {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    spin1_set_timer_tick_and_phase(timer_period, globals.timer_offset);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);
    spin1_callback_on(
            MCPL_PACKET_RECEIVED, multicast_packet_callback, MULTICAST);

    simulation_run();
}
