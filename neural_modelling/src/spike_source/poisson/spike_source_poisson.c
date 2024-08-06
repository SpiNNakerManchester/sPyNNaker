/*
 * Copyright (c) 2014 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*!
 * \dir
 * \brief Implementation of the Poisson spike source
 * \file
 * \brief This file contains the main functions for a Poisson spike generator.
 */

#include <common/maths-util.h>
#include <common/send_mc.h>
#include <data_specification.h>
#include <recording.h>
#include <debug.h>
#include <normal.h>
#include <simulation.h>
#include <spin1_api.h>
#include <bit_field.h>
#include <stdfix-full-iso.h>
#include <limits.h>
#include <circular_buffer.h>

#include "profile_tags.h"
#include <profiler.h>
#include <wfi.h>

#ifndef UNUSED
#define UNUSED __attribute__((__unused__))
#endif

// ----------------------------------------------------------------------

#define END_OF_TIME 0xFFFFFFFF

//! data structure for Poisson sources
typedef struct spike_source_t {
    //! When the current control regime starts, in timer ticks
    uint32_t start_ticks;
    //! When the current control regime ends, in timer ticks
    uint32_t end_ticks;
    //! When we should load the next control regime, in timer ticks
    uint32_t next_ticks;
    //! Flag for whether we're in fast or slow mode
    uint32_t is_fast_source;

    //! exp(-&lambda;)
    UFRACT exp_minus_lambda;
    //! sqrt(&lambda;)
    REAL sqrt_lambda;
    //! Mean interspike interval, in ticks
    uint32_t mean_isi_ticks;
    //! Planned time to spike, in ticks
    uint32_t time_to_spike_ticks;
} spike_source_t;

//! \brief data structure for recording spikes
typedef struct timed_out_spikes {
    //! Time of recording
    uint32_t time;
    //! Number of spike-recording buffers
    uint32_t n_buffers;
    //! Spike recording buffers; sort of a bit_field_t[]
    uint32_t out_spikes[];
} timed_out_spikes;

//! spike source array region IDs in human readable form
typedef enum region {
    SYSTEM,               //!< simulation interface master control
    POISSON_PARAMS,       //!< application configuration; global_parameters
    RATES,                //!< rates to apply; source_info
    SPIKE_HISTORY_REGION, //!< spike history recording region
    PROVENANCE_REGION,    //!< provenance region
    PROFILER_REGION,      //!< profiling region
    SDRAM_PARAMS_REGION,  //!< SDRAM transfer parameters region
    EXPANDER_REGION       //!< Expanding of parameters
} region;

//! The number of recording regions
#define NUMBER_OF_REGIONS_TO_RECORD 1
//! Bytes per word
#define BYTE_TO_WORD_CONVERTER 4
//! A scale factor to allow the use of integers for "inter-spike intervals"
#define ISI_SCALE_FACTOR 1000

//! Priorities for interrupt handlers
typedef enum ssp_callback_priorities {
    //! Multicast packet reception uses the FIQ
    MULTICAST = -1,
    //! SDP handling is highest ordinary priority
    SDP = 0,
    //! DMA complete handling is medium priority
    DMA = 1,
    //! Regular timer interrupt is lowest priority
    TIMER = 2
} callback_priorities;

//! An RNG seed of 4 words
typedef struct {
    uint32_t x;
    uint32_t y;
    uint32_t z;
    uint32_t c;
} rng_seed_t;

//! Parameters of the SpikeSourcePoisson
typedef struct global_parameters {
    //! True if there is a key to transmit, False otherwise
    uint32_t has_key;
    //! The mask to work out the neuron ID when setting the rate
    uint32_t set_rate_neuron_id_mask;
    //! The time between ticks in seconds for setting the rate
    UFRACT seconds_per_tick;
    //! The number of ticks per millisecond for setting the start and duration
    UREAL ticks_per_ms;
    //! The border rate between slow and fast sources
    REAL slow_rate_per_tick_cutoff;
    //! The border rate between fast and faster sources
    REAL fast_rate_per_tick_cutoff;
    //! The ID of the first source relative to the population as a whole
    uint32_t first_source_id;
    //! The number of sources in this sub-population
    uint32_t n_spike_sources;
    //! Maximum expected spikes per tick (for recording)
    uint32_t max_spikes_per_tick;
    //! Number of bits to use for colour
    uint32_t n_colour_bits;
    //! The seed for the Poisson generation process
    rng_seed_t spike_source_seed;
} global_parameters;

