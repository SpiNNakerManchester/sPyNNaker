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
//! \brief Alternating current source functions
//! \file
//! \brief Functions called for an alternating current source
#ifndef _CURRENT_SOURCE_AC_H_
#define _CURRENT_SOURCE_AC_H_

#include <sincos.h>

// Structure for AC current source
typedef struct ac_source_t {
    uint32_t start;
    uint32_t stop;
    REAL amplitude;
    REAL offset;
    REAL frequency;
    REAL phase;
} ac_source_t;

static ac_source_t **ac_source;

static bool current_source_ac_init(uint32_t n_ac_sources, uint32_t *next) {
	ac_source = spin1_malloc(n_ac_sources * sizeof(uint32_t*));
	for (uint32_t n_ac=0; n_ac < n_ac_sources; n_ac++) {
		ac_source[n_ac] = spin1_malloc(sizeof(ac_source_t));
		if (ac_source[n_ac] == NULL) {
			log_error("Unable to allocate AC source parameters - out of DTCM");
			return false;
		}
		*next += sizeof(ac_source_t) / 4;
	}
	return true;
}

static bool current_source_ac_load_parameters(
		address_t cs_address, uint32_t n_ac_sources, uint32_t *next) {
	for (uint32_t n_ac=0; n_ac < n_ac_sources; n_ac++) {
		spin1_memcpy(ac_source[n_ac], &cs_address[*next], sizeof(ac_source_t));
		*next += sizeof(ac_source_t) / 4;
	}
	return true;
}

static REAL current_source_ac_get_offset(uint32_t cs_index, uint32_t time) {
    if ((time >= ac_source[cs_index]->start) && (time < ac_source[cs_index]->stop)) {
        REAL time_value = kbits((time - ac_source[cs_index]->start) << 15);
        REAL sin_value = sink((time_value * ac_source[cs_index]->frequency) +
                ac_source[cs_index]->phase);
        REAL ac_current_offset = ac_source[cs_index]->offset + (
                ac_source[cs_index]->amplitude * sin_value);
        return ac_current_offset;
    }
    return ZERO;
}

#endif // _CURRENT_SOURCE_AC_H_
