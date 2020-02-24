/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/*! \file
 *
 * \brief This file contains the main functions for a Poisson spike generator.
 */

#include <common/maths-util.h>

#include <data_specification.h>
#include <recording.h>
#include <debug.h>
#include <random.h>
#include <simulation.h>
#include <spin1_api.h>
#include <bit_field.h>
#include <stdfix-full-iso.h>
#include <limits.h>

#include "profile_tags.h"
#include <profiler.h>

// Declare spin1_wfi
extern void spin1_wfi(void);

// Spin1 API ticks - to know when the timer wraps
extern uint ticks;

//! data structure for Poisson sources
typedef struct spike_source_t {
    uint32_t start_ticks;
    uint32_t end_ticks;
    uint32_t next_ticks;
    uint32_t is_fast_source;

    UFRACT exp_minus_lambda;
    REAL sqrt_lambda;
    uint32_t mean_isi_ticks;
    uint32_t time_to_spike_ticks;
} spike_source_t;

//! \brief data structure for recording spikes
typedef struct timed_out_spikes {
    uint32_t time;
    uint32_t n_buffers;
    uint32_t out_spikes[];
} timed_out_spikes;

//! spike source array region IDs in human readable form
typedef enum region {
    SYSTEM, POISSON_PARAMS, RATES,
    SPIKE_HISTORY_REGION,
    PROVENANCE_REGION,
    PROFILER_REGION
} region;

#define NUMBER_OF_REGIONS_TO_RECORD 1
#define BYTE_TO_WORD_CONVERTER 4
//! A scale factor to allow the use of integers for "inter-spike intervals"
#define ISI_SCALE_FACTOR 1000

typedef enum callback_priorities {
    MULTICAST = -1,
    SDP = 0,
    DMA = 1,
    TIMER = 2
} callback_priorities;

//! Parameters of the SpikeSourcePoisson
typedef struct global_parameters {
    //! True if there is a key to transmit, False otherwise
    uint32_t has_key;
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
    uint32_t ticks_per_second;
    //! The border rate between slow and fast sources
    REAL slow_rate_per_tick_cutoff;
    //! The border rate between fast and faster sources
    REAL fast_rate_per_tick_cutoff;
    //! The ID of the first source relative to the population as a whole
    uint32_t first_source_id;
    //! The number of sources in this sub-population
    uint32_t n_spike_sources;
    //! The seed for the Poisson generation process
    mars_kiss64_seed_t spike_source_seed;
} global_parameters;

//! The global_parameters for the sub-population
static global_parameters params;

typedef struct source_info {
    uint32_t n_rates;
    uint32_t index;
    spike_source_t poissons[];
} source_info;

static source_info **source_data;

static spike_source_t *source;

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

static inline spike_source_t *get_source_data(uint32_t id) {
    return &source_data[id]->poissons[source_data[id]->index];
}

//! \brief Set specific spikes for recording
//! \param[in] n is the spike array index
//! \return bit field at the location n
static inline bit_field_t out_spikes_bitfield(uint32_t n) {
    return &spikes->out_spikes[n * n_spike_buffer_words];
}

//! \brief Reset the spike buffer by clearing the bit field
//! \return None
static inline void reset_spikes(void) {
    spikes->n_buffers = 0;
    for (uint32_t n = n_spike_buffers_allocated; n > 0; n--) {
        clear_bit_field(out_spikes_bitfield(n - 1), n_spike_buffer_words);
    }
}

//! \brief Determines the time in timer ticks multiplied by ISI_SCALE_FACTOR
//!        until the next spike is to occur given the mean inter-spike interval
//! \param[in] mean_inter_spike_interval_in_ticks The mean number of ticks
//!            before a spike is expected to occur in a slow process.
//! \return a uint32_t which represents "time" in timer ticks * ISI_SCALE_FACTOR
//!         until the next spike occurs
static inline uint32_t slow_spike_source_get_time_to_spike(
        uint32_t mean_inter_spike_interval_in_ticks) {
    // Round (dist variate * ISI_SCALE_FACTOR), convert to uint32
    int nbits = 15;
    uint32_t value = (uint32_t) roundk(exponential_dist_variate(
            mars_kiss64_seed, params.spike_source_seed) * ISI_SCALE_FACTOR, nbits);
    // Now multiply by the mean ISI
    uint32_t exp_variate = value * mean_inter_spike_interval_in_ticks;
    // Note that this will be compared to ISI_SCALE_FACTOR in the main loop!
    return exp_variate;
}

