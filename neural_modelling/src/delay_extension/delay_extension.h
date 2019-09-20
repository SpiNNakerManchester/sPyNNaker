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

#ifndef __DELAY_EXTENSION_H__
#define __DELAY_EXTENSION_H__

#include <common-typedefs.h>

// Constants
#define DELAY_STAGE_LENGTH  16

//! region identifiers
typedef enum region_identifiers {
    SYSTEM = 0, DELAY_PARAMS = 1, PROVENANCE_REGION = 2, EXPANDER_REGION = 3
} region_identifiers;

struct delay_parameters {
    uint32_t key;
    uint32_t incoming_key;
    uint32_t incoming_mask;
    uint32_t n_atoms;
    uint32_t n_delay_stages;
    uint32_t random_backoff;
    uint32_t time_between_spikes;
    uint32_t n_outgoing_edges;
    uint32_t delay_blocks[];
};

#define pack_delay_index_stage(index, stage) \
    ((index & 0xFF) | ((stage & 0xFF) << 8))
#define unpack_delay_index(packed)      (packed & 0xFF)
#define unpack_delay_stage(packed)      ((packed >> 8) & 0xFF)

#endif // __DELAY_EXTENSION_H__
