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
#ifndef _CURRENT_SOURCE_NOISY_H_
#define _CURRENT_SOURCE_NOISY_H_

#include <random.h>
#include <normal.h>

// Structures for different current sources in this impl
typedef struct noisy_current_source_t {
    REAL mean;
    REAL stdev;
    uint32_t start;
    uint32_t stop;
    uint32_t dt;
    mars_kiss64_seed_t seed;
} noisy_current_source_t;

static noisy_current_source_t **noisy_source;

static bool current_source_noisy_init(uint32_t n_noisy_sources, uint32_t *next) {
	noisy_source = spin1_malloc(n_noisy_sources * sizeof(uint32_t*));
	for (uint32_t n_noisy=0; n_noisy < n_noisy_sources; n_noisy++) {
		noisy_source[n_noisy] = spin1_malloc(sizeof(noisy_current_source_t));
		if (noisy_source[n_noisy] == NULL) {
			log_error("Unable to allocate DC source parameters - out of DTCM");
			return false;
		}
		*next += sizeof(noisy_current_source_t) / 4;
	}
	return true;
}

static bool current_source_noisy_load_parameters(
		address_t cs_address, uint32_t n_noisy_sources, uint32_t *next) {
	for (uint32_t n_noisy=0; n_noisy < n_noisy_sources; n_noisy++) {
		spin1_memcpy(noisy_source[n_noisy], &cs_address[*next], sizeof(noisy_current_source_t));
		*next += sizeof(noisy_current_source_t) / 4;
	}
	return true;
}

static REAL current_source_noisy_get_offset(uint32_t cs_index, uint32_t time) {
    if ((time >= noisy_source[cs_index]->start) && (time < noisy_source[cs_index]->stop)) {
        // Pick a normally-distributed value based on the mean and SD provided
        REAL random_value = norminv_urt(mars_kiss64_seed(noisy_source[cs_index]->seed));
        REAL noisy_current_offset = noisy_source[cs_index]->mean + (
                noisy_source[cs_index]->stdev * random_value);
        return noisy_current_offset;
    }
    return ZERO;
}

#endif // _CURRENT_SOURCE_NOISY_H_
