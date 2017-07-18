#ifndef _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_
#define _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_

#include <neuron/additional_inputs/additional_input.h>

//----------------------------------------------------------------------------
// Model from Liu, Y. H., & Wang, X. J. (2001). Spike-frequency adaptation of
// a generalized leaky integrate-and-fire model neuron. Journal of
// Computational Neuroscience, 10(1), 25-45. doi:10.1023/A:1008916026143
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

    // Return the Ca2
    return -additional_input->I_Ca2;
}

static void additional_input_has_spiked(
        additional_input_pointer_t additional_input) {
    // Apply influx of calcium to trace
    additional_input->I_Ca2 += additional_input->I_alpha;
}

#endif // _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_