//! Structure of the provenance data
struct poisson_extension_provenance {
    //! number of times the tdma fell behind its slot
    uint32_t times_tdma_fell_behind;
};

__attribute__((aligned(4)))
typedef struct source_details {
    unsigned long accum rate;
    unsigned long accum start;
    unsigned long accum duration;
} source_details;

//! The keys to send spikes with
static uint32_t *keys;

//! Collection of rates to apply over time to a particular spike source
typedef struct source_info {
    //! The number of rates
    uint32_t n_rates;
    //! Where in the array of rate descriptors we are
    uint32_t index;
    //! Array of rates
    source_details details[];
} source_info;

typedef struct source_expand_details {
    //! The number of items to expand
    uint32_t count;
    //! The details for the given number of items
    source_info info;
} source_expand_details;

typedef struct source_expand_region {
    //! Determine if any rates have been changed
    uint32_t rate_changed;
    // The number of expander items in the region
    uint32_t n_items;
    // The expander items.  Because each of these are dynamic they have to be
    // implied here.
    source_expand_details items[];
} source_expand_region;

//! A region of SDRAM used to transfer synapses
struct sdram_config {
    //! The address of the input data to be transferred
    uint32_t *address;
    //! The size of the input data to be transferred
    uint32_t size_in_bytes;
    //! The offset into the data to write the weights (to account for different
    //! synapse types)
    uint32_t offset;
    //! The weight to send for each active Poisson source
    uint16_t weights[];
};


//! The global_parameters for the sub-population
static global_parameters ssp_params;

//! Array of pointers to sequences of rate data
static source_info **source_data;

//! The currently applied rate descriptors
static spike_source_t *source;

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

//! The timer period
static uint32_t timer_period;

//! Where synaptic input is to be written
static struct sdram_config *sdram_inputs;

//! The inputs to be sent at the end of this timestep
static uint16_t *input_this_timestep;

//! The timesteps per second
static UREAL ts_per_second;

//! Buffer for rate change packets
static circular_buffer rate_change_buffer;

//! The colour of the current time step
static uint32_t colour;

//! The mask to apply to the time to get the colour
static uint32_t colour_mask;

//! \brief Random number generation for the Poisson sources.
//!        This is a local version for speed of operation.
//! \return A random number
static inline uint32_t rng(void) {
    ssp_params.spike_source_seed.x = 314527869 * ssp_params.spike_source_seed.x + 1234567;
    ssp_params.spike_source_seed.y ^= ssp_params.spike_source_seed.y << 5;
    ssp_params.spike_source_seed.y ^= ssp_params.spike_source_seed.y >> 7;
    ssp_params.spike_source_seed.y ^= ssp_params.spike_source_seed.y << 22;
    uint64_t t = 4294584393ULL * ssp_params.spike_source_seed.z + ssp_params.spike_source_seed.c;
    ssp_params.spike_source_seed.c = t >> 32;
    ssp_params.spike_source_seed.z = t;

    return (uint32_t) ssp_params.spike_source_seed.x
            + ssp_params.spike_source_seed.y + ssp_params.spike_source_seed.z;
}

//! \brief How many spikes to generate for a fast Poisson source
//! \param[in] exp_minus_lambda e^(-mean_rate)
//! \return How many spikes to generate
static inline uint32_t n_spikes_poisson_fast(UFRACT exp_minus_lambda) {
    UFRACT p = UFRACT_CONST(1.0);
    uint32_t k = 0;

    do {
        k++;
        //  p = p * ulrbits(uni_rng(seed_arg));
        // Possibly faster multiplication by using DRL's routines
        p = ulrbits(__stdfix_smul_ulr(bitsulr(p), rng()));
    } while (bitsulr(p) > bitsulr(exp_minus_lambda));
    return k - 1;
}

//! \brief How many time steps until the next spike for a slow Poisson source
//! \return The number of time steps until the next spike
static inline REAL n_steps_until_next(void) {
    REAL A = REAL_CONST(0.0);
    uint32_t U, U0, USTAR;

    while (true) {
        U = rng();
        U0 = U;

        do {
            USTAR = rng();
            if (U < USTAR) {
                return A + (REAL) ulrbits(U0);
            }

            U = rng();
        } while (U < USTAR);

        A += 1.0k;
    }
}


