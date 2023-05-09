/*
 * Copyright (c) 2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _NEURON_MODEL_EPROP_ADAPTIVE_IMPL_H_
#define _NEURON_MODEL_EPROP_ADAPTIVE_IMPL_H_

#include "neuron_model.h"
#include <neuron/decay.h>

// TODO: Can this be set up somehow as a value that's passed in?
#define SYNAPSES_PER_NEURON 250

static bool printed_value = false;
extern REAL learning_signal;
extern uint32_t time; // this is probably unnecessary
extern uint32_t syn_dynamics_neurons_in_partition;

typedef struct eprop_syn_state_t {
	REAL delta_w; // weight change to apply
	REAL z_bar_inp;
	REAL z_bar; // low-pass filtered spike train
	REAL el_a; // adaptive component of eligibility vector
	REAL e_bar; // low-pass filtered eligibility trace
	int32_t update_ready; // counter to enable batch update (i.e. don't perform on every spike).
} eprop_syn_state_t;

// eprop adaptive neuron parameters
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

    // Neuron spike train
    REAL z;

    // refractory multiplier - to allow evolution of neuronal dynamics during
    // refractory period
    REAL A;

    // pseudo derivative
    REAL     psi;

    // Threshold paramters
    REAL B; // Capital B(t)
    REAL b; // b(t)
    REAL b_0; // small b^0
    uint32_t tau_a;
    REAL beta;
    REAL scalar;

    REAL    L; // learning signal
    REAL w_fb; // feedback weight
    uint32_t window_size;
    uint32_t number_of_cues;

    REAL pop_rate;
	REAL target_rate;
	REAL tau_err;
	REAL eta; // learning rate

    // array of synaptic states - peak fan-in of 250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];
};


//! eprop neuron state
struct neuron_t {
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

    // Neuron spike train
    REAL z;

    // refractory multiplier - to allow evolution of neuronal dynamics during
    // refractory period
    REAL A;

    // pseudo derivative
    REAL     psi;

    // Threshold paramters
    REAL B; // Capital B(t)
    REAL b; // b(t)
    REAL b_0; // small b^0
    decay_t e_to_dt_on_tau_a; // rho
    REAL beta;
    decay_t adpt; // (1-rho)
    REAL scalar;

    REAL    L; // learning signal
    REAL w_fb; // feedback weight
    uint32_t window_size;
    uint32_t number_of_cues;

    // Former "global" parameters
	REAL core_pop_rate;
	REAL core_target_rate;
	REAL rate_exp_TC;
	REAL eta; // learning rate

    // array of synaptic states - peak fan-in of 250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];
};


// TODO: use the threshold type for this instead
static inline void threshold_type_update_threshold(state_t z,
		neuron_t *threshold_type){

	// TODO: Better names for these variables
	s1615 temp1 = decay_s1615(threshold_type->b, threshold_type->e_to_dt_on_tau_a);
	s1615 temp2 = decay_s1615(threshold_type->scalar, threshold_type->adpt) * z;

	threshold_type->b = temp1 + temp2;

	// Update large B
	threshold_type->B = threshold_type->b_0 +
			threshold_type->beta*threshold_type->b;
}

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

//	log_info("V_membrane %k V_rest %k R_membrane %k exp_TC %k I_offset %k refract_timer %k V_reset %k T_refract_ms %k T_refract %d",
//			state->V_membrane, state->V_rest, state->R_membrane, state->exp_TC, state->I_offset,
//			state->refract_timer, state->V_reset, params->T_refract_ms, state->T_refract);

	// for everything else just copy across for now
	state->z = params->z;
	state->A = params->A;
	state->psi = params->psi;
	state->B = params->B;
	state->b = params->b;
	state->b_0 = params->b_0;
	state->e_to_dt_on_tau_a = expk(-kdivk(ts, params->tau_a));
	state->beta = params->beta;
	state->adpt = 1 - expk(-kdivk(ts, params->tau_a));
	state->scalar = params->scalar;
	state->L = params->L;
	state->w_fb = params->w_fb;
	state->window_size = params->window_size;
	state->number_of_cues = params->number_of_cues;

//	log_info("Check: z %k A %k psi %k B %k b %k b_0 %k window_size %u",
//			state->z, state->A, state->psi, state->B, state->b, state->b_0, state->window_size);

	state->core_pop_rate = params->pop_rate;
	state->core_target_rate = params->target_rate;
	state->rate_exp_TC = expk(-kdivk(ts, params->tau_err));
	state->eta = params->eta;

//	log_info("Check: core_pop_rate %k core_target_rate %k rate_exp_TC %k eta %k",
//			state->core_pop_rate, state->core_target_rate, state->rate_exp_TC, state->eta);

	for (uint32_t n_syn = 0; n_syn < SYNAPSES_PER_NEURON; n_syn++) {
		state->syn_state[n_syn] = params->syn_state[n_syn];
	}
}

static inline void neuron_model_save_state(neuron_t *state, neuron_params_t *params) {
	params->V_init = state->V_membrane;
	params->refract_timer_init = state->refract_timer;
	params->z = state->z;
	params->A = state->A;
	params->psi = state->psi;
	params->B = state->B;
	params->b = state->b;
	params->b_0 = state->b_0;
	params->beta = state->beta;
	params->scalar = state->scalar;
	params->L = state->L;
	params->w_fb = state->w_fb;
	params->window_size = state->window_size;
	params->number_of_cues = state->number_of_cues;

	params->pop_rate = state->core_pop_rate;
	params->target_rate = state->core_target_rate;
	params->eta = state->eta;

	for (uint32_t n_syn = 0; n_syn < SYNAPSES_PER_NEURON; n_syn++) {
		params->syn_state[n_syn] = state->syn_state[n_syn];
	}
}

// simple Leaky I&F ODE
static inline void lif_neuron_closed_form(
        neuron_t *neuron, REAL V_prev, input_t input_this_timestep,
		REAL B_t) {
    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // update membrane voltage
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev))
    		- neuron->z * B_t; // this line achieves reset (?)
}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, input_t* exc_input,
		uint16_t num_inhibitory_inputs, input_t* inh_input,
		input_t external_bias, REAL current_offset, neuron_t *restrict neuron,  // this has a *restrict on it in LIF?
		REAL B_t) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);

    // Get the input in nA
    input_t input_this_timestep =
    		exc_input[0] + exc_input[1] + neuron->I_offset + external_bias + current_offset;

    lif_neuron_closed_form(
            neuron, neuron->V_membrane, input_this_timestep, B_t);

    // If outside of the refractory period
    if (neuron->refract_timer <= 0) {
      	// Allow spiking again
       	neuron->A = 1;
    } else {
       	// Neuron cannot fire, as neuron->A=0;
        // countdown refractory timer
        neuron->refract_timer -= 1;
    }

    // ******************************************************************
    // Update Psi (pseudo-derivative) (done once for each postsynaptic neuron)
    // ******************************************************************
    REAL psi_temp1 = (neuron->V_membrane - neuron->B) * (1/neuron->b_0);
    REAL psi_temp2 = ((absk(psi_temp1)));
    neuron->psi =  ((1.0k - psi_temp2) > 0.0k)?
    		(1.0k/neuron->b_0) *
			0.3k * //todo why is this commented?
			(1.0k - psi_temp2) : 0.0k;
    neuron->psi *= neuron->A;

	// This parameter is OK to update, as the actual size of the array is set in the
    // header file, which matches the Python code. This should make it possible to
    // do a pause and resume cycle and have reliable unloading of data.
    uint32_t total_input_synapses_per_neuron = 40; //todo should this be fixed?
    uint32_t total_recurrent_synapses_per_neuron = 0; //todo should this be fixed?
    uint32_t recurrent_offset = 100;

    // TODO: check if this has already been calculated above...
    REAL rho = neuron->e_to_dt_on_tau_a; // decay_s1615(1.k, neuron->e_to_dt_on_tau_a);

    // TODO: Is there a better way of doing this?
    REAL accum_time = (accum)(time%neuron->window_size) * 0.001k;
    if (!accum_time){
        accum_time += 1.k;
    }

    REAL v_mem_error;

    if (neuron->V_membrane > neuron->B){
        v_mem_error = neuron->V_membrane - neuron->B;
    }
    else if (neuron->V_membrane < -neuron->B){
        v_mem_error = neuron->V_membrane + neuron->B;
    }
    else{
        v_mem_error = 0.k;
    }

    // Calculate regularised learning signal
    REAL reg_learning_signal = (neuron->core_pop_rate // make it work for different ts
//                                    / ((accum)(time%1300)
//                                    / (1.225k // 00000!!!!!
                                    / (accum_time
                                    * (accum)syn_dynamics_neurons_in_partition))
                                    - neuron->core_target_rate;

    // hardcoded reset
    if (time % neuron->window_size == neuron->window_size - 1 & !printed_value) {
        printed_value = true;
    }
    if (time % neuron->window_size == 0){
    	// TODO: does this need editing to be done for all neurons?
//        global_parameters->core_pop_rate = 0.k;
        printed_value = false;
    }

    // Calculate new learning signal
    REAL new_learning_signal = (learning_signal * neuron->w_fb) + v_mem_error;

    uint32_t test_length = (150*neuron->number_of_cues)+1000+150;
    if(neuron->number_of_cues == 0) {
        test_length = neuron->window_size;
    }

	// TODO make this relative to number of cues?
    if (time % neuron->window_size > test_length * 2) {
        neuron->L = new_learning_signal + (reg_learning_signal);// * 0.1k);
    }
    else{
        neuron->L = new_learning_signal;
    }

    neuron->L = new_learning_signal;
    // eta used to be a global parameter, but now just copy from neuron
    REAL local_eta = neuron->eta;

    // Reset parameter check
    if ((time % test_length == 0 || time % test_length == 1) && neuron->number_of_cues){
        neuron->B = neuron->b_0;
        neuron->b = 0.k;
        neuron->V_membrane = neuron->V_rest;
        neuron->refract_timer = 0;
        neuron->z = 0.k;
    }

    // All subsequent operations now need doing once per eprop synapse
    for (uint32_t syn_ind=0; syn_ind < total_input_synapses_per_neuron; syn_ind++){
        if ((time % test_length == 0 || time % test_length == 1) && neuron->number_of_cues){
            neuron->syn_state[syn_ind].z_bar_inp = 0.k;
            neuron->syn_state[syn_ind].z_bar = 0.k;
            neuron->syn_state[syn_ind].el_a = 0.k;
            neuron->syn_state[syn_ind].e_bar = 0.k;
        }
    	// ******************************************************************
		// Low-pass filter incoming spike train
		// ******************************************************************
    	neuron->syn_state[syn_ind].z_bar =
    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC
    			+
    			(1 - neuron->exp_TC) *
    			neuron->syn_state[syn_ind].z_bar_inp; // updating z_bar is problematic, if spike could come and interrupt neuron update


		// ******************************************************************
		// Update eligibility vector
		// ******************************************************************
    	neuron->syn_state[syn_ind].el_a =
    			(neuron->psi * neuron->syn_state[syn_ind].z_bar) +
	    	(rho - neuron->psi * neuron->beta) *
			neuron->syn_state[syn_ind].el_a;

    	// ******************************************************************
		// Update eligibility trace
		// ******************************************************************
    	REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
    		neuron->beta * neuron->syn_state[syn_ind].el_a);

    	neuron->syn_state[syn_ind].e_bar =
    			neuron->exp_TC * neuron->syn_state[syn_ind].e_bar
				+ (1 - neuron->exp_TC) * temp_elig_trace;

		// ******************************************************************
		// Update cached total weight change
		// ******************************************************************
    	REAL this_dt_weight_change =
    			local_eta * neuron->L * neuron->syn_state[syn_ind].e_bar;
    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change; // -= here to enable compiler to handle previous line (can crash when -ve is at beginning of previous line)

    	// reset input (can't have more than one spike per timestep
    	neuron->syn_state[syn_ind].z_bar_inp = 0;

    	// decrease timestep counter preventing rapid updates
        neuron->syn_state[syn_ind].update_ready -= 1;
    }

    // All further operations now need doing once per recurrent eprop synapse
    for (uint32_t syn_ind=recurrent_offset; syn_ind < total_recurrent_synapses_per_neuron+recurrent_offset; syn_ind++){
        if ((time % test_length == 0 || time % test_length == 1) && neuron->number_of_cues){
            neuron->syn_state[syn_ind].z_bar_inp = 0.k;
            neuron->syn_state[syn_ind].z_bar = 0.k;
            neuron->syn_state[syn_ind].el_a = 0.k;
            neuron->syn_state[syn_ind].e_bar = 0.k;
        }
		// ******************************************************************
		// Low-pass filter incoming spike train
		// ******************************************************************
    	// updating z_bar is problematic, if spike could come and interrupt neuron update
    	neuron->syn_state[syn_ind].z_bar =
    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC
    			+ (1 - neuron->exp_TC) * neuron->syn_state[syn_ind].z_bar_inp;

		// ******************************************************************
		// Update eligibility vector
		// ******************************************************************
    	neuron->syn_state[syn_ind].el_a =
    			(neuron->psi * neuron->syn_state[syn_ind].z_bar) +
    		(rho - neuron->psi * neuron->beta) *
			neuron->syn_state[syn_ind].el_a;

    	// ******************************************************************
		// Update eligibility trace
		// ******************************************************************
    	REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
    		neuron->beta * neuron->syn_state[syn_ind].el_a);

    	neuron->syn_state[syn_ind].e_bar =
    			neuron->exp_TC * neuron->syn_state[syn_ind].e_bar
				+ (1 - neuron->exp_TC) * temp_elig_trace;

		// ******************************************************************
		// Update cached total weight change
		// ******************************************************************
    	REAL this_dt_weight_change =
    			local_eta * neuron->L * neuron->syn_state[syn_ind].e_bar;
    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change; // -= here to enable compiler to handle previous line (can crash when -ve is at beginning of previous line)

    	// reset input (can't have more than one spike per timestep
    	neuron->syn_state[syn_ind].z_bar_inp = 0;

    	// decrease timestep counter preventing rapid updates
        neuron->syn_state[syn_ind].update_ready -= 1;
    }

    return neuron->V_membrane;
}

void neuron_model_has_spiked(neuron_t *restrict neuron) {
    // reset z to zero
    neuron->z = 0;
	// TODO: Not sure this should be commented out
//    neuron->V_membrane = neuron->V_rest;
    // Set refractory timer
    neuron->refract_timer  = neuron->T_refract - 1;
    neuron->A = 0;
}

state_t neuron_model_get_membrane_voltage(const neuron_t *neuron) {
    return neuron->V_membrane;
}

void neuron_model_print_state_variables(const neuron_t *neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
    log_debug("learning      = %k ", neuron->L);

    log_debug("Printing synapse state values:");
    for (uint32_t syn_ind=0; syn_ind < 100; syn_ind++){
    	log_debug("synapse number %u delta_w, z_bar, z_bar_inp, e_bar, el_a %11.4k %11.4k %11.4k %11.4k %11.4k",
    			syn_ind, neuron->syn_state[syn_ind].delta_w,
				neuron->syn_state[syn_ind].z_bar, neuron->syn_state[syn_ind].z_bar_inp,
				neuron->syn_state[syn_ind].e_bar, neuron->syn_state[syn_ind].el_a);
    }
}

void neuron_model_print_parameters(const neuron_t *neuron) {
    log_debug("V reset       = %11.4k mv\n\n", neuron->V_reset);
    log_debug("V rest        = %11.4k mv\n", neuron->V_rest);
    log_debug("I offset      = %11.4k nA\n", neuron->I_offset);
    log_debug("R membrane    = %11.4k Mohm\n", neuron->R_membrane);
    log_debug("exp(-ms/(RC)) = %11.4k [.]\n", neuron->exp_TC);
    log_debug("T refract     = %u timesteps\n", neuron->T_refract);
    log_debug("learning      = %k n/a\n", neuron->L);
    log_debug("feedback w    = %k n/a\n\n", neuron->w_fb);
    log_debug("window size   = %u ts\n", neuron->window_size);
    log_debug("beta    = %k n/a\n", neuron->beta);
    log_debug("adpt          = %k n/a\n", neuron->adpt);
}

#endif // _NEURON_MODEL_EPROP_ADAPTIVE_IMPL_H_
