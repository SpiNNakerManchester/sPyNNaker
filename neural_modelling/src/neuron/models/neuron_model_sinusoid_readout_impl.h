#ifndef _NEURON_MODEL_SINUSOID_READOUT_IMPL_H_
#define _NEURON_MODEL_SINUSOID_READOUT_IMPL_H_

#include "neuron_model.h"
#include "random.h"
#include <debug.h>

#define SYNAPSES_PER_NEURON 250

//extern uint32_t time;
extern REAL learning_signal;
//extern REAL local_eta;


typedef struct eprop_syn_state_t {
	REAL delta_w; // weight change to apply
	REAL z_bar_inp;
	REAL z_bar; // low-pass filtered spike train
//	REAL el_a; // adaptive component of eligibility vector
//	REAL e_bar; // low-pass filtered eligibility trace
	uint32_t update_ready; // counter to enable batch update (i.e. don't perform on every spike).
}eprop_syn_state_t;

/////////////////////////////////////////////////////////////
// definition for LIF-sinusoid neuron parameters
struct neuron_params_t {
    // membrane voltage [mV]
    REAL     V_init;

    // membrane resting voltage [mV]
    REAL     V_rest;

    // membrane capacitance [nF]
    REAL     c_m;

    // membrane decay time constant
    REAL     tau_m;

    // offset current (nA)
    REAL     I_offset;

    // post-spike reset membrane voltage (mV)
    REAL     V_reset;

    // refractory time of neuron [ms]
    REAL     T_refract_ms;

    // initial refractory timer value (saved)
    int32_t  refract_timer_init;

    // The time step in milliseconds
    REAL     time_step;

    // TODO: double-check that everything above this point is needed

    REAL    L; // learning signal
    REAL w_fb; // feedback weight

    // former globals
    REAL target_V[1024];
   	REAL eta;

    // array of synaptic states - peak fan-in of 250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];
};


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

    // former globals
    REAL target_V[1024]; // this could be problematic for DTCM usage
   	REAL eta;

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

//typedef struct global_neuron_params_t {
//// 	mars_kiss64_seed_t spike_source_seed; // array of 4 values
////	REAL ticks_per_second;
////	REAL readout_V;
//	REAL target_V[1024];
//	REAL eta;
//} global_neuron_params_t;

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

	for (uint32_t n_v = 0; n_v < 1024; n_v++) {
		state->target_V[n_v] = params->target_V[n_v];
	}
	state->eta = params->eta;
//	local_eta = params->eta;

	for (uint32_t n_syn = 0; n_syn < SYNAPSES_PER_NEURON; n_syn++) {
		state->syn_state[n_syn] = params->syn_state[n_syn];
	}

}