//! \brief Determines how many spikes to transmit this timer tick, for a fast source
//! \param[in] exp_minus_lambda exp(-lambda), lambda is amount of spikes expected to be
//!            produced this timer interval (timer tick in real time)
//! \return a uint32_t which represents the number of spikes to transmit
//!         this timer tick
static inline uint32_t fast_spike_source_get_num_spikes(
        UFRACT exp_minus_lambda) {
    // If the value of exp_minus_lambda is very small then it's not worth
    // using the algorithm, so just return 0
    if (bitsulr(exp_minus_lambda) == bitsulr(UFRACT_CONST(0.0))) {
        return 0;
    }
    return poisson_dist_variate_exp_minus_lambda(
            mars_kiss64_seed, params.spike_source_seed, exp_minus_lambda);
}

//! \brief Determines how many spikes to transmit this timer tick, for a faster source
//!        (where lambda is large enough that a Gaussian can be used instead of a Poisson)
//! \param[in] sqrt_lambda Square root of the amount of spikes expected to be produced
//!            this timer interval (timer tick in real time)
//! \return a uint32_t which represents the number of spikes to transmit
//!         this timer tick
static inline uint32_t faster_spike_source_get_num_spikes(
        REAL sqrt_lambda) {
    // First we do x = (inv_gauss_cdf(U(0, 1)) * 0.5) + sqrt(lambda)
    REAL x = (gaussian_dist_variate(mars_kiss64_seed, params.spike_source_seed)
            * REAL_CONST(0.5)) + sqrt_lambda;
    // Then we return int(roundk(x * x))
    int nbits = 15;
    return (uint32_t) roundk(x * x, nbits);
}

#if LOG_LEVEL >= LOG_DEBUG
static void print_spike_source(index_t s) {
    spike_source_t *p = &source[s];
    log_info("atom %d", s);
    log_info("scaled_start = %u", p->start_ticks);
    log_info("scaled end = %u", p->end_ticks);
    log_info("scaled next = %u", p->next_ticks);
    log_info("is_fast_source = %d", p->is_fast_source);
    log_info("exp_minus_lamda = %k", (REAL) p->exp_minus_lambda);
    log_info("isi_val = %k", p->mean_isi_ticks);
    log_info("time_to_spike = %k", p->time_to_spike_ticks);
}

static void print_spike_sources(void) {
    for (index_t s = 0; s < params.n_spike_sources; s++) {
        print_spike_source(s);
    }
}
#endif

//! \brief entry method for reading the global parameters stored in Poisson
//!        parameter region
//! \param[in] address the absolute SDRAm memory address to which the
//!            Poisson parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
static bool read_global_parameters(global_parameters *sdram_globals) {
    log_info("read global_parameters: starting");

    spin1_memcpy(&params, sdram_globals, sizeof(params));

    log_info("\tkey = %08x, set rate mask = %08x, timer offset = %u",
            params.key, params.set_rate_neuron_id_mask, params.timer_offset);
    log_info("\tseed = %u %u %u %u", params.spike_source_seed[0],
            params.spike_source_seed[1],
            params.spike_source_seed[2],
            params.spike_source_seed[3]);

    log_info("\tspike sources = %u, starting at %u",
            params.n_spike_sources, params.first_source_id);
    log_info("seconds_per_tick = %k\n", (REAL) params.seconds_per_tick);
    log_info("ticks_per_second = %k\n", params.ticks_per_second);
    log_info("slow_rate_per_tick_cutoff = %k\n",
            params.slow_rate_per_tick_cutoff);
    log_info("fast_rate_per_tick_cutoff = %k\n",
            params.fast_rate_per_tick_cutoff);

    log_info("read_global_parameters: completed successfully");
    return true;
}

static inline void read_next_rates(uint32_t id) {
    if (source_data[id]->index < source_data[id]->n_rates) {
        source_data[id]->index++;
        spin1_memcpy(&source[id], get_source_data(id), sizeof(spike_source_t));
        if (!source[id].is_fast_source) {
            source[id].time_to_spike_ticks =
                    slow_spike_source_get_time_to_spike(source[id].mean_isi_ticks);
        }
    }
}

