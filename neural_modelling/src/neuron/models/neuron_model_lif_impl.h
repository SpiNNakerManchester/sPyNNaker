#ifndef _NEURON_MODEL_LIF_CURR_IMPL_H_
#define _NEURON_MODEL_LIF_CURR_IMPL_H_

#include "neuron_model.h"

/////////////////////////////////////////////////////////////
// definition for LIF neuron parameters
typedef struct neuron_t {

    // post-spike reset membrane voltage [mV]
    REAL     V_reset;

    // membrane resting voltage [mV]
    REAL     V_rest;

    // membrane resistance [some multiplier of Ohms, TBD probably MegaOhm]
    REAL     R_membrane;

    // membrane voltage [mV]
    REAL     V_membrane;

    // offset current [nA] but take care because actually 'per timestep charge'
    REAL	 I_offset;

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

#endif // _NEURON_MODEL_LIF_CURR_IMPL_H_