static inline void neuron_model_save_state(neuron_t *state, neuron_params_t *params) {
	// TODO: probably more parameters need copying across at this point, syn_state for a start
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

//void neuron_model_set_global_neuron_params(
//        global_neuron_params_pointer_t params) {
//    use(params);
//
//    local_eta = params->eta;
//    io_printf(IO_BUF, "local eta = %k\n", local_eta);
//
//    // Does Nothing - no params
//}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, input_t* exc_input,
		uint16_t num_inhibitory_inputs, input_t* inh_input,
		input_t external_bias, REAL current_offset, neuron_t *restrict neuron,
		REAL B_t) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);
	use(B_t);

    // If outside of the refractory period
    if (neuron->refract_timer <= 0) {
//		REAL total_exc = 0;
//		REAL total_inh = 0;
//
//		total_exc += exc_input[0];
//		total_inh += inh_input[0];
//		for (int i=0; i < num_excitatory_inputs; i++){
//			total_exc += exc_input[i];
//		}
//		for (int i=0; i< num_inhibitory_inputs; i++){
//			total_inh += inh_input[i];
//		}
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

    neuron->L = learning_signal * neuron->w_fb;
    REAL local_eta = neuron->eta;

    // All operations now need doing once per eprop synapse
    for (uint32_t syn_ind=0; syn_ind < total_synapses_per_neuron; syn_ind++){
		// ******************************************************************
		// Low-pass filter incoming spike train
		// ******************************************************************
    	neuron->syn_state[syn_ind].z_bar =
    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC
//    			+ (1 - neuron->exp_TC) *
    			+
    			neuron->syn_state[syn_ind].z_bar_inp; // updating z_bar is problematic, if spike could come and interrupt neuron update


		// ******************************************************************
		// Update eligibility vector
		// ******************************************************************
//    	neuron->syn_state[syn_ind].el_a =
//    			(neuron->psi * neuron->syn_state[syn_ind].z_bar) +
//    		(rho - neuron->psi * neuron->beta) *
//			neuron->syn_state[syn_ind].el_a;


    	// ******************************************************************
		// Update eligibility trace
		// ******************************************************************
//    	REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
//    		neuron->beta * neuron->syn_state[syn_ind].el_a);
//
//    	neuron->syn_state[syn_ind].e_bar =
//    			neuron->exp_TC * neuron->syn_state[syn_ind].e_bar
//				+ (1 - neuron->exp_TC) * temp_elig_trace;

		// ******************************************************************
		// Update cached total weight change
		// ******************************************************************
    	REAL this_dt_weight_change =
//    			-local_eta * neuron->L * neuron->syn_state[syn_ind].e_bar;
    			local_eta * neuron->L * neuron->syn_state[syn_ind].z_bar;

    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change;
//    	if (!syn_ind || neuron->syn_state[syn_ind].z_bar){// || neuron->syn_state[syn_ind].z_bar_inp){
//            io_printf(IO_BUF, "total synapses = %u \t syn_ind = %u \t "
//                              "z_bar_inp = %k \t z_bar = %k \t time:%u\n"
//                              "L = %k = %k * %k = l * w_fb\n"
//                              "this dw = %k \t tot dw %k\n"
//                              ,
//                total_synapses_per_neuron,
//                syn_ind,
//                neuron->syn_state[syn_ind].z_bar_inp,
//                neuron->syn_state[syn_ind].z_bar,
//                time,
//                neuron->L, learning_signal, neuron -> w_fb,
//                this_dt_weight_change, neuron->syn_state[syn_ind].delta_w
//                );
//        }
    	// reset input (can't have more than one spike per timestep
        neuron->syn_state[syn_ind].z_bar_inp = 0;


    	// decrease timestep counter preventing rapid updates
    	if (neuron->syn_state[syn_ind].update_ready > 0){
    		neuron->syn_state[syn_ind].update_ready -= 1;
    	}

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
//    io_printf(IO_BUF, "V reset       = %11.4k mv\n", neuron->V_reset);
//    io_printf(IO_BUF, "V rest        = %11.4k mv\n", neuron->V_rest);
//
//    io_printf(IO_BUF, "I offset      = %11.4k nA\n", neuron->I_offset);
//    io_printf(IO_BUF, "R membrane    = %11.4k Mohm\n", neuron->R_membrane);
//
//    io_printf(IO_BUF, "exp(-ms/(RC)) = %11.4k [.]\n", neuron->exp_TC);
//
//    io_printf(IO_BUF, "T refract     = %u timesteps\n", neuron->T_refract);
//
//    io_printf(IO_BUF, "learning      = %k n/a\n", neuron->L);
//
//    io_printf(IO_BUF, "feedback w    = %k n/a\n\n", neuron->w_fb);
//
//    io_printf(IO_BUF, "T refract     = %u timesteps\n", neuron->T_refract);
//    io_printf(IO_BUF, "mean_isi_ticks  = %k\n", neuron->mean_isi_ticks);
//    io_printf(IO_BUF, "time_to_spike_ticks  = %k \n",
//    		neuron->time_to_spike_ticks);

//    io_printf(IO_BUF, "Seed 1: %u\n", neuron->spike_source_seed[0]);
//    io_printf(IO_BUF, "Seed 2: %u\n", neuron->spike_source_seed[1]);
//    io_printf(IO_BUF, "Seed 3: %u\n", neuron->spike_source_seed[2]);
//    io_printf(IO_BUF, "Seed 4: %u\n", neuron->spike_source_seed[3]);
////    io_printf(IO_BUF, "seconds per tick: %u\n", neuron->seconds_per_tick);
//    io_printf(IO_BUF, "ticks per second: %k\n", neuron->ticks_per_second);
}

#endif // _NEURON_MODEL_SINUSOID_READOUT_IMPL_H_
