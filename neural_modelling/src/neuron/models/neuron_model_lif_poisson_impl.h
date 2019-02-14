#ifndef _NEURON_MODEL_LIF_CURR_POISSON_IMPL_H_
#define _NEURON_MODEL_LIF_CURR_POISSON_IMPL_H_

#include "neuron_model.h"
#include "random.h"

/////////////////////////////////////////////////////////////
// definition for LIF neuron parameters
typedef struct neuron_t {
    // membrane voltage [mV]
    REAL     V_membrane;

    // membrane resting voltage [mV]
    REAL     V_rest;

    // membrane resistance [MOhm]
    REAL     R_membrane;

    // 'fixed' computation parameter - time constant multiplier for
    // closed-form solution
    // exp(-(machine time step in ms)/(R * C)) [.]
    REAL     exp_TC;

    // offset current [nA]
    REAL     I_offset;

    // countdown to end of next refractory period [timesteps]
    int32_t  refract_timer;

    // post-spike reset membrane voltage [mV]
    REAL     V_reset;

    // refractory time of neuron [timesteps]
    int32_t  T_refract;


    // Poisson compartment params
    REAL mean_isi_ticks;
    REAL time_to_spike_ticks;

    // Should be in global params
    mars_kiss64_seed_t spike_source_seed; // array of 4 values
    UFRACT seconds_per_tick;
    REAL ticks_per_second;

} neuron_t;

typedef struct global_neuron_params_t {
////	mars_kiss64_seed_t spike_source_seed; // array of 4 values
//	UFRACT seconds_per_tick;
//	REAL ticks_per_second;
} global_neuron_params_t;

#endif // _NEURON_MODEL_LIF_CURR_POISSON_IMPL_H_
