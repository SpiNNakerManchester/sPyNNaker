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

#define SYNAPSES_PER_NEURON 250


typedef struct eprop_syn_state_t {
	uint16_t delta_w; // weight change to apply
	uint16_t z_bar; // low-pass filtered spike train
	uint32_t ep_a; // adaptive component of eligibility vector
	uint32_t e_bar; // low-pass filtered eligibility trace
}eprop_syn_state_t;

/////////////////////////////////////////////////////////////
// definition for LIF neuron parameters
typedef struct neuron_t {
    // membrane voltage [mV]
    REAL     V_membrane;

    // membrane resting voltage [mV]
    REAL     V_rest;

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
    REAL     V_reset;

    // refractory time of neuron [timesteps]
    int32_t  T_refract;

    // Neuron spike train
    REAL z;

    // refractory multiplier - to allow evolution of neuronal dynamics during
    // refractory period
    REAL A;

    // pseudo derivative
    REAL     psi;

    REAL    L; // learning signal

    // array of synaptic states - peak fan-in of 250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];

} neuron_t;

typedef struct global_neuron_params_t {
	REAL core_pop_rate;
	REAL core_target_rate;
	REAL rate_exp_TC;
} global_neuron_params_t;

#endif // _NEURON_MODEL_LIF_CURR_IMPL_H_