//! \brief Determine the time in timer ticks multiplied by ISI_SCALE_FACTOR
//!     until the next spike is to occur given the mean inter-spike interval
//! \param[in] mean_inter_spike_interval_in_ticks: The mean number of ticks
//!     before a spike is expected to occur in a slow process.
//! \return "time" in timer ticks * ISI_SCALE_FACTOR until the next spike occurs
static inline uint32_t slow_spike_source_get_time_to_spike(
        uint32_t mean_inter_spike_interval_in_ticks) {
    // Round (dist variate * ISI_SCALE_FACTOR), convert to uint32
    uint32_t value = (uint32_t) roundk(
            n_steps_until_next() * ISI_SCALE_FACTOR, (15));
    // Now multiply by the mean ISI
    uint32_t exp_variate = value * mean_inter_spike_interval_in_ticks;
    // Note that this will be compared to ISI_SCALE_FACTOR in the main loop!
    return exp_variate;
}

//! \brief Determine how many spikes to transmit this timer tick, for a fast
//!     source
//! \param[in] exp_minus_lambda: exp(-&lambda;), &lambda; is amount of spikes
//!     expected to be produced this timer interval (timer tick in real time)
//! \return the number of spikes to transmit this timer tick
static inline uint32_t fast_spike_source_get_num_spikes(
        UFRACT exp_minus_lambda) {
    // If the value of exp_minus_lambda is very small then it's not worth
    // using the algorithm, so just return 0
    if (bitsulr(exp_minus_lambda) == bitsulr(UFRACT_CONST(0.0))) {
        return 0;
    }
    return n_spikes_poisson_fast(exp_minus_lambda);
}

//! \brief Determine how many spikes to transmit this timer tick, for a faster
//!     source (where &lambda; is large enough that a Gaussian can be used
//!     instead of a Poisson)
//! \param[in] sqrt_lambda: Square root of the amount of spikes expected to be
//!     produced this timer interval (timer tick in real time)
//! \return The number of spikes to transmit this timer tick
static inline uint32_t faster_spike_source_get_num_spikes(
        REAL sqrt_lambda) {
    // First we do x = (inv_gauss_cdf(U(0, 1)) * 0.5) + sqrt(lambda)
    uint32_t U = rng();
    REAL x = (norminv_urt(U) * HALF) + sqrt_lambda;
    // Then we return int(roundk(x * x))
    return (uint32_t) roundk(x * x, 15);
}

//! \brief Set the spike source rate as required
//! \param[in] id: the ID of the source to be updated
//! \param[in] rate:
//!     the rate in Hz, to be multiplied to get per-tick values
void set_spike_source_rate(uint32_t sub_id, UREAL rate) {

    // This is an U1616 * U032 which means the result in U1616 is shifted by 32,
	// but in S1615 (required later) is shifted by 33 to account for the sign
    REAL rate_per_tick = kbits(
            (__U64(bitsuk(rate)) * __U64(bitsulr(ssp_params.seconds_per_tick))) >> 33);
    log_info("Setting rate of %u to %KHz (%k per tick)",
            sub_id, rate, rate_per_tick);
    spike_source_t *spike_source = &source[sub_id];

    if (rate_per_tick >= ssp_params.slow_rate_per_tick_cutoff) {
        spike_source->is_fast_source = 1;
        spike_source->mean_isi_ticks = 0;
        spike_source->time_to_spike_ticks = 0;
        if (rate_per_tick >= ssp_params.fast_rate_per_tick_cutoff) {
            spike_source->sqrt_lambda = SQRT(rate_per_tick);
            spike_source->exp_minus_lambda = UFRACT_CONST(0);
        } else {
            spike_source->exp_minus_lambda = (UFRACT) EXP(-rate_per_tick);
            spike_source->sqrt_lambda = ZERO;
        }
    } else {
        if (rate > 0) {
            spike_source->mean_isi_ticks =
                (uint32_t) ((bitsulk((unsigned long accum) ts_per_second)) / bitsulk(rate));
        } else {
            spike_source->mean_isi_ticks = 0;
        }

        spike_source->exp_minus_lambda = UFRACT_CONST(0);
        spike_source->sqrt_lambda = ZERO;
        spike_source->is_fast_source = 0;
        spike_source->time_to_spike_ticks =
                slow_spike_source_get_time_to_spike(spike_source->mean_isi_ticks);
    }
}

