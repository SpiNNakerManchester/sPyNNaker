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
    // Does Nothing - no params
}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, input_t* exc_input,
		uint16_t num_inhibitory_inputs, input_t* inh_input,
		input_t external_bias, neuron_pointer_t neuron,
		REAL B_t) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);

	REAL total_exc = 0;
	REAL total_inh = 0;

	for (int i=0; i < num_excitatory_inputs; i++) {
		total_exc += exc_input[i];
	}
	for (int i=0; i< num_inhibitory_inputs; i++) {
		total_inh += inh_input[i];
	}
    // Get the input in nA
    input_t input_this_timestep =
    		exc_input[0] - inh_input[0] + external_bias + neuron->I_offset;

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
    // REAL temp1 = (neuron->V_membrane - v_threshold_baseline) * (1/v_thresh)
    // REAL temp2 = ((1/v_th) * 0.3 * 1-(abs(temp1))
    // neuron->psi =  (temp2 > 0)? temp2 , 0;

    // All operations now need doing once per eprop synapse
//    for (int syn=0; syn < total_synapses_per_neuron; syn++){
    // ******************************************************************
    // Update eligibility vector
    // ******************************************************************
//    neuron->syn_state[syn_ind].ep_a; = neuron->psi * neuron->syn_state[syn_ind].z_bar +
//    		(global_params->rho - neuron->psi * global_params->beta) *
//    			neuron->syn_state[syn_ind].ep_a;


    // ******************************************************************
    // Update eligibility trace
    // ******************************************************************
//    REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
//    		global_params->beta * neuron->syn_state[syn_ind].ep_a);
//    neuron->syn_state[syn_ind].e_bar = "low pass filtered temp_elig_trace"


    // ******************************************************************
    // Update total weight change
    // ******************************************************************
//    uint16_t this_dt_weight_change = -global_params->eta * neuron->learning_sig * neuron->syn_state[syn_ind].e_bar;
//    neuron->syn_state[syn_ind].delta_w +=this_dt_weight_change;

//    }







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
    log_debug("V reset       = %11.4k mv", neuron->V_reset);
    log_debug("V rest        = %11.4k mv", neuron->V_rest);

    log_debug("I offset      = %11.4k nA", neuron->I_offset);
    log_debug("R membrane    = %11.4k Mohm", neuron->R_membrane);

    log_debug("exp(-ms/(RC)) = %11.4k [.]", neuron->exp_TC);

    log_debug("T refract     = %u timesteps", neuron->T_refract);
}
