#ifndef _NEURON_MODEL_IZH_CURR_IMPL_H_
#define _NEURON_MODEL_IZH_CURR_IMPL_H_

#include "neuron_model_interface.h"

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

    // current timestep - simple correction for threshold
    REAL this_h;

} neuron_t;

typedef struct global_neuron_params_t {
    REAL machine_timestep_ms;
} global_neuron_params_t;

#endif   // _NEURON_MODEL_IZH_CURR_IMPL_H_
