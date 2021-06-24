#ifndef _NEURON_MODEL_SHD_READOUT_IMPL_H_
#define _NEURON_MODEL_SHD_READOUT_IMPL_H_

#include "neuron_model.h"
#include "random.h"

#define SYNAPSES_PER_NEURON 190


typedef struct eprop_syn_state_t {
	REAL delta_w; // weight change to apply
//	REAL z_bar_inp; // now all in z_bar
	REAL z_bar; // low-pass filtered spike train
//	REAL el_a; // adaptive component of eligibility vector
//	REAL e_bar; // low-pass filtered eligibility trace
	int32_t update_ready; // counter to enable batch update (i.e. don't perform on every spike).
}eprop_syn_state_t;

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

    uint32_t window_size;

    REAL    L; // learning signal
//    REAL w_fb; // feedback weight

    // array of synaptic states - peak fan-in of >250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];


    // Poisson compartment params
//    REAL mean_isi_ticks;
//    REAL time_to_spike_ticks;
//
//    int32_t time_since_last_spike;
//    REAL rate_at_last_setting;
//    REAL rate_update_threshold;


//    // Should be in global params
//    mars_kiss64_seed_t spike_source_seed; // array of 4 values
////    UFRACT seconds_per_tick;
//    REAL ticks_per_second;

} neuron_t;

typedef struct global_neuron_params_t {
// 	mars_kiss64_seed_t spike_source_seed; // array of 4 values
//	REAL ticks_per_second;
//	REAL readout_V[20];
	REAL eta;
	uint8_t target_V[1002];
} global_neuron_params_t;

#endif // _NEURON_MODEL_SINUSOID_READOUT_IMPL_H_
