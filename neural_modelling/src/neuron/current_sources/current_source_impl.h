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
#include <sincos.h>

// Global parameter for current source ID value
typedef struct current_source_globals_t {
    uint32_t current_source_id;
} current_source_globals_t;

typedef struct dc_sources_t {
    REAL amplitude;
    uint32_t start;
    uint32_t stop;
} dc_sources_t;

typedef struct ac_sources_t {
    uint32_t start;
    uint32_t stop;
    REAL amplitude;
    REAL offset;
    REAL frequency;
    REAL phase;
} ac_sources_t;

typedef struct step_current_sources_t {
    uint32_t amp_length;
    REAL times_and_amplitudes[];
} step_current_sources_t;

typedef struct noisy_current_sources_t {
    REAL mean;
    REAL stdev;
    uint32_t start;
    uint32_t stop;
    uint32_t dt;
} noisy_current_sources_t;

static current_source_globals_t *cs_globals;
static dc_sources_t *dc_source;
static ac_sources_t *ac_source;
static step_current_sources_t *step_current_source;
static noisy_current_sources_t *noisy_current_source;

// Select which header to go to based on CurrentSourceID number
//  (copy the idea from the synapse_expander... )?

//! \brief Initialise the particular implementation of the data
//! \param[in] n_neurons: The number of neurons
//! \return True if successful
static bool current_source_impl_initialise(address_t cs_address) {

    // Read from cs_address; the first value is the current source ID value
    void *cs_addr = cs_address;
    cs_globals = cs_addr;

//    log_info("test: current_source ID %u", cs_globals->current_source_id);

//    current_source_id = cs_addr[0];
//
//    log_info("current_source_id %u", current_source_id):

    uint32_t next = 1;
    if (cs_globals->current_source_id == 1) {
        // Direct current source
        dc_source = spin1_malloc(sizeof(dc_sources_t));
        spin1_memcpy(dc_source, &cs_address[next], sizeof(dc_sources_t));
//        log_info("DC source, parameters: %k %u %u", dc_source->amplitude,
//                dc_source->start, dc_source->stop);

    } else if (cs_globals->current_source_id == 2) {
        // Alternating current source
        ac_source = spin1_malloc(sizeof(ac_sources_t));
        spin1_memcpy(ac_source, &cs_address[next], sizeof(ac_sources_t));
//        log_info("AC source, parameters: %u %u %k %k %k %k",
//                ac_source->start, ac_source->stop, ac_source->amplitude,
//                ac_source->offset, ac_source->frequency, ac_source->phase);

    } else if (cs_globals->current_source_id == 3) {
        // Step current source
        uint32_t arr_len = &cs_address[next];
        uint32_t struct_size = ((2 * arr_len) + 1) * 4;
        step_current_source = spin1_malloc(struct_size);  // think this is right?
        spin1_memcpy(step_current_source, &cs_address[next], struct_size);
        log_info("step current source, parameters: %u %k %k",
                step_current_source->amp_length,
                step_current_source->times_and_amplitudes[0],
                step_current_source->times_and_amplitudes[arr_len]);

    } else if (cs_globals->current_source_id == 4) {
        // Noisy current source
        noisy_current_source = spin1_malloc(sizeof(noisy_current_sources_t));
        spin1_memcpy(noisy_current_source, &cs_address[next], sizeof(noisy_current_sources_t));
        log_info("noisy current source, parameters %k %k %u %u %u",
                noisy_current_source->mean, noisy_current_source->stdev,
                noisy_current_source->start, noisy_current_source->stop,
                noisy_current_source->dt);

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
    } else if (cs_globals->current_source_id == 2) {
        // Alternating current source between start and stop
        if ((time >= ac_source->start) && (time < ac_source->stop)) {
            // calculate c_off = offset + amplitude * sin((t/freq) + phase)
            REAL time_value = (REAL) time - (REAL) ac_source->start;
            REAL sin_value = sink((time_value * ac_source->frequency) + ac_source->phase);
            REAL current_offset = ac_source->offset + (
                    ac_source->amplitude * sin_value);
            log_info("time %u current_offset %k", time, current_offset);
            return current_offset;
        } else {
            return ZERO;
        }
    } else if (cs_globals->current_source_id == 3) {
        // Step current source, i.e. change to offset values at specified times
        return ZERO;

    } else if (cs_globals->current_source_id == 4) {
        // Noisy current source, i.e. select offset each time based on normal distribution
        return ZERO;

    } else {
        log_error("Unexpected current_source_id value %u", cs_globals->current_source_id);
        return ZERO;
    }

}

#endif // _CURRENT_SOURCE_IMPL_H_
