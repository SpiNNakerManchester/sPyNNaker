#ifndef _NEURON_MODEL_HT_IMPL_H_
#define _NEURON_MODEL_HT_IMPL_H_

#include "neuron_model.h"

/////////////////////////////////////////////////////////////
// definition for LIF neuron parameters
typedef struct neuron_t {
    // membrane voltage [mV]
    REAL V_membrane;

    // membrane resting voltage [mV]
    REAL g_Na;

    // membrane resistance [MOhm]
    REAL E_Na;

    // offset current [nA]
    REAL g_K;

    // countdown to end of next refractory period [timesteps]
    REAL E_K;

    // 'fixed' computation parameter - time constant multiplier for
    // closed-form solution
    // exp(-(machine time step in ms)/(R * C)) [.]
    REAL exp_TC;

    // post-spike reset membrane voltage [mV]
    REAL I_offset;

} neuron_t;

typedef struct global_neuron_params_t {
} global_neuron_params_t;

#endif // _NEURON_MODEL_HT_IMPL_H_
