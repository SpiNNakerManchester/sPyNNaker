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

#ifndef _NEURON_MODEL_IZH_CURR_IMPL_H_
#define _NEURON_MODEL_IZH_CURR_IMPL_H_

#include "neuron_model.h"

typedef struct neuron_t {
    // nominally 'fixed' parameters
    REAL A;
    REAL B;
    REAL C;
    REAL D;

    // Variable-state parameters
    REAL V;
    REAL U;

    // offset current [nA]
    REAL I_offset;

    // current timestep - simple correction for threshold
    REAL this_h;
} neuron_t;

typedef struct global_neuron_params_t {
    REAL machine_timestep_ms;
} global_neuron_params_t;

#endif   // _NEURON_MODEL_IZH_CURR_IMPL_H_
