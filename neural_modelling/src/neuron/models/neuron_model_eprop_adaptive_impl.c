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

#include "neuron_model_eprop_adaptive_impl.h"

#include <debug.h>

extern REAL learning_signal;
REAL local_eta;

// simple Leaky I&F ODE
static inline void lif_neuron_closed_form(
        neuron_pointer_t neuron, REAL V_prev, input_t input_this_timestep,
		REAL B_t) {

    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // update membrane voltage
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev))
    		- neuron->z * B_t; // this line achieves reset
}

void neuron_model_set_global_neuron_params(
        global_neuron_params_pointer_t params) {
    use(params);

    local_eta = params->eta;
    io_printf(IO_BUF, "local eta = %k\n", local_eta);
    // Does Nothing - no params
}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, input_t* exc_input,
		uint16_t num_inhibitory_inputs, input_t* inh_input,
		input_t external_bias, neuron_pointer_t neuron,
		REAL B_t) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);

//	REAL total_exc = 0;
//	REAL total_inh = 0;
//
//	for (int i=0; i < num_excitatory_inputs; i++) {
//		total_exc += exc_input[i];
//	}
//	for (int i=0; i< num_inhibitory_inputs; i++) {
//		total_inh += inh_input[i];
//	}
    // Get the input in nA
    input_t input_this_timestep =
    		exc_input[0] + exc_input[1] + neuron->I_offset;

    lif_neuron_closed_form(
            neuron, neuron->V_membrane, input_this_timestep, B_t);

    // If outside of the refractory period
    if (neuron->refract_timer <= 0) {
      	// Allow spiking again
       	neuron->A = 1;
    } else {
       	// Neuron cannot fire, as neuron->A=0;
        // countdown refractory timer
        neuron->refract_timer -= 1;
    }


    // ******************************************************************
    // Update Psi (pseudo-derivative) (done once for each postsynaptic neuron)
    // ******************************************************************
    REAL psi_temp1 = (neuron->V_membrane - neuron->B) * (1/neuron->b_0);
    REAL psi_temp2 = ((absk(psi_temp1)));
    neuron->psi =  ((1.0k - psi_temp2) > 0.0k)?
    		(1.0k/neuron->b_0) *
//			0.3k *
			(1.0k - psi_temp2) : 0.0k;

    uint32_t total_synapses_per_neuron = 1; //todo should this be fixed


//    neuron->psi = neuron->psi << 10;

    REAL rho = 0.998;


    neuron->L = learning_signal * neuron->w_fb;


    // All operations now need doing once per eprop synapse
    for (uint32_t syn_ind=0; syn_ind < total_synapses_per_neuron; syn_ind++){
		// ******************************************************************
		// Low-pass filter incoming spike train
		// ******************************************************************
    	neuron->syn_state[syn_ind].z_bar =
    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC
    			+ (1 - neuron->exp_TC) * neuron->syn_state[syn_ind].z_bar_inp; // updating z_bar is problematic, if spike could come and interrupt neuron update
    	// reset input (can't have more than one spike per timestep
        if (!syn_ind){
            io_printf(IO_BUF, "total synapses = %u\n"
                              "z_bar_inp = %k - z_bar = %k\n"
                              "L = %k = l * w_fb = %k * %k\n",
                total_synapses_per_neuron,
                neuron->syn_state[syn_ind].z_bar_inp, neuron->syn_state[syn_ind].z_bar,
                neuron->L, learning_signal, neuron -> w_fb);
        }
    	neuron->syn_state[syn_ind].z_bar_inp = 0;


		// ******************************************************************
		// Update eligibility vector
		// ******************************************************************
    	neuron->syn_state[syn_ind].el_a =
    			(neuron->psi * neuron->syn_state[syn_ind].z_bar) +
    		(rho - neuron->psi * neuron->beta) *
			neuron->syn_state[syn_ind].el_a;


    	// ******************************************************************
		// Update eligibility trace
		// ******************************************************************
    	REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
    		neuron->beta * neuron->syn_state[syn_ind].el_a);

    	neuron->syn_state[syn_ind].e_bar =
    			neuron->exp_TC * neuron->syn_state[syn_ind].e_bar
				+ (1 - neuron->exp_TC) * temp_elig_trace;

		// ******************************************************************
		// Update cached total weight change
		// ******************************************************************
    	REAL this_dt_weight_change =
    			-local_eta * neuron->L * neuron->syn_state[syn_ind].e_bar;
    	neuron->syn_state[syn_ind].delta_w += this_dt_weight_change;


//        io_printf(IO_BUF, "eta: %k, l: %k, ebar: %k, delta_w: %k, this dt: %k\n",
//            local_eta, neuron->L, neuron->syn_state[syn_ind].e_bar, neuron->syn_state[syn_ind].delta_w, this_dt_weight_change);

    }

    return neuron->V_membrane;
}

void neuron_model_has_spiked(neuron_pointer_t neuron) {
    // reset z to zero
    neuron->z = 0;

    // Set refractory timer
    neuron->refract_timer  = neuron->T_refract - 1;
    neuron->A = 0;
}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->V_membrane;
}

void neuron_model_print_state_variables(restrict neuron_pointer_t neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
}

void neuron_model_print_parameters(restrict neuron_pointer_t neuron) {
    io_printf(IO_BUF, "V reset       = %11.4k mv\n", neuron->V_reset);
    io_printf(IO_BUF, "V rest        = %11.4k mv\n", neuron->V_rest);

    io_printf(IO_BUF, "I offset      = %11.4k nA\n", neuron->I_offset);
    io_printf(IO_BUF, "R membrane    = %11.4k Mohm\n", neuron->R_membrane);

    io_printf(IO_BUF, "exp(-ms/(RC)) = %11.4k [.]\n", neuron->exp_TC);

    io_printf(IO_BUF, "T refract     = %u timesteps\n", neuron->T_refract);

    io_printf(IO_BUF, "learning      = %k n/a\n", neuron->L);

    io_printf(IO_BUF, "feedback w    = %k n/a\n", neuron->w_fb);
}