// ----------------------------------------------------------------------

//! \brief Writes the provenance data
//! \param[out] provenance_region: Where to write the provenance
static void store_provenance_data(address_t provenance_region) {
    log_debug("writing other provenance data");
    struct poisson_extension_provenance *prov = (void *) provenance_region;

    // store the data into the provenance data region
    prov->times_tdma_fell_behind = 0;
    log_debug("finished other provenance data");
}

static inline uint32_t ms_to_ticks(unsigned long accum ms) {
    return (uint32_t) ((ms * ssp_params.ticks_per_ms) + 0.5k);
}

static inline void set_spike_source_details(uint32_t id, bool rate_changed) {
    uint32_t index = source_data[id]->index;
    log_debug("Source %u is at index %u", id, index);
    source_details details = source_data[id]->details[index];
    if (rate_changed) {
        log_debug("Setting rate of %u to %k at %u", id, (s1615) details.rate, time);
        set_spike_source_rate(id, details.rate);
    }
    spike_source_t *p = &(source[id]);
    p->start_ticks = ms_to_ticks(details.start);
    log_debug("Start of %u is %u", id, p->start_ticks);
    if (details.duration == END_OF_TIME) {
        log_debug("Duration of %u is forever", id);
        p->end_ticks = END_OF_TIME;
    } else {
        uint32_t duration_ticks = ms_to_ticks(details.duration);
        p->end_ticks = p->start_ticks + duration_ticks;
        log_debug("Duration of %u is %u, end = %u", id, duration_ticks, p->end_ticks);
    }
    if ((index + 1) >= source_data[id]->n_rates) {
        log_debug("Next of %u never happens", id);
        p->next_ticks = END_OF_TIME;
    } else {
        accum next_start = source_data[id]->details[index + 1].start;
        p->next_ticks = ms_to_ticks(next_start);
        log_debug("Next of %u at %u", id, p->next_ticks);
    }
}

//! \brief Set specific spikes for recording
//! \param[in] n: the spike array index
//! \return bit field at the location n
static inline bit_field_t out_spikes_bitfield(uint32_t n) {
    return &spikes->out_spikes[n * n_spike_buffer_words];
}

//! \brief Reset the spike buffer by clearing the bit field
static inline void reset_spikes(void) {
    spikes->n_buffers = 0;
    for (uint32_t n = n_spike_buffers_allocated; n > 0; n--) {
        clear_bit_field(out_spikes_bitfield(n - 1), n_spike_buffer_words);
    }
}


#if LOG_LEVEL >= LOG_DEBUG
//! \brief Print a spike source
//! \param[in] s: The spike source ID
static void print_spike_source(index_t s) {
    spike_source_t *p = &source[s];
    log_info("atom %d", s);
    log_info("scaled_start = %u", p->start_ticks);
    log_info("scaled end = %u", p->end_ticks);
    log_info("scaled next = %u", p->next_ticks);
    log_info("is_fast_source = %d", p->is_fast_source);
    log_info("exp_minus_lambda = %k", (REAL) p->exp_minus_lambda);
    log_info("sqrt_lambda = %k", p->sqrt_lambda);
    log_info("isi_val = %u", p->mean_isi_ticks);
    log_info("time_to_spike = %u", p->time_to_spike_ticks);
}

//! Print all spike sources
static void print_spike_sources(void) {
    for (index_t s = 0; s < ssp_params.n_spike_sources; s++) {
        print_spike_source(s);
    }
}
#endif

