#include "my_neuron_model_impl.h"

#include <debug.h>

// The global parameters of this neuron model
static const global_neuron_params_t *global_params;

void neuron_model_set_global_neuron_params(
        const global_neuron_params_t *params) {

    // TODO: Store parameters as required
    global_params = params;
}

state_t neuron_model_state_update(
        uint16_t num_excitatory_inputs, const input_t* exc_input,
        uint16_t num_inhibitory_inputs, const input_t* inh_input,
        input_t external_bias, neuron_t *restrict neuron) {

    // This takes the input and generates an input value, assumed to be a
    // current.  Note that the conversion to current from conductance is done
    // outside of this function, so does not need to be repeated here.

    // Sum contributions from multiple inputs (if used)
    REAL total_exc = 0;
    REAL total_inh = 0;
    for (uint32_t i = 0; i < num_excitatory_inputs; i++) {
        total_exc += exc_input[i];
    }
    for (uint32_t i = 0; i < num_inhibitory_inputs; i++) {
        total_inh += inh_input[i];
    }

    input_t input_this_timestep =
            total_exc - total_inh + external_bias + neuron->I_offset;

    // TODO: Solve your equation here
    neuron->V += input_this_timestep;

    log_debug("TESTING TESTING V = %11.4k mv", neuron->V);

    // Return the state variable to be compared with the threshold value
    // to determine if the neuron has spikes (commonly the membrane voltage)
    // TODO: Update to return the correct variable
    return neuron->V;
}

state_t neuron_model_get_membrane_voltage(const neuron_t *neuron) {

    // TODO: Get the state value representing the membrane voltage
    return neuron->V;
}

void neuron_model_has_spiked(neuron_t *restrict neuron) {

    // TODO: Perform operations required to reset the state after a spike
    neuron->V = neuron->my_parameter;
}

void neuron_model_print_state_variables(const neuron_t *neuron) {

    // TODO: Print all state variables
    log_debug("V = %11.4k mv", neuron->V);
}

void neuron_model_print_parameters(const neuron_t *neuron) {

    // TODO: Print all neuron parameters
    log_debug("my parameter = %11.4k mv", neuron->my_parameter);
}
