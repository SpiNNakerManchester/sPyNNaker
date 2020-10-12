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

#ifndef _NEURON_MODEL_LIF_TWO_COMP_IMPL_H_
#define _NEURON_MODEL_LIF_TWO_COMP_IMPL_H_

#include "neuron_model.h"
#include <random.h>

/////////////////////////////////////////////////////////////
// definition for LIF neuron parameters
typedef struct neuron_t {
    // membrane voltage [mV]
    REAL     U_membrane;

    // membrane resting voltage [mV]
    REAL     U_rest;

    // membrane resistance [MOhm]
    REAL     R_membrane;

    // offset current [nA]
    REAL     I_offset;

    // post-spike reset membrane voltage [mV]
    REAL     U_reset;

    // Dendritic compartment parameters
    REAL		V; // dendritic potential
    REAL		V_star; // dendritic prediction of U
    REAL    plasticity_rate_multiplier; // precalculated multiplier to convert rate for plasticity

    // Leaky conductance
    REAL g_L;
    REAL tau_L;

    // Coupling conductance
    REAL g_D;

    REAL g_som;


    REAL rate_at_last_setting;
    REAL rate_update_threshold;
    REAL rate_diff;

} neuron_t;

typedef struct global_neuron_params_t {
 	mars_kiss64_seed_t spike_source_seed; // array of 4 values
	REAL ticks_per_second;
} global_neuron_params_t;

#endif // _NEURON_MODEL_LIF_CURR_IMPL_H_
