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
#include <neuron/decay.h>

#define SYNAPSES_PER_NEURON 1024


typedef struct eprop_syn_state_t {
	REAL delta_w; // weight change to apply
	REAL z_bar_inp;
	REAL z_bar; // low-pass filtered spike train
	REAL el_a; // adaptive component of eligibility vector
	REAL e_bar; // low-pass filtered eligibility trace
	int32_t update_ready; // counter to enable batch update (i.e. don't perform on every spike).
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

    // Threshold paramters
    REAL B; // Capital B(t)
    REAL b; // b(t)
    REAL b_0; // small b^0
    decay_t e_to_dt_on_tau_a; // rho
    REAL beta;
    decay_t adpt; // (1-rho)
    REAL scalar;

    REAL    L; // learning signal
    uint32_t window_size;
    uint32_t number_of_cues;
    uint32_t input_synapses;
    uint32_t rec_synapses;
    REAL neuron_rate;
    REAL v_mem_lr;
    REAL firing_lr;
    REAL w_fb[20]; // feedback weight

    // array of synaptic states - peak fan-in of 250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];

} neuron_t;

typedef struct global_neuron_params_t {
	REAL core_pop_rate;
	REAL core_target_rate;
	REAL rate_exp_TC;
	REAL eta; // learning rate
} global_neuron_params_t;


static inline void threshold_type_update_threshold(state_t z,
		neuron_pointer_t threshold_type){

//	_print_threshold_params(threshold_type);


	s1615 temp1 = decay_s1615(threshold_type->b, threshold_type->e_to_dt_on_tau_a);
	s1615 temp2 = decay_s1615(threshold_type->scalar, threshold_type->adpt) * z;

	threshold_type->b = temp1
			+ temp2;
	// io_printf(IO_BUF, "temp1: %k; temp2: %k\n", temp1, temp2);

//	// Evolve threshold dynamics (decay to baseline) and adapt if z=nonzero
//	// Update small b (same regardless of spike - uses z from previous timestep)
//	threshold_type->b =
//			decay_s1615(threshold_type->b, threshold_type->e_to_dt_on_tau_a)
//			+ decay_s1615(1000k, threshold_type->adpt) // fold scaling into decay to increase precision
//			* z; // stored on neuron
//
//    io_printf(IO_BUF, "\nbefore B = %k, temp1 = %k, temp2 = %k, b = %k, b_0 = %k, beta = %k, z = %k",
//                    threshold_type->B, temp1, temp2, threshold_type->b,
//                    threshold_type->b_0, threshold_type->beta, z);
	// Update large B
	threshold_type->B = threshold_type->b_0 +
			threshold_type->beta*threshold_type->b;
//    io_printf(IO_BUF, "\nafter B = %k\n\n", threshold_type->B);
}




#endif // _NEURON_MODEL_LIF_CURR_IMPL_H_