//! \brief method for reading the rates of the Poisson
//! \param[in] config the configuration in SDRAM
//! \return a boolean which is True if the rates were read successfully or
//!         False otherwise
static bool read_rates(source_info *sdram_sources) {

    // Allocate DTCM for array of spike sources and copy block of data
    if (params.n_spike_sources > 0) {
        // the first time around, the array is set to NULL, afterwards,
        // assuming all goes well, there's an address here.
        if (source == NULL) {
            source = spin1_malloc(params.n_spike_sources * sizeof(spike_source_t));
            // if failed to alloc memory, report and fail.
            if (source == NULL) {
                log_error("Failed to allocate local sources");
                return false;
            }
            source_data = spin1_malloc(params.n_spike_sources * sizeof(source_info *));
            if (source_data == NULL) {
                log_error("Failed to allocate SDRAM source links");
                return false;
            }

            // Copy the address of each source
            source_info *sdram_source = sdram_sources;
            for (uint32_t i = 0; i < params.n_spike_sources; i++) {
                source_data[i] = sdram_source;
                sdram_source = (source_info *)
                        &(sdram_source->poissons[sdram_source->n_rates]);
            }
        }

        // Put the correct values into the current source information
        for (uint32_t i = 0; i < params.n_spike_sources; i++) {
            spike_source_t *p = &source[i];
            spin1_memcpy(p, get_source_data(i), sizeof(spike_source_t));
            if (!p->is_fast_source && p->time_to_spike_ticks == 0) {
                p->time_to_spike_ticks =
                        slow_spike_source_get_time_to_spike(p->mean_isi_ticks);
            }
        }
    }
    log_info("read_poisson_parameters: completed successfully");
    return true;
}

//! \brief Initialises the recording parts of the model
//! \return True if recording initialisation is successful, false otherwise
static bool initialise_recording(data_specification_metadata_t *ds_regions) {
    // Get the system region
    void *recording_region = data_specification_get_region(
            SPIKE_HISTORY_REGION, ds_regions);

    bool success = recording_initialize(&recording_region, &recording_flags);
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
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(ds_regions)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM, ds_regions),
            APPLICATION_NAME_HASH, &timer_period, &simulation_ticks,
            &infinite_run, &time, SDP, DMA)) {
        return false;
    }
    simulation_set_provenance_data_address(
            data_specification_get_region(PROVENANCE_REGION, ds_regions));

    // setup recording region
    if (!initialise_recording(ds_regions)) {
        return false;
    }

    // Setup regions that specify spike source array data
    if (!read_global_parameters(
            data_specification_get_region(POISSON_PARAMS, ds_regions))) {
        return false;
    }

    if (!read_rates(
            data_specification_get_region(RATES, ds_regions))) {
        return false;
    }

    // print spike sources for debug purposes
#if LOG_LEVEL >= LOG_DEBUG
    print_spike_sources();
#endif

    // Set up recording buffer
    n_spike_buffers_allocated = 0;
    n_spike_buffer_words = get_bit_field_size(params.n_spike_sources);
    spike_buffer_size = n_spike_buffer_words * sizeof(uint32_t);

    // Setup profiler
    profiler_init(
            data_specification_get_region(PROFILER_REGION, ds_regions));

    log_info("Initialise: completed successfully");

    return true;
}

//! \brief runs any functions needed at resume time.
//! \return None
static void resume_callback(void) {
    recording_reset();

    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    // Setup regions that specify spike source array data
    if (!read_global_parameters(
            data_specification_get_region(POISSON_PARAMS, ds_regions))) {
        log_error("failed to reread the Poisson parameters from SDRAM");
        rt_error(RTE_SWERR);
    }

    if (!read_rates(
            data_specification_get_region(RATES, ds_regions))){
        log_error("failed to reread the Poisson rates from SDRAM");
        rt_error(RTE_SWERR);
    }

    // Loop through slow spike sources and initialise 1st time to spike
    for (index_t s = 0; s < params.n_spike_sources; s++) {
        spike_source_t *p = &source[s];
        if (!p->is_fast_source && p->time_to_spike_ticks == 0) {
            p->time_to_spike_ticks =
                    slow_spike_source_get_time_to_spike(p->mean_isi_ticks);
        }
    }

    log_info("Successfully resumed Poisson spike source at time: %u", time);

    // print spike sources for debug purposes
#if LOG_LEVEL >= LOG_DEBUG
    print_spike_sources();
#endif
}

