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
typedef struct current_source_t {
    uint32_t current_source_id;
} current_source_t;

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

typedef struct ac_source_times_t {
    uint32_t times_length;
    uint32_t times[];
} ac_source_times_t;

typedef struct ac_source_amps_t {
    uint32_t amp_length;
    REAL amplitudes[];
} ac_source_amps_t;

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

// Globals for possible current sources
static current_source_t *current_source;
static dc_sources_t *dc_source;
//static ac_sources_t *ac_source;
static ac_source_times_t *ac_cs_times;
static ac_source_amps_t *ac_cs_amps;
static step_current_source_times_t *step_cs_times;
static step_current_source_amps_t *step_cs_amps;
static noisy_current_sources_t *noisy_current_source;

// Global values used in step current source
static REAL step_cs_amp_last = ZERO;
static uint32_t step_cs_index = 0;
static REAL ac_cs_amp_last = ZERO;
static uint32_t ac_cs_index = 0;

//! \brief Initialise the particular implementation of the data
//! \param[in] n_neurons: The number of neurons
//! \return True if successful
static bool current_source_impl_initialise(address_t cs_address, uint32_t n_neurons) {

    // Read from cs_address; the first value is the current source ID value
//    void *cs_addr = cs_address;
//    cs_globals = cs_addr;

    uint32_t cs_globals_size = n_neurons * sizeof(current_source_t);

    current_source = spin1_malloc(cs_globals_size);
    if (current_source == NULL) {
        log_error("Unable to allocate current source IDs"
                "- Out of DTCM");
        return false;
    }
    spin1_memcpy(current_source, &cs_address[0], cs_globals_size);

    uint32_t next = n_neurons;
    for (uint32_t n = 0; n < n_neurons; n++) {
        if (current_source[n].current_source_id == 1) {
            // Direct current source
            dc_source = spin1_malloc(sizeof(dc_sources_t));
            if (dc_source == NULL) {
                log_error("Unable to allocate DC source parameters"
                        "- Out of DTCM");
                return false;
            }
            spin1_memcpy(dc_source, &cs_address[next], sizeof(dc_sources_t));
            next += sizeof(dc_sources_t) / 4;
        } else if (current_source[n].current_source_id == 2) {
            //    Leaving this here for a time when this will fit into ITCM again
            //    (need to uncomment the structs / headers for this above too)
//            // Alternating current source
//            ac_source = spin1_malloc(sizeof(ac_sources_t));
//            spin1_memcpy(ac_source, &cs_address[next], sizeof(ac_sources_t));
//            next += sizeof(ac_sources_t) / 4;
            // ACSource as array
            uint32_t arr_len = (uint32_t) cs_address[next];
//            log_info("ac source, arr_len: %u", arr_len);
            uint32_t struct_size = (arr_len + 1) * 4;
            ac_cs_times = spin1_malloc(struct_size);
            if (ac_cs_times == NULL) {
                log_error("Unable to allocate ac source times array"
                        "- Out of DTCM");
                return false;
            }
            spin1_memcpy(ac_cs_times, &cs_address[next], struct_size);
            ac_cs_amps = spin1_malloc(struct_size);
            if (ac_cs_amps == NULL) {
                log_error("Unable to allocate ac source amplitudes array"
                        "- Out of DTCM");
                return false;
            }
            spin1_memcpy(ac_cs_amps, &cs_address[next+arr_len+1], struct_size);
            next += 2 * (arr_len + 1);
        } else if (current_source[n].current_source_id == 3) {
            // Step current source
            uint32_t arr_len = (uint32_t) cs_address[next];
//            log_info("step current source, arr_len: %u", arr_len);
            uint32_t struct_size = (arr_len + 1) * 4;
            step_cs_times = spin1_malloc(struct_size);
            if (step_cs_times == NULL) {
                log_error("Unable to allocate step current source times array"
                        "- Out of DTCM");
                return false;
            }
            spin1_memcpy(step_cs_times, &cs_address[next], struct_size);
            step_cs_amps = spin1_malloc(struct_size);
            if (step_cs_amps == NULL) {
                log_error("Unable to allocate step urrent source amplitudes array"
                        "- Out of DTCM");
                return false;
            }
            spin1_memcpy(step_cs_amps, &cs_address[next+arr_len+1], struct_size);
            next += 2 * (arr_len + 1);
        } else if (current_source[n].current_source_id == 4) {
            // Noisy current source
            noisy_current_source = spin1_malloc(sizeof(noisy_current_sources_t));
            if (noisy_current_source == NULL) {
                log_error("Unable to allocate noisy current source parameters"
                        "- Out of DTCM");
                return false;
            }
            spin1_memcpy(noisy_current_source, &cs_address[next], sizeof(noisy_current_sources_t));
            next += sizeof(noisy_current_sources_t) / 4;
        }
    }

    return true;

}

static REAL current_source_get_offset(uint32_t time, uint32_t neuron_index) {

    // Could simply just have the different cases in here
    // TODO: use an enum or something like that instead for the IDs

    // Case zero: do nothing
    if (current_source[neuron_index].current_source_id == 0) {
        return ZERO;
    } else if (current_source[neuron_index].current_source_id == 1) {
        // Direct current source between start and stop
        if ((time >= dc_source->start) && (time < dc_source->stop)) {
            return dc_source->amplitude;
        } else {
            return ZERO;
        }
//    Leaving this here for a time when this will fit into ITCM again
//    (need to uncomment the structs / headers for this above too)
    } else if (current_source[neuron_index].current_source_id == 2) {
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
        // AC source, i.e. change to offset values at specified times
        if (time >= ac_cs_times->times[ac_cs_index]) {
            ac_cs_amp_last = ac_cs_amps->amplitudes[ac_cs_index];
            ac_cs_index++;
        }
        return ac_cs_amp_last;

    } else if (current_source[neuron_index].current_source_id == 3) {
        // Step current source, i.e. change to offset values at specified times
        if (time >= step_cs_times->times[step_cs_index]) {
            step_cs_amp_last = step_cs_amps->amplitudes[step_cs_index];
            step_cs_index++;
        }
        return step_cs_amp_last;

    } else if (current_source[neuron_index].current_source_id == 4) {
        // Noisy current source, i.e. select offset each time based on normal distribution
        if ((time >= noisy_current_source->start) && (time < noisy_current_source->stop)) {
            // Pick a normally-distributed value based on the mean and SD provided
            REAL random_value = norminv_urt(mars_kiss64_seed(noisy_current_source->seed));
            return noisy_current_source->mean + (noisy_current_source->stdev * random_value);
        } else {
            return ZERO;
        }
    } else {
        log_error("Unexpected current_source_id value %u index %u",
                current_source[neuron_index].current_source_id, neuron_index);
        return ZERO;
    }

}

#endif // _CURRENT_SOURCE_IMPL_H_
