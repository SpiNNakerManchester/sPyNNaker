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
#ifndef _CURRENT_SOURCE_H_
#define _CURRENT_SOURCE_H_

#include <common/neuron-typedefs.h>

#ifdef _CURRENT_SOURCE_DC_H_
#include "current_source_dc.h"
#endif
#ifdef _CURRENT_SOURCE_AC_H_
#include "current_source_ac.h"
#endif
#ifdef _CURRENT_SOURCE_STEP_H_
#include "current_source_step.h"
#endif
#ifdef _CURRENT_SOURCE_NOISY_H_
#include "current_source_noisy.h"
#endif

// Global struct for current source ID value relating to indices in individual structs
typedef struct current_source_t {
    uint32_t current_source_id;  // the current source ID value
    uint32_t current_source_index;  // the index this refers to in this current source type's struct
    uint32_t n_neuron_ids;  // the number of neurons this current source applies to
    uint32_t neuron_id_list[];  // the list of IDs of these neurons
} current_source_t;

static uint32_t n_current_sources;
static uint32_t n_dc_sources;
static uint32_t n_ac_sources;
static uint32_t n_step_sources;
static uint32_t n_noisy_sources;

static current_source_t **current_source;

//static neuron_current_sources_t *neuron_current_sources;

#ifndef SOMETIMES_UNUSED
#define SOMETIMES_UNUSED __attribute__((unused))
#endif // !SOMETIMES_UNUSED

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Initialise the particular implementation of the data
//! \param[in] cs_address: The address to start reading data from
//! \param[in] n_neurons: The number of neurons to initialise data for
//! \return True if successful
static bool current_source_initialise(address_t cs_address) {
    // Avoid the loops if no current sources
    #if !defined(_CURRENT_SOURCE_DC_H_) && !defined(_CURRENT_SOURCE_AC_H) && !defined(_CURRENT_SOURCE_STEP_H_) && !defined(_CURRENT_SOURCE_NOISY_H_)
    io_printf(IO_BUF, "no current sources defined \n");
    return true;
    #else

    // Read from cs_address; the first value is the number of current sources
    n_current_sources = cs_address[0];

    current_source = spin1_malloc(n_current_sources * sizeof(uint32_t*));

    // Loop over number of current sources and get ID list for each
    uint32_t next = 1;
    for (uint32_t ncs=0; ncs < n_current_sources; ncs++)  {

    	// try the original way
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
			n_step_sources++;
		} else if (current_source[ncs]->current_source_id == 4) {
			n_noisy_sources++;
		}

		next += (n_ids + 3);
    }

	// Now initialise separate sources
#ifdef _CURRENT_SOURCE_DC_H_
	if (!current_source_dc_init(n_dc_sources, &next)) {
		return false;
	}
#else
	if (n_dc_sources > 0) {
		log_error("DC current source is not supported for this build");
		return false;
	}
#endif

#ifdef _CURRENT_SOURCE_AC_H_
	if (!current_source_ac_init(n_ac_sources, &next)) {
		return false;
	}
#else
	if (n_ac_sources > 0) {
		log_error("AC current source is not supported for this build");
		return false;
	}
#endif

#ifdef _CURRENT_SOURCE_STEP_H_
	if (!current_source_step_init(cs_address, n_step_sources, &next)) {
		return false;
	}
#else
	if (n_step_sources > 0) {
		log_error("Step current source is not supported for this build");
		return false;
	}
#endif

#ifdef _CURRENT_SOURCE_NOISY_H_
	if (!current_source_noisy_init(n_noisy_sources, &next)) {
		return false;
	}
#else
	if (n_noisy_sources > 0) {
		log_error("Noisy current source is not supported for this build");
		return false;
	}
#endif

    return true;

    #endif
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Load the data into the allocated array structures
//! \param[in] cs_address: The address to start reading data from
//! \return True if successful
static bool current_source_load_parameters(address_t cs_address) {

    // Read the number of current sources
    n_current_sources = cs_address[0];

    uint32_t next = 1;

    // Copy data into current source array
    for (uint32_t ncs=0; ncs < n_current_sources; ncs++) {
        uint32_t n_ids = (uint32_t) cs_address[next+2];
        uint32_t struct_size = (n_ids + 3) * sizeof(uint32_t);

        spin1_memcpy(current_source[ncs], &cs_address[next], struct_size);

        next += (n_ids + 3);
    }

    // Copy into individual source arrays
#ifdef _CURRENT_SOURCE_DC_H_
    current_source_dc_load_parameters(cs_address, n_dc_sources, &next);
#endif
#ifdef _CURRENT_SOURCE_AC_H_
    current_source_ac_load_parameters(cs_address, n_ac_sources, &next);
#endif
#ifdef _CURRENT_SOURCE_STEP_H_
    current_source_step_load_parameters(cs_address, n_step_sources, &next);
#endif
#ifdef _CURRENT_SOURCE_NOISY_H_
    current_source_noisy_load_parameters(cs_address, n_noisy_sources, &next);
#endif

    return true;
}


SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Calculate the current offset from all injected current sources
//! \param[in] time: The current time
//! \param[in] neuron_index: The neuron index to calculate the value for
//! \return True if successful
static inline REAL current_source_get_offset(uint32_t time, uint32_t neuron_index) {
    // Avoid the loops if no current sources
    #if !defined(_CURRENT_SOURCE_DC_H_) && !defined(_CURRENT_SOURCE_AC_H) && !defined(_CURRENT_SOURCE_STEP_H_) && !defined(_CURRENT_SOURCE_NOISY_H_)
    return ZERO;
    #else

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
				#ifdef _CURRENT_SOURCE_DC_H_
				// Now do the appropriate calculation based on the ID value
				if (cs_id == 1) {  // DCSource
					current_offset += current_source_dc_get_offset(cs_index, time);
				}
				#endif
				#ifdef _CURRENT_SOURCE_AC_H_
				// Now do the appropriate calculation based on the ID value
				if (cs_id == 2) {  // ACSource
					current_offset += current_source_ac_get_offset(cs_index, time);
				}
				#endif
				#ifdef _CURRENT_SOURCE_STEP_H_
				// Now do the appropriate calculation based on the ID value
				if (cs_id == 3) {  // StepCurrentSource
					current_offset += current_source_step_get_offset(cs_index, time);
				}
				#endif
				#ifdef _CURRENT_SOURCE_NOISY_H_
				// Now do the appropriate calculation based on the ID value
				if (cs_id == 4) {  // NoisyCurrentSource
					current_offset += current_source_noisy_get_offset(cs_index, time);
				}
				#endif
			}

		}
	}

	return current_offset;

	#endif
}

#endif // _CURRENT_SOURCE_H_
