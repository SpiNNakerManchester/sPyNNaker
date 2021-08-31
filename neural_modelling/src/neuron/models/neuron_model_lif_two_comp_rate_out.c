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

#include "neuron_model_lif_two_comp_rate_impl.h"

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

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);

    // Get the dendrite input in nA
    input_t dendrite_input_this_timestep =
        exc_input[1] - inh_input[1] + neuron->I_offset;
    //input_t dendrite_input_this_timestep =
    //  exc_input[1] - inh_input[1];

    // update dendrite
    neuron->V = dendrite_input_this_timestep;

    // Get the soma input in nA
    //Isyn (exc_input[0] contains g_som * U_trgt)
    input_t soma_input_this_timestep =
        exc_input[0] + neuron->I_offset;

    //io_printf(IO_BUF, "dend input %k, soma input %k\n", dendrite_input_this_timestep, soma_input_this_timestep);

    // There is a teching signal
    if(soma_input_this_timestep != 0)
        neuron->U_membrane = (neuron->g_D * neuron->V + soma_input_this_timestep + external_bias) /
                                (neuron->g_L + neuron->g_D + neuron->g_som);
    // No teraching signal
    else
        neuron->U_membrane = (neuron->g_D * neuron->V) / (neuron->g_L + neuron->g_D);

    //io_printf(IO_BUF, "U %k, V %k\n", neuron->U_membrane, neuron->V);

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
