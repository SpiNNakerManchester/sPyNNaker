#ifndef _NEURON_MODEL_LIF_COND_IMPL_H_
#define _NEURON_MODEL_LIF_COND_IMPL_H_

#include "neuron_model.h"

/////////////////////////////////////////////////////////////
// definition for LIF neuron
typedef struct neuron_t {

    // membrane voltage threshold at which neuron spikes [mV]
    REAL     V_thresh;

    // post-spike reset membrane voltage [mV]
    REAL     V_reset;

    // membrane resting voltage [mV]
    REAL     V_rest;

    // membrane resistance [some multiplier of Ohms, TBD probably MegaOhm]
    REAL     R_membrane;

    // reversal voltage - Excitatory [mV]
    REAL     V_rev_E;

    // reversal voltage - Inhibitory [mV]
    REAL     V_rev_I;

    // membrane voltage [mV]
    REAL     V_membrane;

    // offset current [nA] but take care because actually 'per timestep charge'
    REAL     I_offset;

    // 'fixed' computation parameter - time constant multiplier for
    // closed-form solution
    // exp( -(machine time step in ms)/(R * C) ) [.]
    REAL     exp_TC;

    // countdown to end of next refractory period [timesteps]
    int32_t  refract_timer;

    // refractory time of neuron [timesteps]
    int32_t  T_refract;

} neuron_t;

typedef struct global_neuron_params_t {
} global_neuron_params_t;

//
neuron_pointer_t neuron_model_lif_cond_impl_create(
    REAL V_thresh, REAL V_reset, REAL V_rest, REAL V_rev_E, REAL V_rev_I,
    REAL R, int32_t T_refract, REAL V, REAL I, int32_t refract_timer,
    REAL exp_tc);

// function that converts the input into the real value to be used by the neuron
inline input_t neuron_model_convert_input(input_t input) {
    return input >> 10;
}

#endif // _NEURON_MODEL_LIF_COND_IMPL_H_
