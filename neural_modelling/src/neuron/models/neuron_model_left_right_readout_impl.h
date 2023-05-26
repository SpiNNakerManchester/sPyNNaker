#ifndef _NEURON_MODEL_LIF_CURR_LEFT_RIGHT_READOUT_IMPL_H_
#define _NEURON_MODEL_LIF_CURR_LEFT_RIGHT_READOUT_IMPL_H_

#include "neuron_model.h"
#include "random.h"

#define SYNAPSES_PER_NEURON 250

extern REAL learning_signal;

typedef struct eprop_syn_state_t {
	REAL delta_w; // weight change to apply
	REAL z_bar_inp;
	REAL z_bar; // low-pass filtered spike train
	int32_t update_ready; // counter to enable batch update (i.e. don't perform on every spike).
}eprop_syn_state_t;

/////////////////////////////////////////////////////////////
// definition for LIF neuron parameters
typedef struct neuron_params_t {
    // membrane voltage [mV]
    REAL     V_init;

    // membrane resting voltage [mV]
    REAL     V_rest;

    // membrane capacitance [nF]
    REAL     c_m;

    // membrane decay time constant
    REAL     tau_m;

    // offset current [nA]
    REAL     I_offset;

    // post-spike reset membrane voltage [mV]
    REAL     V_reset;

    // refractory time of neuron [ms]
    REAL     T_refract_ms;

    // initial refractory timer value (saved)
    int32_t  refract_timer_init;

    // The time step in milliseconds
    REAL     time_step;

    REAL    L; // learning signal
    REAL w_fb; // feedback weight
    uint32_t window_size;

    // globals here
 	mars_kiss64_seed_t kiss_seed; // array of 4 values
	REAL ticks_per_second;
	REAL readout_V_0;
	REAL readout_V_1;
	REAL rate_on;
	REAL rate_off;
	REAL mean_0;
	REAL mean_1;
	REAL cross_entropy;
	uint32_t p_key;
	uint32_t p_pop_size;
	REAL eta;
	uint32_t number_of_cues;

    // array of synaptic states - peak fan-in of >250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];
};

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

    REAL    L; // learning signal
    REAL w_fb; // feedback weight
    uint32_t window_size;

    // former globals
 	mars_kiss64_seed_t kiss_seed; // array of 4 values
	REAL ticks_per_second;
	REAL readout_V_0;
	REAL readout_V_1;
	REAL rate_on;
	REAL rate_off;
	REAL mean_0;
	REAL mean_1;
	REAL cross_entropy;
	uint32_t p_key;
	uint32_t p_pop_size;
	REAL eta;
	uint32_t number_of_cues;

    // array of synaptic states - peak fan-in of >250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];

} neuron_t;

//! \brief Performs a ceil operation on an accum
//! \param[in] value The value to ceil
//! \return The ceil of the value
static inline int32_t lif_ceil_accum(REAL value) {
	int32_t bits = bitsk(value);
	int32_t integer = bits >> 15;
	int32_t fraction = bits & 0x7FFF;
	if (fraction > 0) {
	    return integer + 1;
	}
	return integer;
}

static inline void neuron_model_initialise(
		neuron_t *state, neuron_params_t *params, uint32_t n_steps_per_timestep) {
	REAL ts = kdivui(params->time_step, n_steps_per_timestep);
	state->V_membrane = params->V_init;
	state->V_rest = params->V_rest;
    state->R_membrane = kdivk(params->tau_m, params->c_m);
	state->exp_TC = expk(-kdivk(ts, params->tau_m));
	state->I_offset = params->I_offset;
    state->refract_timer = params->refract_timer_init;
	state->V_reset = params->V_reset;
	state->T_refract = lif_ceil_accum(kdivk(params->T_refract_ms, ts));

	// for everything else just copy across for now
	state->L = params->L;
	state->w_fb = params->w_fb;

    state->window_size = params->window_size;

    // former globals
    for (uint32_t n_seed = 0; n_seed < 4; n_seed++) {
    	state->kiss_seed[n_seed] = params->kiss_seed[n_seed]; // array of 4 values
    }

	state->ticks_per_second = params->ticks_per_second;
	state->readout_V_0 = params->readout_V_0;
	state->readout_V_1 = params->readout_V_1;
	state->rate_on = params->rate_on;
	state->rate_off = params->rate_off;
	state->mean_0 = params->mean_0;
	state->mean_1 = params->mean_1;
	state->cross_entropy = params->cross_entropy;
	state->p_key = params->p_key;
	state->p_pop_size = params->p_pop_size;
	state->eta = params->eta;
	state->number_of_cues = params->number_of_cues;

	log_info("Check p_key %u p_pop_size %u", params->p_key, params->p_pop_size);
	log_info("Check number_of_cues %u eta %k", params->number_of_cues, params->eta);
	log_info("mean_0 %k mean_1 %k rate_on %k rate_off %k readout_V_0 %k readout_V_1 %k",
			params->mean_0, params->mean_1, params->rate_on, params->rate_off,
			params->readout_V_0, params->readout_V_1);

	for (uint32_t n_syn = 0; n_syn < SYNAPSES_PER_NEURON; n_syn++) {
		state->syn_state[n_syn] = params->syn_state[n_syn];
	}
}

