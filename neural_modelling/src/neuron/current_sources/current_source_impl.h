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

//! \dir
//! \brief Current source implementations
//! \file
//! \brief General API of a neuron implementation
#ifndef _CURRENT_SOURCE_IMPL_H_
#define _CURRENT_SOURCE_IMPL_H_

#include <common/neuron-typedefs.h>
//#include <sincos.h>
#include <random.h>
#include <normal.h>

// Global parameter for current source ID value
typedef struct current_source_globals_t {
    uint32_t current_source_id;
} current_source_globals_t;

// Structures for different current sources
typedef struct dc_sources_t {
    REAL amplitude;
    uint32_t start;
    uint32_t stop;
} dc_sources_t;

//typedef struct ac_sources_t {
//    uint32_t start;
//    uint32_t stop;
//    REAL amplitude;
//    REAL offset;
//    REAL frequency;
//    REAL phase;
//} ac_sources_t;

typedef struct step_current_source_times_t {
    uint32_t times_length;
    uint32_t times[];
} step_current_source_times_t;

typedef struct step_current_source_amps_t {
    uint32_t amp_length;
    REAL amplitudes[];
} step_current_source_amps_t;

typedef struct noisy_current_sources_t {
    REAL mean;
    REAL stdev;
    uint32_t start;
    uint32_t stop;
    uint32_t dt;
    mars_kiss64_seed_t seed;
} noisy_current_sources_t;

static noisy_current_sources_t *noisy_current_source;

// Globals for possible current sources
static current_source_globals_t *cs_globals;
static dc_sources_t *dc_source;
//static ac_sources_t *ac_source;
static step_current_source_times_t *step_cs_times;
static step_current_source_amps_t *step_cs_amps;

// Global values used in step current source
static REAL step_cs_amp_last = ZERO;
static uint32_t step_cs_index = 0;

//! \brief Initialise the particular implementation of the data
//! \param[in] n_neurons: The number of neurons
//! \return True if successful
static bool current_source_impl_initialise(address_t cs_address) {

    // Read from cs_address; the first value is the current source ID value
    void *cs_addr = cs_address;
    cs_globals = cs_addr;

    uint32_t next = 1;
    if (cs_globals->current_source_id == 1) {
        // Direct current source
        dc_source = spin1_malloc(sizeof(dc_sources_t));
        spin1_memcpy(dc_source, &cs_address[next], sizeof(dc_sources_t));
//    Leaving this here for a time when this will fit into ITCM again
//    (need to uncomment the structs / headers for this above too)
//    } else if (cs_globals->current_source_id == 2) {
//        // Alternating current source
//        ac_source = spin1_malloc(sizeof(ac_sources_t));
//        spin1_memcpy(ac_source, &cs_address[next], sizeof(ac_sources_t));
    } else if ((cs_globals->current_source_id == 3) || (cs_globals->current_source_id == 2)) {
        // Step current source / "alternating current source" as array
        uint32_t arr_len = (uint32_t) cs_address[next];
//        log_info("step current source, arr_len: %u", arr_len);
        uint32_t struct_size = (arr_len + 1) * 4;
        step_cs_times = spin1_malloc(struct_size);
        spin1_memcpy(step_cs_times, &cs_address[next], struct_size);
        step_cs_amps = spin1_malloc(struct_size);
        spin1_memcpy(step_cs_amps, &cs_address[next+arr_len+1], struct_size);
    } else if (cs_globals->current_source_id == 4) {
        // Noisy current source
        noisy_current_source = spin1_malloc(sizeof(noisy_current_sources_t));
        spin1_memcpy(noisy_current_source, &cs_address[next], sizeof(noisy_current_sources_t));
    }

    return true;

}

static REAL current_source_get_offset(uint32_t time) {

    // Could simply just have the different cases in here
    // TODO: use an enum or something like that instead for the IDs

    // Case zero: do nothing
    if (cs_globals->current_source_id == 0) {
        return ZERO;
    } else if (cs_globals->current_source_id == 1) {
        // Direct current source between start and stop
        if ((time >= dc_source->start) && (time < dc_source->stop)) {
            return dc_source->amplitude;
        } else {
            return ZERO;
        }
//    Leaving this here for a time when this will fit into ITCM again
//    (need to uncomment the structs / headers for this above too)
//    } else if (cs_globals->current_source_id == 2) {
//        // Alternating current source between start and stop
//        if ((time >= ac_source->start) && (time < ac_source->stop)) {
//            // calculate c_off = offset + amplitude * sin((t/freq) + phase)
//            REAL time_value = (REAL) time - (REAL) ac_source->start;
//            REAL sin_value = sink((time_value * ac_source->frequency) + ac_source->phase);
//            REAL current_offset = ac_source->offset + (
//                    ac_source->amplitude * sin_value);
////            log_info("time %u current_offset %k", time, current_offset);
//            return current_offset;
//        } else {
//            return ZERO;
//        }
//        return ZERO;
    } else if ((cs_globals->current_source_id == 3) || (cs_globals->current_source_id == 2)) {
        // Step current source, i.e. change to offset values at specified times
        if (time >= step_cs_times->times[step_cs_index]) {
            step_cs_amp_last = step_cs_amps->amplitudes[step_cs_index];
            step_cs_index++;
        }
        return step_cs_amp_last;

    } else if (cs_globals->current_source_id == 4) {
        // Noisy current source, i.e. select offset each time based on normal distribution
        if ((time >= noisy_current_source->start) && (time < noisy_current_source->stop)) {
            // Pick a normally-distributed value based on the mean and SD provided
            REAL random_value = norminv_urt(mars_kiss64_seed(noisy_current_source->seed));
            return noisy_current_source->mean + (noisy_current_source->stdev * random_value);
        } else {
            return ZERO;
        }
    } else {
        log_error("Unexpected current_source_id value %u", cs_globals->current_source_id);
        return ZERO;
    }

}

#endif // _CURRENT_SOURCE_IMPL_H_
