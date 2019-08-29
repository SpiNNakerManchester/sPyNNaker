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

#include "neuron_model_lif_two_comp_impl.h"

#include <debug.h>

// simple Leaky I&F ODE
static inline void lif_neuron_closed_form(
        neuron_pointer_t neuron, REAL U_prev, input_t input_this_timestep) {
    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->U_rest;

    // update membrane voltage
    neuron->U_membrane = alpha - (neuron->exp_TC * (alpha - U_prev));
}

void neuron_model_set_global_neuron_params(
        global_neuron_params_pointer_t params) {
    use(params);
    // Does Nothing - no params
}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, input_t* exc_input,
		uint16_t num_inhibitory_inputs, input_t* inh_input,
		input_t external_bias, neuron_pointer_t neuron) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);

    // If outside of the refractory period
    if (neuron->refract_timer <= 0) {

        // Get the soma input in nA
        input_t soma_input_this_timestep =
                exc_input[0] - inh_input[0] + neuron->I_offset;

        // Get the dendrite input in nA
        input_t dendrite_input_this_timestep =
                exc_input[1] - inh_input[1];




        // update dendrite
        neuron->V = neuron->exp_TC_dend * neuron->V + dendrite_input_this_timestep;
//        neuron->V_star = neuron->V * neuron->V_star_cond;

        REAL R_m = 10.0k;
        REAL g_L = 0.1k;
        neuron->U_membrane = ((neuron->U_membrane) - ((neuron->V * g_L + soma_input_this_timestep) * neuron->V_star_cond)) * neuron->exp_TC
        		+ ((neuron->V * g_L + soma_input_this_timestep) * neuron->V_star_cond);
//        // update soma
//        lif_neuron_closed_form(
//                neuron, neuron->U_membrane, soma_input_this_timestep);



    } else {
        // countdown refractory timer
        neuron->refract_timer--;
    }
    return neuron->U_membrane;
}

void neuron_model_has_spiked(neuron_pointer_t neuron) {
//    // reset membrane voltage
//    neuron->U_membrane = neuron->U_reset;
//
//    // reset refractory timer
//    neuron->refract_timer  = neuron->T_refract;
}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->U_membrane;
}

void neuron_model_print_state_variables(restrict neuron_pointer_t neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->U_membrane);
}

void neuron_model_print_parameters(restrict neuron_pointer_t neuron) {
    log_debug("V reset       = %11.4k mv", neuron->U_reset);
    log_debug("V rest        = %11.4k mv", neuron->U_rest);

    log_debug("I offset      = %11.4k nA", neuron->I_offset);
    log_debug("R membrane    = %11.4k Mohm", neuron->R_membrane);

    log_debug("exp(-ms/(RC)) = %11.4k [.]", neuron->exp_TC);

    log_debug("T refract     = %u timesteps", neuron->T_refract);
}
