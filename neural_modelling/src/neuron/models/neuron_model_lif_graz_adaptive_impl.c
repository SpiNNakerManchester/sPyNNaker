#include "neuron_model_lif_graz_adaptive_impl.h"
#include "../threshold_types/threshold_type_adaptive.h"
#include <debug.h>

// simple Leaky I&F ODE
static inline void _lif_neuron_closed_form(
        neuron_pointer_t neuron, REAL V_prev, input_t input_this_timestep, input_t B_t) {

    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // update membrane voltage
	// include threshold_reset contribution gated by z
    // (which a was gated by A at previous update)
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev)) - neuron->z * B_t;
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
		input_t B_t) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);


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

    _lif_neuron_closed_form(
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
