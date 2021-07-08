/*
 * Copyright (c) The University of Sussex, Garibaldi Pineda Garcia,
 * James Turner, James Knight and Thomas Nowotny
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

#ifndef _LOCAL_ONLY_STRUCTS_
#define _LOCAL_ONLY_STRUCTS_

#include <common/neuron-typedefs.h>

// TODO: we can probably do a forward declaration of these types here and
// let implementation deal with them?

typedef input_t lc_weight_t;
// Dimensions are needed to be signed due to mapping from pre- to post-synaptic.
typedef int16_t lc_dim_t;
// Neuron Ids are not signed, this is compatible with the rest of the tools (?).
typedef uint32_t lc_neuron_id_t;

// Reduce the number of parameters with the following structs
typedef struct {
    lc_dim_t row;
    lc_dim_t col;
} lc_coord_t;

typedef struct {
    lc_dim_t width;
    lc_dim_t height;
} lc_shape_t;


#endif
