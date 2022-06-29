#include "neuron_model_lif_v_hist_impl.h"

#include <debug.h>

// simple Leaky I&F ODE
static inline void _lif_neuron_closed_form(
        neuron_pointer_t neuron, REAL V_prev, input_t input_this_timestep) {

    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // update membrane voltage
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev));
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

	//neuron_model_print_parameters(neuron);

	// track previous timestep membrane voltage
    neuron->V_mem_hist = neuron->V_membrane;

    // If outside of the refractory period
    if (neuron->refract_timer <= 0) {



    	if (exc_input[1]>0){
    		// Teacher input received, so fire
    		neuron->V_membrane = 1024.0k;
    	}

    	if (inh_input[0]>0){
    		// Forced reset
    		neuron->V_membrane = neuron->V_reset;
                exc_input[0] = 0.0k;
                //io_printf(IO_BUF, "X\n");
    	}

    	// Otherwise evolve subthreshold dynamics
		REAL total_exc = 0;
		REAL total_inh = 0;



//		for (int i=0; i < num_excitatory_inputs; i++){
//			total_exc += exc_input[i];
//		}

		total_exc = exc_input[0];


		total_inh += inh_input[1];
		//for (int i=0; i< num_inhibitory_inputs; i++){
		//	total_inh += inh_input[i];
		//}
        // Get the input in nA
        input_t input_this_timestep =
            total_exc - total_inh + external_bias + neuron->I_offset;

        _lif_neuron_closed_form(
            neuron, neuron->V_membrane, input_this_timestep);
    } else {

        // countdown refractory timer
        neuron->refract_timer -= 1;
    }
    return neuron->V_membrane;
}

void neuron_model_has_spiked(neuron_pointer_t neuron) {

    // reset membrane voltage
    neuron->V_membrane = neuron->V_reset;

    // reset refractory timer
    neuron->refract_timer  = neuron->T_refract;
}


void neuron_model_set_v_hist(neuron_pointer_t neuron){
	neuron->V_mem_hist = 1000.0k;
}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->V_membrane;
}

void neuron_model_print_state_variables(restrict neuron_pointer_t neuron) {
//    io_printf(IO_BUF, "V membrane    = %11.4k mv", neuron->V_membrane);
}

void neuron_model_print_parameters(restrict neuron_pointer_t neuron) {
    io_printf(IO_BUF, "V reset       = %11.4k mv\n", neuron->V_reset);
    io_printf(IO_BUF, "V rest        = %11.4k mv\n", neuron->V_rest);

    io_printf(IO_BUF, "I offset      = %11.4k nA\n", neuron->I_offset);
    io_printf(IO_BUF, "R membrane    = %11.4k Mohm\n", neuron->R_membrane);

    io_printf(IO_BUF, "exp(-ms/(RC)) = %11.4k [.]\n", neuron->exp_TC);

    io_printf(IO_BUF, "T refract     = %u timesteps\n", neuron->T_refract);
    io_printf(IO_BUF, "V membrane    = %11.4k mv\n", neuron->V_membrane);
}