//! \brief Read the global parameters stored in Poisson parameter region.
//! \param[in] sdram_globals: the absolute SDRAM memory address to which the
//!            Poisson parameter region starts.
//! \return Whether the parameters were read successfully.
static bool read_global_parameters(global_parameters *sdram_globals) {
    log_info("read global_parameters: starting");
    ssp_params = *sdram_globals;
    ts_per_second = ukbits(1000 * bitsuk(ssp_params.ticks_per_ms));

    uint32_t keys_size = sizeof(uint32_t) * ssp_params.n_spike_sources;
    keys = spin1_malloc(keys_size);
    if (keys == NULL) {
        log_error("Couldn't allocate space %u for %u keys",
                keys_size, ssp_params.n_spike_sources);
    }
    spin1_memcpy(keys, &(sdram_globals[1]), keys_size);

    colour_mask = (1 << ssp_params.n_colour_bits) - 1;

    log_info("\tset rate mask = %08x",
            ssp_params.set_rate_neuron_id_mask);
    log_info("\tseed = %u %u %u %u", ssp_params.spike_source_seed.c,
            ssp_params.spike_source_seed.x,
            ssp_params.spike_source_seed.y,
            ssp_params.spike_source_seed.z);

    log_info("\tspike sources = %u, starting at %u",
            ssp_params.n_spike_sources, ssp_params.first_source_id);
    log_info("seconds_per_tick = %K", (UREAL) ssp_params.seconds_per_tick);
    log_info("ticks_per_ms = %K", ssp_params.ticks_per_ms);
    log_info("ts_per_second = %K", ts_per_second);
    log_info("slow_rate_per_tick_cutoff = %K",
            ssp_params.slow_rate_per_tick_cutoff);
    log_info("fast_rate_per_tick_cutoff = %K",
            ssp_params.fast_rate_per_tick_cutoff);
#if LOG_LEVEL >= LOG_DEBUG
    for (uint32_t i = 0; i < ssp_params.n_spike_sources; i++) {
        log_debug("Key %u: 0x%08x", i, keys[i]);
    }
#endif

    log_info("read_global_parameters: completed successfully");
    return true;
}

//! \brief Get the next chunk of rates read
//! \param[in] id: The spike source ID
static inline void read_next_rates(uint32_t id) {
    if (source_data[id]->index < source_data[id]->n_rates) {
        source_data[id]->index++;
        set_spike_source_details(id, true);
    }
}

//! \brief Read the rates of the Poisson.
//! \param[in] sdram_sources: the configuration in SDRAM
//! \param[in] rate_changed: whether any rates have actually changed
//! \param[in] next_time: the time which will be the next timestep to run
//! \return Whether the rates were read successfully.
static bool read_rates(source_info *sdram_sources, bool rate_changed, uint32_t next_time) {
    // Allocate DTCM for array of spike sources and copy block of data
    if (ssp_params.n_spike_sources > 0) {
        // the first time around, the array is set to NULL, afterwards,
        // assuming all goes well, there's an address here.
        if (source == NULL) {
            source = spin1_malloc(
                    ssp_params.n_spike_sources * sizeof(spike_source_t));
            // if failed to alloc memory, report and fail.
            if (source == NULL) {
                log_error("Failed to allocate local sources");
                return false;
            }
            source_data = spin1_malloc(
                    ssp_params.n_spike_sources * sizeof(source_info *));
            if (source_data == NULL) {
                log_error("Failed to allocate SDRAM source links");
                return false;
            }

            // Copy the address of each source
            source_info *sdram_source = sdram_sources;
            for (uint32_t i = 0; i < ssp_params.n_spike_sources; i++) {
                source_data[i] = sdram_source;
                sdram_source = (source_info *)
                        &sdram_source->details[sdram_source->n_rates];
            }
        }

        // Put the correct values into the current source information
        for (uint32_t i = 0; i < ssp_params.n_spike_sources; i++) {

            // Find the index for the current time
            uint32_t index = 0;
            uint32_t n_rates = source_data[i]->n_rates;
            while ((index + 1) < n_rates
                    && next_time >= ms_to_ticks(source_data[i]->details[index + 1].start)) {
                index++;
            }
            bool new_index = source_data[i]->index != index;
            source_data[i]->index = index;
            set_spike_source_details(i, rate_changed || new_index);
        }
    }
    log_info("read_poisson_parameters: completed successfully");
    return true;
}