//! \brief stores the Poisson parameters back into SDRAM for reading by the
//! host when needed
//! \return None
static bool store_poisson_parameters(void) {
    log_info("store_parameters: starting");

    // Get the address this core's DTCM data starts at from SRAM
    global_parameters *sdram_globals = data_specification_get_region(
        POISSON_PARAMS, data_specification_get_data_address());

    // Copy the global_parameters back to SDRAM
    spin1_memcpy(sdram_globals, &params, sizeof(params));

    // store spike source parameters into array into SDRAM for reading by
    // the host
    for (uint32_t i = 0; i < params.n_spike_sources; i++) {
        spin1_memcpy(get_source_data(i), &source[i], sizeof(spike_source_t));
    }

    log_info("store_parameters: completed successfully");
    return true;
}

//! \brief handles spreading of Poisson spikes for even packet reception at
//! destination
//! \param[in] spike_key: the key to transmit
//! \return None
static void send_spike(uint32_t spike_key, uint32_t timer_count) {
    // Wait until the expected time to send
    while ((ticks == timer_count) && (tc[T1_COUNT] > expected_time)) {
        // Do Nothing
    }
    expected_time -= params.time_between_spikes;

    // Send the spike
    log_debug("Sending spike packet %x at %d\n", spike_key, time);
    while (!spin1_send_mc_packet(spike_key, 0, NO_PAYLOAD)) {
        spin1_delay_us(1);
    }
}

//! \brief Expand the space for recording spikes.
static inline void expand_spike_recording_buffer(uint32_t n_spikes) {
    uint32_t new_size = 8 + (n_spikes * spike_buffer_size);
    timed_out_spikes *new_spikes = spin1_malloc(new_size);
    if (new_spikes == NULL) {
        log_error("Cannot reallocate spike buffer");
        rt_error(RTE_SWERR);
    }

    // bzero the new buffer
    uint32_t *data = (uint32_t *) new_spikes;
    for (uint32_t n = new_size >> 2; n > 0; n--) {
        data[n - 1] = 0;
    }

    // Copy over old buffer if we have it
    if (spikes != NULL) {
        spin1_memcpy(new_spikes, spikes,
                8 + n_spike_buffers_allocated * spike_buffer_size);
        sark_free(spikes);
    }

    spikes = new_spikes;
    n_spike_buffers_allocated = n_spikes;
}

//! \brief records spikes as needed
//! \param[in] neuron_id: the neurons to store spikes from
//! \param[in] n_spikes: the number of times this neuron has spiked
//!
static inline void mark_spike(uint32_t neuron_id, uint32_t n_spikes) {
    if (recording_flags > 0) {
        if (n_spike_buffers_allocated < n_spikes) {
            expand_spike_recording_buffer(n_spikes);
        }
        if (spikes->n_buffers < n_spikes) {
            spikes->n_buffers = n_spikes;
        }
        for (uint32_t n = n_spikes; n > 0; n--) {
            bit_field_set(out_spikes_bitfield(n - 1), neuron_id);
        }
    }
}

//! \brief callback for completed recording
static void recording_complete_callback(void) {
    recording_in_progress = false;
}

//! \brief writing spikes to SDRAM
//! \param[in] time: the time to which these spikes are being recorded
static inline void record_spikes(uint32_t time) {
    while (recording_in_progress) {
        spin1_wfi();
    }
    if ((spikes != NULL) && (spikes->n_buffers > 0)) {
        recording_in_progress = true;
        spikes->time = time;
        recording_record_and_notify(
                0, spikes, 8 + (spikes->n_buffers * spike_buffer_size),
                recording_complete_callback);
        reset_spikes();
    }
}

//! \brief Handle a fast spike source
static void process_fast_source(
        index_t s_id, spike_source_t *source, uint timer_count) {
    if ((time >= source->start_ticks) && (time < source->end_ticks)) {
        // Get number of spikes to send this tick
        uint32_t num_spikes = 0;

        // If sqrt_lambda has been set then use the Gaussian algorithm for faster sources
        if (REAL_COMPARE(source->sqrt_lambda, >, REAL_CONST(0.0))) {
            profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_PROB_FUNC);
            num_spikes = faster_spike_source_get_num_spikes(source->sqrt_lambda);
            profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_PROB_FUNC);
        } else {
            // Call the fast source Poisson algorithm
            profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_PROB_FUNC);
            num_spikes = fast_spike_source_get_num_spikes(source->exp_minus_lambda);
            profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_PROB_FUNC);
        }

        log_debug("Generating %d spikes", num_spikes);

        // If there are any
        if (num_spikes > 0) {
            // Write spike to out spikes
            mark_spike(s_id, num_spikes);

            // If no key has been given, do not send spikes to fabric
            if (params.has_key) {
                // Send spikes
                const uint32_t spike_key = params.key | s_id;
                for (uint32_t index = 0; index < num_spikes; index++) {
                    send_spike(spike_key, timer_count);
                }
            }
        }
    }
}

