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

#ifndef _NEURON_MODEL_LIF_CURR_IMPL_H_
#define _NEURON_MODEL_LIF_CURR_IMPL_H_

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

    // 'fixed' computation parameter - time constant multiplier for
    // closed-form solution
    // exp(-(machine time step in ms)/(R * C)) [.]
    REAL     exp_TC;

    // offset current [nA]
    REAL     I_offset;

    // countdown to end of next refractory period [timesteps]
    int32_t  refract_timer;

    // post-spike reset membrane voltage [mV]
    REAL     U_reset;

    // refractory time of neuron [timesteps]
    int32_t  T_refract;


    // Dendritic compartment parameters
    REAL	V; // dendritic potential
    REAL	V_star; // dendritic prediction of U
    REAL    V_star_cond; // precalculated multiplier for converting V to V*
    REAL    exp_TC_dend; // Exp time constant for low-pass filtering dendrite potential


    // Poisson compartment params
    REAL mean_isi_ticks;
    REAL time_to_spike_ticks;
    int32_t time_since_last_spike;
    REAL rate_at_last_setting;
    REAL rate_update_threshold;

} neuron_t;

typedef struct global_neuron_params_t {
 	mars_kiss64_seed_t spike_source_seed; // array of 4 values
	REAL ticks_per_second;
} global_neuron_params_t;

#endif // _NEURON_MODEL_LIF_CURR_IMPL_H_
