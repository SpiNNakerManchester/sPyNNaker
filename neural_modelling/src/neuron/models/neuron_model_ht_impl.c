#include "neuron_model_ht_impl.h"

#include <debug.h>

// simple Leaky I&F ODE
static inline void _ht_closed_form(
        neuron_pointer_t neuron, REAL V_prev, input_t input_this_timestep) {

//	neuron->A = 1;

//	neuron->B = 1;


    // update membrane voltage
//    neuron->V_membrane = neuron->A*V_prev +
//    		(neuron->B - input_this_timestep) * neuron->exp_TC -
//			(neuron->B - input_this_timestep);
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

	neuron_model_print_parameters(neuron);

	REAL total_exc = 0;
	REAL total_inh = 0;

	for (int i=0; i < num_excitatory_inputs; i++){
		total_exc += exc_input[i];
	}
	for (int i=0; i< num_inhibitory_inputs; i++){
		total_inh += inh_input[i];
	}

    // Get the input in nA
    input_t input_this_timestep =
        total_exc - total_inh + external_bias + neuron->I_offset;

    _ht_closed_form(
        neuron, neuron->V_membrane, input_this_timestep);

    return neuron->V_membrane;

}

void neuron_model_has_spiked(neuron_pointer_t neuron) {

    // reset membrane voltage
    neuron->V_membrane = neuron->E_Na;

}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->V_membrane;
}

void neuron_model_print_state_variables(restrict neuron_pointer_t neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
}

void neuron_model_print_parameters(restrict neuron_pointer_t neuron) {
    log_info("V membrane        = %k mv", neuron->V_membrane);
    log_info("g_Na	            = %k microS", neuron->g_Na);
    log_info("E_Na              = %k mV", neuron->E_Na);
    log_info("g_K               = %k microS", neuron->g_K);
    log_info("E_K               = %k mV", neuron->E_K);
    log_info("exp(-ms/(RC))     = %k ", neuron->exp_TC);
    log_info("I offset          = %k nA", neuron->I_offset);

}