//! \brief Handle a slow spike source
static void process_slow_source(
        index_t s_id, spike_source_t *source, uint timer_count) {
    if ((time >= source->start_ticks) && (time < source->end_ticks)
            && (source->mean_isi_ticks != 0)) {
        // Mark a spike while the "timer" is below the scale factor value
        while (source->time_to_spike_ticks < ISI_SCALE_FACTOR) {
            // Write spike to out_spikes
            mark_spike(s_id, 1);

            // if no key has been given, do not send spike to fabric.
            if (params.has_key) {
                // Send package
                send_spike(params.key | s_id, timer_count);
            }

            // Update time to spike (note, this might not get us back above
            // the scale factor, particularly if the mean_isi is smaller)
            profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_PROB_FUNC);
            source->time_to_spike_ticks +=
                    slow_spike_source_get_time_to_spike(source->mean_isi_ticks);
            profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_PROB_FUNC);
        }

        // Now we have finished for this tick, subtract the scale factor
        source->time_to_spike_ticks -= ISI_SCALE_FACTOR;
    }
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

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

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

        profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        if (recording_flags > 0) {
            recording_finalise();
        }

        profiler_finalise();

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;
        simulation_ready_to_read();
        return;
    }

    // Set the next expected time to wait for between spike sending
    expected_time = sv->cpu_clk * timer_period;

    // Loop through spike sources
    for (index_t s_id = 0; s_id < params.n_spike_sources; s_id++) {
        // If this spike source is active this tick
        spike_source_t *spike_source = &source[s_id];
        if (spike_source->is_fast_source) {
            process_fast_source(s_id, spike_source, timer_count);
        } else {
            process_slow_source(s_id, spike_source, timer_count);
        }

        if ((time + 1) >= spike_source->next_ticks) {
            log_debug("Moving to next rate at time %d", time);
            read_next_rates(s_id);
#if LOG_LEVEL >= LOG_DEBUG
            // print_spike_source(s_id);
#endif
        }
    }

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

    // Record output spikes if required
    if (recording_flags > 0) {
        record_spikes(time);
        recording_do_timestep_update(time);
    }
}

//! \brief set the spike source rate as required
//! \param[in] id, the ID of the source to be updated
//! \param[in] rate, the REAL-valued rate in Hz, to be multiplied
//!            to get per_tick values
void set_spike_source_rate(uint32_t id, REAL rate) {
    if ((id < params.first_source_id) ||
            (id - params.first_source_id >= params.n_spike_sources)) {
        return;
    }

    uint32_t sub_id = id - params.first_source_id;
    REAL rate_per_tick = rate * params.seconds_per_tick;
    log_debug("Setting rate of %u (%u) to %kHz (%k per tick)",
            id, sub_id, rate, rate_per_tick);
    spike_source_t *spike_source = &source[sub_id];

    if (rate_per_tick >= params.slow_rate_per_tick_cutoff) {
        spike_source->is_fast_source = true;
        if (rate_per_tick >= params.fast_rate_per_tick_cutoff) {
            spike_source->sqrt_lambda = SQRT(rate_per_tick);
            // warning: sqrtk is untested...
        } else {
            spike_source->exp_minus_lambda = (UFRACT) EXP(-rate_per_tick);
            spike_source->sqrt_lambda = REAL_CONST(0.0);
        }
    } else if (rate_per_tick == 0) {
        spike_source->is_fast_source = false;
        spike_source->mean_isi_ticks = 0;
        spike_source->time_to_spike_ticks = 0;
    } else {
        spike_source->is_fast_source = false;
        spike_source->mean_isi_ticks =
                (uint32_t) (REAL_CONST(1.0) / rate_per_tick);
        spike_source->time_to_spike_ticks =
                slow_spike_source_get_time_to_spike(spike_source->mean_isi_ticks);
    }
}

//! multicast callback used to set rate when injected in a live example
static void multicast_packet_callback(uint key, uint payload) {
    uint32_t id = key & params.set_rate_neuron_id_mask;
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
    spin1_set_timer_tick_and_phase(timer_period, params.timer_offset);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);
    spin1_callback_on(
            MCPL_PACKET_RECEIVED, multicast_packet_callback, MULTICAST);

    simulation_run();
}
