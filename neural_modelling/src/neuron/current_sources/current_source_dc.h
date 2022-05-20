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
