#include "neuron_model_ht_impl.h"

#include <debug.h>

// simple Leaky I&F ODE
static inline void _ht_closed_form(
        neuron_pointer_t neuron, REAL V_prev, input_t input_this_timestep) {


//	REAL A = neuron->g_Na + neuron->g_K;
//	REAL B = (neuron->g_Na * neuron->E_Na) + (neuron->g_K * neuron->E_K);
//
//	REAL A_SPIKE = (neuron->g_Na + neuron->g_K) * neuron->tau_spike +
//			neuron->g_spike * neuron->tau_m;
//	REAL B_SPIKE = (B * neuron->tau_spike) + (neuron->tau_m * neuron->g_spike * neuron->E_K);
//
//	log_info("A_SPIKE: %k, B_SPIKE: %k", A_SPIKE, B_SPIKE);
//
////	REAL A;
////	REAL B;
//	REAL TC;

	if (neuron->ref_counter > 0){
//		A = (neuron->g_Na + neuron->g_K) * neuron->tau_spike +
//							neuron->g_spike * neuron->tau_m;
//
//		B = ((neuron->g_Na *neuron->E_Na +
//				neuron->g_K * neuron->E_K) * neuron->tau_spike)
//				+ (neuron->tau_m * neuron->g_spike * neuron->E_K);
//
//		TC = neuron->exp_TC_spike;

	    neuron->V_membrane = (V_prev -
	    		(neuron->B_SPIKE + input_this_timestep) * neuron->A_SPIKE_INV) * neuron->exp_TC_spike +
				((neuron->B_SPIKE + input_this_timestep) * neuron->A_SPIKE_INV);



		neuron->ref_counter--;

	} else {
//		A = (neuron->g_Na + neuron->g_K) * neuron->tau_spike;
//		B = ((neuron->g_Na * neuron->E_Na) + (neuron->g_K * neuron->E_K)) * neuron->tau_spike;
//		TC = neuron->exp_TC;

	    neuron->V_membrane = (V_prev -
	    		(neuron->B + (input_this_timestep * neuron->tau_spike)) * neuron->A_INV) * neuron->exp_TC +
				((neuron->B + (input_this_timestep * neuron->tau_spike)) * neuron->A_INV);
	}

//	log_info("A: %k, B: %k", A, B);
//
//    // update membrane voltage
//    neuron->V_membrane = (V_prev -
//    		(B + input_this_timestep)/A) * TC +
//			((B + input_this_timestep)/A);
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
    neuron->g_spike_var = neuron->g_spike;
    neuron->ref_counter += neuron->t_spike;

}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->V_membrane;
}

void neuron_model_print_state_variables(restrict neuron_pointer_t neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
}

void neuron_model_print_parameters(restrict neuron_pointer_t neuron) {
    log_debug("V membrane        = %k mv", neuron->V_membrane);
    log_debug("g_Na	            = %k microS", neuron->g_Na);
    log_debug("E_Na              = %k mV", neuron->E_Na);
    log_debug("g_K               = %k microS", neuron->g_K);
    log_debug("E_K               = %k mV", neuron->E_K);
    log_debug("exp(-ms/(RC))     = %k ", neuron->exp_TC);
    log_debug("tau_m             = %k ms", neuron->tau_m);
    log_debug("exp_TC_spike      = %k ", neuron->exp_TC_spike);
    log_debug("tau_spike         = %k ms", neuron->tau_spike);
    log_debug("I offset          = %k nA", neuron->I_offset);
    log_debug("g_spike_var       = %k microS", neuron->g_spike_var);
    log_debug("g_spike           = %k microS", neuron->g_spike);
    log_debug("t_spike           = %k ms", neuron->t_spike);
    log_debug("ref_counter       = %k ms", neuron->ref_counter);
    log_debug("A                  = %k", neuron->A);
    log_debug("B                  = %k", neuron->B);
    log_debug("A_SPIKE            = %k", neuron->A_SPIKE);
    log_debug("B_SPIKE            = %k", neuron->B_SPIKE);
    log_debug("A_INV              = %k", neuron->A_INV);
    log_debug("A_SPIKE_INV        = %k", neuron->A_SPIKE_INV);
}
