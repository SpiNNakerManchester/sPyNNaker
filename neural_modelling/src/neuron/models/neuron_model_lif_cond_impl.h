#ifndef _NEURON_MODEL_LIF_COND_IMPL_H_
#define _NEURON_MODEL_LIF_COND_IMPL_H_

#include "neuron_model.h"

// only works properly for 1000, 700, 400 microsec timesteps
//#define CORRECT_FOR_REFRACTORY_GRANULARITY

//#define CORRECT_FOR_THRESHOLD_GRANULARITY

// 9% slower than standard but inevitably more accurate(?) might over-compensate
//#define SIMPLE_COMBINED_GRANULARITY

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

    // [kHz!] only necessary if one wants to use ODE solver because allows
    // multiply and host double prec to calc
    // - UNSIGNED ACCUM & unsigned fract much slower
    REAL     one_over_tauRC;

    // countdown to end of next refractory period [ms/10]
    // - 3 secs limit do we need more? Jan 2014
    int32_t  refract_timer;

    // refractory time of neuron [ms/10]
    int32_t  T_refract;

#ifdef SIMPLE_COMBINED_GRANULARITY

    // store the 3 internal timestep to avoid granularity
    REAL     eTC[3];
#endif
#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY

    // which period previous spike happened to approximate threshold crossing
    uint8_t prev_spike_code;

    // store the 3 internal timestep to avoid granularity
    REAL     eTC[3];
#endif
#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY

    // approx corrections for release from refractory period
    uint8_t  ref_divisions[2];

    // store the 3 internal timestep to avoid granularity
    REAL     eTC[3];
#endif

} neuron_t;

//
neuron_pointer_t neuron_model_lif_cond_impl_create(
    REAL V_thresh, REAL V_reset, REAL V_rest, REAL V_rev_E, REAL V_rev_I,
    REAL one_over_tauRC, REAL R, int32_t T_refract, REAL V, REAL I,
    int32_t refract_timer, REAL exp_tc );

// function that converts the input into the real value to be used by the neuron
inline input_t neuron_model_convert_input(input_t input) {
    return input >> 10;
}

#endif // _NEURON_MODEL_LIF_COND_IMPL_H_