static bool expand_rates(source_expand_region *items, source_info *sdram_sources) {

	if (!items->rate_changed) {
		return false;
	}

    // We need a pointer here as each item is dynamically sized.  This pointer
    // will be updated each time with the start of the next item to be read
    source_expand_details *item = &(items->items[0]);

    // Similarly, we need a pointer for the current SDRAM source
    source_info *source = &(sdram_sources[0]);

    // Go though each expander item, which says how many times to repeat
    for (uint32_t i = 0; i < items->n_items; i++) {

        // Copy SDRAM data to local
        uint32_t n_rates = item->info.n_rates;
        log_debug("Reading %u rates", n_rates);
        source_details details[n_rates];
        for (uint32_t k = 0; k < n_rates; k++) {
            details[k] = item->info.details[k];
            log_debug("Repeating rate %k %u times",
                    (accum) details[k].rate, item->count);
        }

        // Repeat the same thing this many times
        for (uint32_t j = 0; j < item->count; j++) {
            source->n_rates = n_rates;
            source->index = 0;
            for (uint32_t k = 0; k < n_rates; k++) {
                source->details[k] = details[k];
            }

            // Update the source point to just after the last item written
            source = (source_info *) &(source->details[n_rates]);
        }

        // Update the item pointer to just after the last item read
        item = (source_expand_details *) &(item->info.details[n_rates]);
    }

    items->rate_changed = false;
    return true;
}

//! \brief Initialise the recording parts of the model.
//! \param[in] ds_regions: Data specification master descriptor
//! \return Whether recording initialisation is successful
static bool initialise_recording(data_specification_metadata_t *ds_regions) {
    // Get the system region
    void *recording_region = data_specification_get_region(
            SPIKE_HISTORY_REGION, ds_regions);

    bool success = recording_initialize(&recording_region, &recording_flags);
    log_info("Recording flags = 0x%08x", recording_flags);

    return success;
}

//! \brief Expand the space for recording spikes.
//! \param[in] n_spikes: New number of spikes to hold
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

//! \brief Initialise the model by reading in the regions and checking
//!     recording data.
//! \return Whether it successfully read all the regions and set up
//!     all its internal data structures.
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

    simulation_set_provenance_function(
            store_provenance_data,
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

    void *rates_region = data_specification_get_region(RATES, ds_regions);
    bool rates_changed = expand_rates(
            data_specification_get_region(EXPANDER_REGION, ds_regions),
            rates_region);
    if (!read_rates(rates_region, rates_changed, 0)) {
        return false;
    }

    // print spike sources for debug purposes
#if LOG_LEVEL >= LOG_DEBUG
    print_spike_sources();
#endif

    // Set up recording buffer
    n_spike_buffers_allocated = 0;
    n_spike_buffer_words = get_bit_field_size(ssp_params.n_spike_sources);
    spike_buffer_size = n_spike_buffer_words * sizeof(uint32_t);
    expand_spike_recording_buffer(ssp_params.max_spikes_per_tick);

    // Setup profiler
    profiler_init(
            data_specification_get_region(PROFILER_REGION, ds_regions));

    // Setup SDRAM transfer
    struct sdram_config *sdram_conf = data_specification_get_region(
            SDRAM_PARAMS_REGION, ds_regions);
    uint32_t sdram_inputs_size = sizeof(struct sdram_config) + (
            ssp_params.n_spike_sources * sizeof(uint16_t));
    sdram_inputs = spin1_malloc(sdram_inputs_size);
    if (sdram_inputs == NULL) {
        log_error("Could not allocate %d bytes for SDRAM inputs",
                sdram_inputs_size);
        return false;
    }
    spin1_memcpy(sdram_inputs, sdram_conf, sdram_inputs_size);
    log_info("Writing output to address 0x%08x, size in total %d,"
             "offset in half-words %d, size to write %d", sdram_inputs->address,
             sdram_inputs->size_in_bytes, sdram_inputs->offset,
             ssp_params.n_spike_sources * sizeof(uint16_t));
    if (sdram_inputs->size_in_bytes != 0) {
        input_this_timestep = spin1_malloc(sdram_inputs->size_in_bytes);
        if (input_this_timestep == NULL) {
            log_error("Could not allocate %d bytes for input this timestep",
                    sdram_inputs->size_in_bytes);
            return false;
        }
        sark_word_set(input_this_timestep, 0, sdram_inputs->size_in_bytes);
        for (uint32_t i = 0; i < ssp_params.n_spike_sources; i++) {
            log_debug("weight[%u] = %u", i, sdram_inputs->weights[i]);
        }
    }

    // Allocate buffer to allow rate change (2 ints) per source
    rate_change_buffer = circular_buffer_initialize(
    		(ssp_params.n_spike_sources * 2) + 1);
    if (rate_change_buffer == NULL) {
    	log_error("Could not allocate rate change buffer!");
    	return false;
    }

    log_info("Initialise: completed successfully");

    return true;
}

