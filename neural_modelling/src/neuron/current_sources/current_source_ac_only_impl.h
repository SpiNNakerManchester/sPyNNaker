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
//! \brief General API of a current source implementation
#ifndef _CURRENT_SOURCE_IMPL_H_
#define _CURRENT_SOURCE_IMPL_H_

#include "current_source.h"
#include <common/neuron-typedefs.h>
#include <sincos.h>

// Global parameter for current source ID value
typedef struct current_source_t {
    uint32_t current_source_id;  // the current source ID value
    uint32_t current_source_index;  // the index this refers to in this current source type's struct
    uint32_t n_neuron_ids;  // the number of neurons this current source applies to
    uint32_t neuron_id_list[];
} current_source_t;

// Structures for different current sources
typedef struct ac_sources_t {
    uint32_t start;
    uint32_t stop;
    REAL amplitude;
    REAL offset;
    REAL frequency;
    REAL phase;
} ac_sources_t;

// Globals for possible current sources
static current_source_t **current_source;
static ac_sources_t **ac_source;

static uint32_t n_current_sources;
static uint32_t n_dc_sources = 0;
static uint32_t n_ac_sources = 0;
static uint32_t n_step_current_sources = 0;
static uint32_t n_noisy_current_sources = 0;

#ifndef SOMETIMES_UNUSED
#define SOMETIMES_UNUSED __attribute__((unused))
#endif // !SOMETIMES_UNUSED

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Initialise the particular implementation of the data
//! \param[in] cs_address: The address to start reading data from
//! \return True if successful
static bool current_source_impl_initialise(address_t cs_address) {

    // Read from cs_address; the first value is the number of current sources
    n_current_sources = cs_address[0];

    current_source = spin1_malloc(n_current_sources * sizeof(uint32_t*));

    uint32_t next = 1;
    // Loop over number of current sources and get ID list for each
    for (uint32_t ncs=0; ncs < n_current_sources; ncs++) {
        uint32_t n_ids = (uint32_t) cs_address[next+2];
        uint32_t struct_size = (n_ids + 3) * sizeof(uint32_t);
        current_source[ncs] = spin1_malloc(struct_size);
        if (current_source[ncs] == NULL) {
            log_error("Unable to allocate %u of %u current source IDs - Out of DTCM",
                    ncs, n_current_sources);
            return false;
        }

        spin1_memcpy(current_source[ncs], &cs_address[next], struct_size);

        // Count sources
        if (current_source[ncs]->current_source_id == 1) {
            n_dc_sources++;
        } else if (current_source[ncs]->current_source_id == 2) {
            n_ac_sources++;
        } else if (current_source[ncs]->current_source_id == 3) {
            n_step_current_sources++;
        } else if (current_source[ncs]->current_source_id == 4) {
            n_noisy_current_sources++;
        }

        next += (n_ids + 3);
    }

    log_debug("Initialising current sources: n_dc %u n_ac %u n_step %u n_noisy %u\n",
            n_dc_sources, n_ac_sources, n_step_current_sources, n_noisy_current_sources);

    // Error if DC sources defined
    if (n_dc_sources > 0) {
        log_error("This implementation file does not define DC sources");
        return false;
    }

    // Initialise AC sources
    ac_source = spin1_malloc(n_ac_sources * sizeof(uint32_t*));
    for (uint32_t n_ac=0; n_ac < n_ac_sources; n_ac++) {
        ac_source[n_ac] = spin1_malloc(sizeof(ac_sources_t));
        if (ac_source[n_ac] == NULL) {
            log_error("Unable to allocate DC source parameters - out of DTCM");
            return false;
        }

        next += sizeof(ac_sources_t) / 4;
    }

    // Error if step current sources defined
    if (n_step_current_sources > 0) {
        log_error("This implementation file does not define StepCurrentSources");
        return false;
    }

    // Error if noisy current sources defined
    if (n_noisy_current_sources > 0) {
        log_error("This implementation file does not define NoisyCurrentSources");
        return false;
    }

    return true;

}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Load the data into the allocated array structures
//! \param[in] cs_address: The address to start reading data from
//! \return True if successful
static bool current_source_impl_load_parameters(address_t cs_address) {
    n_current_sources = cs_address[0];

    uint32_t next = 1;

    // Copy data into current source array
    for (uint32_t ncs=0; ncs < n_current_sources; ncs++) {
        uint32_t n_ids = (uint32_t) cs_address[next+2];
        uint32_t struct_size = (n_ids + 3) * sizeof(uint32_t);

        spin1_memcpy(current_source[ncs], &cs_address[next], struct_size);

        next += (n_ids + 3);
    }

    // Copy into AC sources array
    for (uint32_t n_ac=0; n_ac < n_ac_sources; n_ac++) {
        spin1_memcpy(ac_source[n_ac], &cs_address[next], sizeof(ac_sources_t));
        next += sizeof(ac_sources_t) / 4;
    }

    return true;
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
static REAL current_source_get_offset(uint32_t time, uint32_t neuron_index) {
    // Could simply just have the different cases in here
    // TODO: use an enum or something like that instead for the IDs
    REAL current_offset = ZERO;

    // Loop over current sources
    for (uint32_t n_cs=0; n_cs < n_current_sources; n_cs++) {
        // Loop over neuron IDs associated with this current source
        uint32_t n_neuron_ids = current_source[n_cs]->n_neuron_ids;
        for (uint32_t n=0; n < n_neuron_ids; n++) {
            // If neuron ID matches the index value we are currently at
            if (neuron_index == current_source[n_cs]->neuron_id_list[n]) {
                uint32_t cs_index = current_source[n_cs]->current_source_index;
                uint32_t cs_id = current_source[n_cs]->current_source_id;
                // Now do the appropriate calculation based on the ID value
                if (cs_id == 2) {  // ACSource
                    // Alternating current source between start and stop
                    if ((time >= ac_source[cs_index]->start) &&
                            (time < ac_source[cs_index]->stop)) {
                        // calculate c_off = offset + amplitude * sin((t/freq) + phase)
                        REAL time_value = (REAL) time - (REAL) ac_source[cs_index]->start;
                        REAL sin_value = sink((time_value * ac_source[cs_index]->frequency) +
                                ac_source[cs_index]->phase);
                        REAL ac_current_offset = ac_source[cs_index]->offset + (
                                ac_source[cs_index]->amplitude * sin_value);
                        current_offset += ac_current_offset;
                    }
               }
            }
        }
    }

    return current_offset;
}

#endif // _CURRENT_SOURCE_IMPL_H_
