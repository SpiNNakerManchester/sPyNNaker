#ifndef _NEURON_MODEL_LIF_CURR_IMPL_H_
#define _NEURON_MODEL_LIF_CURR_IMPL_H_

#include "neuron_model.h"

/////////////////////////////////////////////////////////////
// definition for LIF neuron parameters
typedef struct neuron_t {

    // membrane voltage threshold at which neuron spikes [mV]
    REAL     V_thresh;

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

//! \creates a neuron parameter strut given the neural parameters
//! \param[in] V_thresh membrane voltage threshold at which neuron spikes [mV]
//! \param[in] V_reset post-spike reset membrane voltage [mV]
//! \param[in] V_rest membrane resting voltage [mV]
//! \param[in] R membrane resistance
//! \param[in] T_refract refractory time of neuron [ms/10]
//! \param[in] V initial membrane voltage
//! \param[in] I offset input current
//! \param[in] refract_timer count down to end of next refractory period
//! \param[in] exp_tc time constant multiplier for closed-form solution
//! \return the corresponding neuron_t with the correct parameters instantiated.
neuron_pointer_t neuron_model_lif_curr_impl_create(
    REAL V_thresh, REAL V_reset, REAL V_rest, REAL R,
    int32_t T_refract, REAL V, REAL I, int32_t refract_timer, REAL exp_tc);

//! \function that converts the input into the real value to be used by the
//! neuron
//! \param[in] input the input buffer that needs converting for use by the
//! neuron
//! \return the converted input buffer which has been converted for use by the
//! neuron
static inline input_t neuron_model_convert_input(input_t input) {
    return input;
}

#endif // _NEURON_MODEL_LIF_CURR_IMPL_H_

