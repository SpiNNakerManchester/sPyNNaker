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

#include "neuron_model_pyramidal_impl.h"

#include <debug.h>

void neuron_model_set_global_neuron_params(
        global_neuron_params_pointer_t params) {
    use(params);
    // Does Nothing - no params
}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, input_t* exc_input,
		uint16_t num_inhibitory_inputs, input_t* inh_input,
		input_t external_bias, neuron_pointer_t neuron) {

	use(num_excitatory_inputs);
	use(num_inhibitory_inputs);

	log_debug("Exc A: %12.6k, Exc B: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh A: %12.6k, Inh B: %12.6k", inh_input[0], inh_input[1]);

    // Get the apical dendrite input in nA
    input_t apical_dendrite_input_this_timestep =
        exc_input[0] - inh_input[0] + external_bias + neuron->I_offset;

    // Get the basal dendrite input in nA
    input_t basal_dendrite_input_this_timestep =
        exc_input[1] - inh_input[1] + external_bias + neuron->I_offset;

    // update dendrites
    neuron->Va = apical_dendrite_input_this_timestep;
    neuron->Vb = basal_dendrite_input_this_timestep;


    //io_printf(IO_BUF, "apical input %k, basal input %k\n", apical_dendrite_input_this_timestep, basal_dendrite_input_this_timestep);

    neuron->U_membrane = (neuron->g_B * neuron->Vb + neuron->g_A * neuron->Va) /
                            (neuron->g_L + neuron->g_B + neuron->g_A);

    //io_printf(IO_BUF, "U %k, Va %k, Vb %k\n", neuron->U_membrane, neuron->Va, neuron->Vb);

    return neuron->U_membrane;
}

void neuron_model_has_spiked(neuron_pointer_t neuron) {
    use(neuron);
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

}