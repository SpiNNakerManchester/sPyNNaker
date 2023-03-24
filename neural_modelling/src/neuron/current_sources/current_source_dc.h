/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \dir
//! \brief Direct current source functions
//! \file
//! \brief Functions called for a DirectCurrentSource
#ifndef _CURRENT_SOURCE_DC_H_
#define _CURRENT_SOURCE_DC_H_

typedef struct dc_source_t {
    REAL amplitude;
    uint32_t start;
    uint32_t stop;
} dc_source_t;

static dc_source_t **dc_source;

static bool current_source_dc_init(uint32_t n_dc_sources, uint32_t *next) {
	dc_source = spin1_malloc(n_dc_sources * sizeof(uint32_t*));
	for (uint32_t n_dc=0; n_dc < n_dc_sources; n_dc++) {
		dc_source[n_dc] = spin1_malloc(sizeof(dc_source_t));
		if (dc_source[n_dc] == NULL) {
			log_error("Unable to allocate DC source parameters - out of DTCM");
			return false;
		}
		*next += sizeof(dc_source_t) / 4;
	}
	return true;
}

static bool current_source_dc_load_parameters(
		address_t cs_address, uint32_t n_dc_sources, uint32_t *next) {
	for (uint32_t n_dc=0; n_dc < n_dc_sources; n_dc++) {
		spin1_memcpy(dc_source[n_dc], &cs_address[*next], sizeof(dc_source_t));
		*next += sizeof(dc_source_t) / 4;
	}
	return true;
}

static REAL current_source_dc_get_offset(uint32_t cs_index, uint32_t time) {
    if ((time >= dc_source[cs_index]->start) && (time < dc_source[cs_index]->stop)) {
        return dc_source[cs_index]->amplitude;
    }
    return ZERO;
}

#endif // _CURRENT_SOURCE_DC_H_
