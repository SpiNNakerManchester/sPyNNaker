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
//! \brief Noisy current source functions
//! \file
//! \brief Functions called for a noisy current source
#ifndef _CURRENT_SOURCE_STEP_H_
#define _CURRENT_SOURCE_STEP_H_

#include <random.h>
#include <normal.h>

// Structures for different current sources used in this impl
typedef struct step_current_source_times_t {
    uint32_t times_length;
    uint32_t times[];
} step_current_source_times_t;

typedef struct step_current_source_amps_t {
    uint32_t amp_length;
    REAL amplitudes[];
} step_current_source_amps_t;

// Global values used in step current source
static step_current_source_times_t **step_cs_times;
static step_current_source_amps_t **step_cs_amps;
static REAL *step_cs_amp_last;
static uint32_t *step_cs_index;

static bool current_source_step_init(
		address_t cs_address, uint32_t n_step_current_sources, uint32_t *next) {
	if (n_step_current_sources > 0) {
		step_cs_times = spin1_malloc(n_step_current_sources * sizeof(uint32_t*));
		step_cs_amps = spin1_malloc(n_step_current_sources * sizeof(uint32_t*));
		step_cs_amp_last = spin1_malloc(n_step_current_sources * sizeof(REAL));
		step_cs_index = spin1_malloc(n_step_current_sources * sizeof(uint32_t));
		if (step_cs_amp_last == NULL) {
			log_error("Unable to allocate step current source amp last - out of DTCM");
			return false;
		}
		if (step_cs_index == NULL) {
			log_error("Unable to allocate step current source index - out of DTCM");
			return false;
		}
	}
	for (uint32_t n_step=0; n_step < n_step_current_sources; n_step++) {
		uint32_t arr_len = (uint32_t) cs_address[*next];
		uint32_t struct_size = (arr_len + 1) * sizeof(uint32_t);
		step_cs_times[n_step] = spin1_malloc(struct_size);
		if (step_cs_times[n_step] == NULL) {
			log_error("Unable to allocate step current source times - out of DTCM",
			        "struct_size is %u next %u n_step %u)", struct_size, *next, n_step);
			return false;
		}

		step_cs_amps[n_step] = spin1_malloc(struct_size);
		if (step_cs_amps[n_step] == NULL) {
			log_error("Unable to allocate step current source amplitudes - out of DTCM",
			        "(struct_size is %u next %u n_step %u)", struct_size, *next, n_step);
			return false;
		}

		*next += 2 * (arr_len + 1);
		// Initialise last value and current index along the array for this source
		step_cs_amp_last[n_step] = ZERO;
		step_cs_index[n_step] = 0;
	}
	return true;
}

static bool current_source_step_load_parameters(
		address_t cs_address, uint32_t n_step_current_sources, uint32_t *next) {
	for (uint32_t n_step=0; n_step < n_step_current_sources; n_step++) {
		uint32_t arr_len = (uint32_t) cs_address[*next];
		uint32_t struct_size = (arr_len + 1) * sizeof(uint32_t);

		spin1_memcpy(step_cs_times[n_step], &cs_address[*next], struct_size);
		spin1_memcpy(step_cs_amps[n_step], &cs_address[*next+arr_len+1], struct_size);

		*next += 2 * (arr_len + 1);

		// Does this need to happen here too?  (What happens on reload??)
		step_cs_amp_last[n_step] = ZERO;
		step_cs_index[n_step] = 0;
	}
	return true;
}

static REAL current_source_step_get_offset(uint32_t cs_index, uint32_t time) {
	if (time >= step_cs_times[cs_index]->times[step_cs_index[cs_index]]) {
		step_cs_amp_last[cs_index] =
				step_cs_amps[cs_index]->amplitudes[step_cs_index[cs_index]];
		step_cs_index[cs_index]++;
	}
	return step_cs_amp_last[cs_index];
}

#endif // _CURRENT_SOURCE_STEP_H_
