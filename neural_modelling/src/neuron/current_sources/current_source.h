/*
 * Copyright (c) 2017 The University of Manchester
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

//! \dir
//! \brief Current source implementations
//! \file
//! \brief General API of a current source implementation
#ifndef _CURRENT_SOURCE_H_
#define _CURRENT_SOURCE_H_

#include <common/neuron-typedefs.h>

// Struct for current source id type and current source index of that type
typedef struct cs_id_index_t {
    uint32_t cs_id;
    uint32_t cs_index;
} cs_id_index_t;

// Global struct for each neuron's current source IDs and indices
typedef struct neuron_current_source_t {
    uint32_t n_current_sources;  // the number of current sources for this neuron
    cs_id_index_t cs_id_index_list[];  // the list of CS type ID and index in that type
} neuron_current_source_t;

// Global values for the total number of current sources and number of each type
static uint32_t n_current_sources;
static uint32_t n_dc_sources;
static uint32_t n_ac_sources;
static uint32_t n_step_sources;
static uint32_t n_noisy_sources;

static uint32_t n_neurons_on_core;

static neuron_current_source_t **neuron_current_source;

#ifndef SOMETIMES_UNUSED
#define SOMETIMES_UNUSED __attribute__((unused))
#endif // !SOMETIMES_UNUSED

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Initialise the particular implementation of the data
//! \param[in] cs_address: The address to start reading data from
//! \param[in] n_neurons: The number of neurons to initialise data for
//! \return True if successful
static bool current_source_initialise(address_t cs_address, uint32_t n_neurons) {
    // Avoid the loops if no current sources
    #if !defined(_CURRENT_SOURCE_DC_H_) && !defined(_CURRENT_SOURCE_AC_H) && \
		!defined(_CURRENT_SOURCE_STEP_H_) && !defined(_CURRENT_SOURCE_NOISY_H_)
    return true;
    #else

    n_neurons_on_core = n_neurons;

    // Read from cs_address; the first value is the number of current sources
    n_current_sources = cs_address[0];

    // Don't initialise if no current sources
    if (n_current_sources != 0) {

		neuron_current_source = spin1_malloc(n_neurons * sizeof(uint32_t*));

		// Loop over neurons and read in the current IDs and indices
		uint32_t next = 1;
		for (uint32_t n=0; n < n_neurons; n++) {
			uint32_t n_sources = (uint32_t) cs_address[next];
			uint32_t struct_size = (1 + (2 * n_sources)) * sizeof(uint32_t);
			neuron_current_source[n] = spin1_malloc(struct_size);
			spin1_memcpy(neuron_current_source[n], &cs_address[next], struct_size);

			next += 1 + (n_sources * 2);

		}

		// Read number of each type of current source
        n_dc_sources = (uint32_t) cs_address[next++];
        n_ac_sources = (uint32_t) cs_address[next++];
        n_step_sources = (uint32_t) cs_address[next++];
        n_noisy_sources = (uint32_t) cs_address[next++];

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

    }

    return true;

    #endif
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Load the data into the allocated array structures
//! \param[in] cs_address: The address to start reading data from
//! \return True if successful
static bool current_source_load_parameters(address_t cs_address) {
    // Avoid the loops if no current sources
    #if !defined(_CURRENT_SOURCE_DC_H_) && !defined(_CURRENT_SOURCE_AC_H) && \
        !defined(_CURRENT_SOURCE_STEP_H_) && !defined(_CURRENT_SOURCE_NOISY_H_)
//    io_printf(IO_BUF, "no current sources defined \n");
    return true;
    #else

    // Read the number of current sources
    n_current_sources = cs_address[0];

    // Don't load if no current sources
    if (n_current_sources != 0) {
		uint32_t next = 1;

		// Copy data into neuron_current_source array
		for (uint32_t n=0; n < n_neurons_on_core; n++) {
			uint32_t n_sources = (uint32_t) cs_address[next];
			uint32_t struct_size = (1 + (2 * n_sources)) * sizeof(uint32_t);
			neuron_current_source[n] = spin1_malloc(struct_size);
			spin1_memcpy(neuron_current_source[n], &cs_address[next], struct_size);

			next += 1 + (n_sources * 2);
		}

        // Read number of each type of current source
        n_dc_sources = (uint32_t) cs_address[next++];
        n_ac_sources = (uint32_t) cs_address[next++];
        n_step_sources = (uint32_t) cs_address[next++];
        n_noisy_sources = (uint32_t) cs_address[next++];

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

    }

    return true;

    #endif
}


SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Calculate the current offset from all injected current sources
//! \param[in] time: The current time
//! \param[in] neuron_index: The neuron index to calculate the value for
//! \return True if successful
static inline REAL current_source_get_offset(uint32_t time, uint32_t neuron_index) {
    // Avoid the loops if no current sources defined
    #if !defined(_CURRENT_SOURCE_DC_H_) && !defined(_CURRENT_SOURCE_AC_H) && \
		!defined(_CURRENT_SOURCE_STEP_H_) && !defined(_CURRENT_SOURCE_NOISY_H_)
    return ZERO;
    #else

    REAL current_offset = ZERO;

    // Also avoid the loop if no current sources set by user
    if (n_current_sources != 0) {
		uint32_t n_current_sources_neuron =
				neuron_current_source[neuron_index]->n_current_sources;
		if (n_current_sources_neuron > 0) {
			for (uint32_t n_cs=0; n_cs < n_current_sources_neuron; n_cs++) {
				uint32_t cs_id =
						neuron_current_source[neuron_index]->cs_id_index_list[n_cs].cs_id;
				uint32_t cs_index =
						neuron_current_source[neuron_index]->cs_id_index_list[n_cs].cs_index;
				// Now do the appropriate calculation based on the ID value
				#ifdef _CURRENT_SOURCE_DC_H_
				if (cs_id == 1) {  // DCSource
					current_offset += current_source_dc_get_offset(cs_index, time);
				}
				#endif
				#ifdef _CURRENT_SOURCE_AC_H_
				if (cs_id == 2) {  // ACSource
					current_offset += current_source_ac_get_offset(cs_index, time);
				}
				#endif
				#ifdef _CURRENT_SOURCE_STEP_H_
				if (cs_id == 3) {  // StepCurrentSource
					current_offset += current_source_step_get_offset(cs_index, time);
				}
				#endif
				#ifdef _CURRENT_SOURCE_NOISY_H_
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