//! \brief Run any functions needed at resume time.
static void resume_callback(void) {
    recording_reset();

    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    // If we are resetting, re-read the seed
    bool rates_changed = false;
    if (time == UINT32_MAX) {
    	if (!read_global_parameters(data_specification_get_region(
    			POISSON_PARAMS, ds_regions))) {
    		log_error("failed to reread the Poisson params");
    		rt_error(RTE_SWERR);
    	}
    	rates_changed = true;
    }

    void *rates_region = data_specification_get_region(RATES, ds_regions);
    bool expand_rates_changed = expand_rates(
            data_specification_get_region(EXPANDER_REGION, ds_regions),
            rates_region);
    rates_changed = rates_changed || expand_rates_changed;

    if (!read_rates(rates_region, rates_changed, time + 1)) {
        log_error("failed to reread the Poisson rates from SDRAM");
        rt_error(RTE_SWERR);
    }

    log_info("Successfully resumed Poisson spike source at time: %u", time);

    // print spike sources for debug purposes
#if LOG_LEVEL >= LOG_DEBUG
    print_spike_sources();
#endif
}

//! \brief records spikes as needed
//! \param[in] neuron_id: the neurons to store spikes from
//! \param[in] n_spikes: the number of times this neuron has spiked
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

//! \brief writing spikes to SDRAM
//! \param[in] time: the time to which these spikes are being recorded
static inline void record_spikes(uint32_t time) {
    if ((spikes != NULL) && (spikes->n_buffers > 0)) {
        spikes->time = time;
        recording_record(0, spikes, 8 + (spikes->n_buffers * spike_buffer_size));
        reset_spikes();
    }
}

//! \brief Handle a fast spike source
//! \param s_id: Source ID
//! \param source: Source descriptor
static void process_fast_source(index_t s_id, spike_source_t *source) {
    if ((time >= source->start_ticks) && (time < source->end_ticks)) {
        // Get number of spikes to send this tick
        uint32_t num_spikes = 0;

        // If sqrt_lambda has been set then use the Gaussian algorithm for
        // faster sources
        if (REAL_COMPARE(source->sqrt_lambda, >, ZERO)) {
            profiler_write_entry_disable_irq_fiq(
                    PROFILER_ENTER | PROFILER_PROB_FUNC);
            num_spikes = faster_spike_source_get_num_spikes(
                    source->sqrt_lambda);
            profiler_write_entry_disable_irq_fiq(
                    PROFILER_EXIT | PROFILER_PROB_FUNC);
        } else {
            // Call the fast source Poisson algorithm
            profiler_write_entry_disable_irq_fiq(
                    PROFILER_ENTER | PROFILER_PROB_FUNC);
            num_spikes = fast_spike_source_get_num_spikes(
                    source->exp_minus_lambda);
            profiler_write_entry_disable_irq_fiq(
                    PROFILER_EXIT | PROFILER_PROB_FUNC);
        }

        log_debug("Generating %d spikes", num_spikes);

        // If there are any
        if (num_spikes > 0) {
            // Write spike to out spikes
            mark_spike(s_id, num_spikes);

            // If no key has been given, do not send spikes to fabric
            if (ssp_params.has_key) {
                // Send spikes
                const uint32_t spike_key = keys[s_id] | colour;
                send_spike_mc_payload(spike_key, num_spikes);
            } else if (sdram_inputs->address != 0) {
                input_this_timestep[sdram_inputs->offset + s_id] +=
                     sdram_inputs->weights[s_id] * num_spikes;
            }
        }
    }
}

