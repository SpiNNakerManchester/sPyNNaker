#ifndef _NEURON_IZH_CURR_IMPL_
#define _NEURON_IZH_CURR_IMPL_

#include  "neuron.h"

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

neuron_pointer_t neuron_izh_curr_impl_create( REAL A, REAL B, REAL C, REAL D,
        REAL V, REAL U, REAL I);

#endif   // _NEURON_IZH_CURR_IMPL_
