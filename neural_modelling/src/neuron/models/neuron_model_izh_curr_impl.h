#ifndef _NEURON_MODEL_IZH_CURR_IMPL_H_
#define _NEURON_MODEL_IZH_CURR_IMPL_H_

#include "neuron_model.h"

typedef struct neuron_t {

    // nominally 'fixed' parameters
    REAL A;
    REAL B;
    REAL C;
    REAL D;

    // Variable-state parameters
    REAL V;
    REAL U;

    // offset current [nA]
    REAL I_offset;

    // current timestep - simple correction for threshold in beta version
    REAL this_h;

} neuron_t;

neuron_pointer_t neuron_model_izh_curr_impl_create(REAL A, REAL B, REAL C,
                                                   REAL D, REAL V, REAL U,
                                                   REAL I);

// function that converts the input into the real value to be used by the neuron
inline input_t neuron_model_convert_input(input_t input) {
    return input;
}

#endif   // _NEURON_MODEL_IZH_CURR_IMPL_H_