//! \brief Handle a slow spike source
//! \param s_id: Source ID
//! \param source: Source descriptor
static void process_slow_source(index_t s_id, spike_source_t *source) {
    if ((time >= source->start_ticks) && (time < source->end_ticks)
            && (source->mean_isi_ticks != 0)) {
        uint32_t count = 0;
        // Mark a spike while the "timer" is below the scale factor value
        while (source->time_to_spike_ticks < ISI_SCALE_FACTOR) {
            count++;

            // Update time to spike (note, this might not get us back above
            // the scale factor, particularly if the mean_isi is smaller)
            profiler_write_entry_disable_irq_fiq(
                    PROFILER_ENTER | PROFILER_PROB_FUNC);
            source->time_to_spike_ticks +=
                    slow_spike_source_get_time_to_spike(source->mean_isi_ticks);
            profiler_write_entry_disable_irq_fiq(
                    PROFILER_EXIT | PROFILER_PROB_FUNC);
        }
        if (count) {
            // Write spike to out_spikes
            mark_spike(s_id, count);

            // if no key has been given, do not send spike to fabric.
            if (ssp_params.has_key) {
                // Send package
                const uint32_t spike_key = keys[s_id] | colour;
                send_spike_mc_payload(spike_key, count);
            } else if (sdram_inputs->address != 0) {
                input_this_timestep[sdram_inputs->offset + s_id] +=
                    sdram_inputs->weights[s_id] * count;
            }
        }

        // Now we have finished for this tick, subtract the scale factor
        source->time_to_spike_ticks -= ISI_SCALE_FACTOR;
    }
}

//! \brief Timer interrupt callback
//! \param[in] timer_count: the number of times this call back has been
//!     executed since start of simulation
//! \param[in] unused: for consistency sake of the API always returning two
//!     parameters, this parameter has no semantics currently and thus
//!     is set to 0
static void timer_callback(UNUSED uint timer_count, UNUSED uint unused) {
    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    time++;

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (simulation_is_finished()) {
        // go into pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

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

    // Set the colour for the time step
    colour = time & colour_mask;

    // Do any rate changes
    while (circular_buffer_size(rate_change_buffer) >= 2) {
    	uint32_t id = 0;
    	UREAL rate = 0.0k;
    	circular_buffer_get_next(rate_change_buffer, &id);
    	circular_buffer_get_next(rate_change_buffer, (uint32_t *) &rate);
        set_spike_source_rate(id, rate);
    }

    // Reset the inputs this timestep if using them
    if (sdram_inputs->address != 0) {
        sark_word_set(input_this_timestep, 0, sdram_inputs->size_in_bytes);
    }

    // Loop through spike sources and see if they need updating
    // NOTE: This full loop needs to happen first with processing in a second
    // separate loop.  This is to ensure that the random generator use matches
    // between a single run and a split run (as slow sources can produce
    // multiple spikes in a single time step).
    for (index_t s_id = 0; s_id < ssp_params.n_spike_sources; s_id++) {
        spike_source_t *spike_source = &source[s_id];

        // Move to the next tick now if needed
        if (time >= spike_source->next_ticks) {
            log_debug("Moving to next rate at time %d", time);
            read_next_rates(s_id);
#if LOG_LEVEL >= LOG_DEBUG
            print_spike_source(s_id);
#endif
        }
    }

    // Loop through the sources and process them
    for (index_t s_id = 0; s_id < ssp_params.n_spike_sources; s_id++) {
        spike_source_t *spike_source = &source[s_id];
        if (spike_source->is_fast_source) {
            process_fast_source(s_id, spike_source);
        } else {
            process_slow_source(s_id, spike_source);
        }
    }

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

    // If transferring over SDRAM, transfer now
    if (sdram_inputs->address != 0) {
        spin1_dma_transfer(0, sdram_inputs->address, input_this_timestep,
                DMA_WRITE, sdram_inputs->size_in_bytes);
    }

    // Record output spikes if required
    if (recording_flags > 0) {
        record_spikes(time);
    }
}

//! \brief Multicast callback used to set rate when injected in a live example
//! \param[in] key: Received multicast key
//! \param[in] payload: Received multicast payload
static void multicast_packet_callback(uint key, uint payload) {
    uint32_t id = key & ssp_params.set_rate_neuron_id_mask;
    if ((id < ssp_params.first_source_id) ||
            (id - ssp_params.first_source_id >= ssp_params.n_spike_sources)) {
        return;
    }
    // The above condition prevents this from being negative
    uint32_t sub_id = (uint32_t) id - ssp_params.first_source_id;

    if ((circular_buffer_real_size(rate_change_buffer) -
    		circular_buffer_size(rate_change_buffer)) >= 2) {
		circular_buffer_add(rate_change_buffer, sub_id);
	    circular_buffer_add(rate_change_buffer, payload);
    }
}

//! The entry point for this model
void c_main(void) {
    // Load DTCM data
    time = 0;
    if (!initialize()) {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);
    spin1_callback_on(
            MCPL_PACKET_RECEIVED, multicast_packet_callback, MULTICAST);

    simulation_run();
}
