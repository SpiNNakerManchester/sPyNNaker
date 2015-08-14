#include "neuron_model_lif_cond_impl.h"
#include "../../common/constants.h"

#include <debug.h>

// simple Leaky I&F ODE - discrete changes elsewhere -  assumes 1ms timestep?
static inline void _lif_neuron_closed_form(
        neuron_pointer_t neuron, REAL V_prev, input_t input_this_timestep) {

    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // update membrane voltage
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev));
}

// ODE solver has just set neuron->V which is current state of membrane voltage
static inline void _neuron_discrete_changes(neuron_pointer_t neuron) {

    // reset membrane voltage
    neuron->V_membrane = neuron->V_reset;

    // reset refractory timer
    neuron->refract_timer  = neuron->T_refract;
}

void neuron_model_set_global_neuron_params(
        global_neuron_params_pointer_t params) {
    use(params);

    // Does Nothing - no params
}

bool neuron_model_state_update(input_t exc_input, input_t inh_input,
                               input_t external_bias, neuron_pointer_t neuron) {

    bool spike = false;
    REAL V_last = neuron->V_membrane;

    // If outside of the refractory period
    if (neuron->refract_timer < 1) {

        // Get the input in nA
        input_t input_this_timestep = exc_input * (neuron->V_rev_E - V_last)
                                      + inh_input * (neuron->V_rev_I - V_last)
                                      + external_bias + neuron->I_offset;

        _lif_neuron_closed_form(neuron, V_last, input_this_timestep);

        // has it spiked?
        spike = REAL_COMPARE(neuron->V_membrane, >=, neuron->V_thresh);

        if (spike) {
            _neuron_discrete_changes(neuron);
        }
    } else {

        // countdown refractory timer
        neuron->refract_timer -= 1;
    }

    return spike;
}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->V_membrane;
}

// printout of neuron definition and state variables
void neuron_model_print(restrict neuron_pointer_t neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
    log_debug("V thresh      = %11.4k mv", neuron->V_thresh);
    log_debug("V reset       = %11.4k mv", neuron->V_reset);
    log_debug("V rest        = %11.4k mv", neuron->V_rest);

    log_info( "V reversal E  = %11.4k mv", neuron->V_rev_E);
    log_info( "V reversal I  = %11.4k mv", neuron->V_rev_I);

    log_debug("I offset      = %11.4k nA", neuron->I_offset);
    log_debug("R membrane    = %11.4k Mohm", neuron->R_membrane);

    log_debug("exp(-ms/(RC)) = %11.4k [.]", neuron->exp_TC);

    log_debug("T refract     = %u timesteps", neuron->T_refract);
}

//
neuron_pointer_t neuron_model_lif_cond_impl_create(
        REAL V_thresh, REAL V_reset, REAL V_rest, REAL V_rev_E, REAL V_rev_I,
        REAL R, int32_t T_refract, REAL V, REAL I, int32_t refract_timer,
        REAL exp_tc) {
    neuron_pointer_t neuron = spin1_malloc(sizeof(neuron_t));

    neuron->V_membrane = V;
    neuron->V_thresh = V_thresh;
    neuron->V_reset = V_reset;
    neuron->V_rest = V_rest;

    neuron->V_rev_E = V_rev_E;
    neuron->V_rev_I = V_rev_I;

    neuron->I_offset = I;
    neuron->R_membrane = R;
    neuron->exp_TC = exp_tc;

    neuron->T_refract = T_refract;
    neuron->refract_timer = refract_timer;

    return neuron;
}