static inline void neuron_model_save_state(neuron_t *state, neuron_params_t *params) {
	params->V_init = state->V_membrane;
	params->refract_timer_init = state->refract_timer;
	params->L = state->L;
	params->w_fb = state->w_fb;

	for (uint32_t n_syn = 0; n_syn < SYNAPSES_PER_NEURON; n_syn++) {
		params->syn_state[n_syn] = state->syn_state[n_syn];
	}
}

// simple Leaky I&F ODE
static inline void lif_neuron_closed_form(
        neuron_t *neuron, REAL V_prev, input_t input_this_timestep) {

    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // update membrane voltage
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev));
}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, const input_t* exc_input,
		uint16_t num_inhibitory_inputs, const input_t* inh_input,
		input_t external_bias, REAL current_offset, neuron_t *restrict neuron,
		REAL B_t) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);
	use(B_t);

    // If outside of the refractory period
    if (neuron->refract_timer <= 0) {
        // Get the input in nA
        input_t input_this_timestep =
                exc_input[0] + exc_input[1] + neuron->I_offset + external_bias + current_offset;

        lif_neuron_closed_form(
            neuron, neuron->V_membrane, input_this_timestep);
    } else {

        // countdown refractory timer
        neuron->refract_timer -= 1;
    }

    uint32_t total_synapses_per_neuron = 100; //todo should this be fixed?

    neuron->L = learning_signal * neuron->w_fb; //* ((accum)syn_ind * -1.k);
    REAL local_eta = neuron->eta;

    // All subsequent operations now need doing once per eprop synapse
    for (uint32_t syn_ind=0; syn_ind < total_synapses_per_neuron; syn_ind++){
		// ******************************************************************
		// Low-pass filter incoming spike train
		// ******************************************************************
    	neuron->syn_state[syn_ind].z_bar =
    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC
    			+ (1.k - neuron->exp_TC) * neuron->syn_state[syn_ind].z_bar_inp; // updating z_bar is problematic, if spike could come and interrupt neuron update

		// ******************************************************************
		// Update cached total weight change
		// ******************************************************************
    	REAL this_dt_weight_change =
    			local_eta * neuron->L * neuron->syn_state[syn_ind].z_bar;

    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change;

    	// reset input (can't have more than one spike per timestep
        neuron->syn_state[syn_ind].z_bar_inp = 0;

    	// decrease timestep counter preventing rapid updates
        neuron->syn_state[syn_ind].update_ready -= 1;
    }

    return neuron->V_membrane;
}

void neuron_model_has_spiked(neuron_t *restrict neuron) {

    // reset membrane voltage
    neuron->V_membrane = neuron->V_reset;

    // reset refractory timer
    neuron->refract_timer  = neuron->T_refract;
}

state_t neuron_model_get_membrane_voltage(const neuron_t *neuron) {
    return neuron->V_membrane;
}

void neuron_model_print_state_variables(const neuron_t *neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
}

void neuron_model_print_parameters(const neuron_t *neuron) {
    log_debug("V reset       = %11.4k mv\n", neuron->V_reset);
    log_debug("V rest        = %11.4k mv\n", neuron->V_rest);
    log_debug("I offset      = %11.4k nA\n", neuron->I_offset);
    log_debug("R membrane    = %11.4k Mohm\n", neuron->R_membrane);
    log_debug("exp(-ms/(RC)) = %11.4k [.]\n", neuron->exp_TC);
    log_debug("T refract     = %u timesteps\n", neuron->T_refract);
    log_debug("learning      = %k n/a\n", neuron->L);
    log_debug("feedback w    = %k n/a\n", neuron->w_fb);
    log_debug("window size   = %u n/a\n", neuron->window_size);
    log_debug("T refract     = %u timesteps\n", neuron->T_refract);
}

#endif // _NEURON_MODEL_LIF_CURR_LEFT_RIGHT_READOUT_IMPL_H_
