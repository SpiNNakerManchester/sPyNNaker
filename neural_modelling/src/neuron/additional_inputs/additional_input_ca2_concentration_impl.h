#ifndef _ADDITIONAL_INPUT_CA2_CONCENTRATIOn_H_
#define _ADDITIONAL_INPUT_CA2_CONCENTRATION_H_

#include "additional_input.h"

//----------------------------------------------------------------------------
// Model from Braeder, J., Senn, W., and Fusi, S.: Learning Real-World
// Stimuli in a Neural Network with Spike-Driven Synaptic Dynamics, Journal of
// Neural Computation, 2007
//----------------------------------------------------------------------------

typedef struct additional_input_t {

    // exp ( -(machine time step in ms)/(TauCa) )
    REAL    exp_TauCa;

    // Calcium current
    REAL    I_Ca2;

    // Influx of CA2 caused by each spike
    REAL    I_alpha;

} additional_input_t;

static input_t additional_input_get_input_value_as_current(
        additional_input_pointer_t additional_input,
        state_t membrane_voltage) {

    // Decay Ca2 trace
    additional_input->I_Ca2 *= additional_input->exp_TauCa;


    // Return 0.0 contribution from the Ca2
    return ZERO;
}

static void additional_input_has_spiked(
        additional_input_pointer_t additional_input) {
    // Apply influx of calcium to trace
    additional_input->I_Ca2 += additional_input->I_alpha;

    log_info("calcium concentration = %12.6k", additional_input->I_Ca2);
}

#endif // _ADDITIONAL_INPUT_CA2_CONCENTRATION_H_
