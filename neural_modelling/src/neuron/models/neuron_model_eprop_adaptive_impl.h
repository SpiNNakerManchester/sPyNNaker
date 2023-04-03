/*
 * Copyright (c) 2017-2019 The University of Manchester
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
//REAL v_mem_error;
//REAL new_learning_signal;
extern REAL learning_signal;
//REAL local_eta;
extern uint32_t time;
//extern global_neuron_params_pointer_t global_parameters;
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

    // TODO: double-check that everything above this point is needed

    // TODO: see whether anything below this point should be approached in a similar way

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
//    decay_t e_to_dt_on_tau_a; // rho
    REAL beta;
//    decay_t adpt; // (1-rho)
    REAL scalar;

    REAL    L; // learning signal
    REAL w_fb; // feedback weight
    uint32_t window_size;
    uint32_t number_of_cues;

	REAL target_rate;
	REAL tau_err;
	REAL eta; // learning rate

    // array of synaptic states - peak fan-in of 250 for this case
    eprop_syn_state_t syn_state[SYNAPSES_PER_NEURON];
};


//! eprop neuron state
//! TODO: work to make this do something like what happens for LIF

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

    // TODO: double-check that everything above this point is needed

    // TODO: check approach for values below this (but these should be the same)

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

//neuron_t *neuron_array;

//typedef struct global_neuron_params_t {
//	REAL core_pop_rate;
//	REAL core_target_rate;
//	REAL rate_exp_TC;
//	REAL eta; // learning rate
//} global_neuron_params_t;

// TODO: use the threshold type for this instead?
static inline void threshold_type_update_threshold(state_t z,
		neuron_t *threshold_type){

//	_print_threshold_params(threshold_type);


	s1615 temp1 = decay_s1615(threshold_type->b, threshold_type->e_to_dt_on_tau_a);
	s1615 temp2 = decay_s1615(threshold_type->scalar, threshold_type->adpt) * z;

	threshold_type->b = temp1
			+ temp2;
	// io_printf(IO_BUF, "temp1: %k; temp2: %k\n", temp1, temp2);

//	// Evolve threshold dynamics (decay to baseline) and adapt if z=nonzero
//	// Update small b (same regardless of spike - uses z from previous timestep)
//	threshold_type->b =
//			decay_s1615(threshold_type->b, threshold_type->e_to_dt_on_tau_a)
//			+ decay_s1615(1000k, threshold_type->adpt) // fold scaling into decay to increase precision
//			* z; // stored on neuron
//
//    io_printf(IO_BUF, "before B = %k, temp1 = %k, temp2 = %k, b = %k, b_0 = %k, beta = %k",
//                    threshold_type->B, temp1, temp2, threshold_type->b, threshold_type->b_0, threshold_type->beta);
	// Update large B
	threshold_type->B = threshold_type->b_0 +
			threshold_type->beta*threshold_type->b;
//    io_printf(IO_BUF, "\nafter B = %k\n", threshold_type->B);
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

//	log_info("V_membrane %k V_rest %k R_membrane %k exp_TC %k I_offset %k refract_timer %k V_reset %k T_refract %k",
//			state->V_membrane, state->V_rest, state->R_membrane, state->exp_TC, state->I_offset,
//			state->refract_timer, state->V_reset, state->T_refract);

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

	state->core_pop_rate = 0.0k;
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
	// TODO: probably more parameters need copying across at this point, syn_state for a start
	params->V_init = state->V_membrane;
	params->refract_timer_init = state->refract_timer;
}

// simple Leaky I&F ODE
static inline void lif_neuron_closed_form(
        neuron_t *neuron, REAL V_prev, input_t input_this_timestep,
		REAL B_t) {

    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

//    log_info("alpha %k input %k R_membrane %k V_rest %k",
//    		alpha, input_this_timestep, neuron->R_membrane, neuron->V_rest);

    // update membrane voltage
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev))
    		- neuron->z * B_t; // this line achieves reset

//    log_info("neuron->V_membrane is %k neuron_z %k B_t %k", neuron->V_membrane, neuron->z, B_t);
}

//void neuron_model_set_global_neuron_params(
//        global_neuron_params_pointer_t params) {
//    use(params);
//
//    local_eta = params->eta;
//    io_printf(IO_BUF, "local eta = %k\n", local_eta);
//    io_printf(IO_BUF, "core_pop_rate = %k\n", params->core_pop_rate);
//    io_printf(IO_BUF, "core_target_rate = %k\n", params->core_target_rate);
//    io_printf(IO_BUF, "rate_exp_TC = %k\n\n", params->rate_exp_TC);
//    // Does Nothing - no params
//}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, input_t* exc_input,
		uint16_t num_inhibitory_inputs, input_t* inh_input,
		input_t external_bias, REAL current_offset, neuron_t *restrict neuron,  // this has a *restrict on it in LIF?
		REAL B_t) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);

//	REAL total_exc = 0;
//	REAL total_inh = 0;
//
//	for (int i=0; i < num_excitatory_inputs; i++) {
//		total_exc += exc_input[i];
//	}
//	for (int i=0; i< num_inhibitory_inputs; i++) {
//		total_inh += inh_input[i];
//	}
    // Get the input in nA
    input_t input_this_timestep =
    		exc_input[0] + exc_input[1] + neuron->I_offset + external_bias + current_offset;

//    log_info("exc input 0 %k exc input 1 %k I_offset %k", exc_input[0], exc_input[1], neuron->I_offset);

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
//	if (neuron->refract_timer){
//	    neuron->psi = 0.0k;
//	}
    neuron->psi *= neuron->A;

//  This parameter is OK to update, as the actual size of the array is set in the header file, which matches the Python code.
//  This should make it possible to do a pause and resume cycle and have reliable unloading of data.
    uint32_t total_input_synapses_per_neuron = 40; //todo should this be fixed?
    uint32_t total_recurrent_synapses_per_neuron = 0; //todo should this be fixed?
    uint32_t recurrent_offset = 100;

//    neuron->psi = neuron->psi << 10;

//    REAL rho = neuron->rho;//expk(-1.k / 1500.k); // adpt
    // CHECK: but I think this has already been calculated above... ?
    REAL rho = neuron->e_to_dt_on_tau_a; // decay_s1615(1.k, neuron->e_to_dt_on_tau_a);
//    REAL rho_3 = (accum)decay_s1615(1000.k, neuron->e_to_dt_on_tau_a);
//    io_printf(IO_BUF, "1:%k, 2:%k, 3:%k, 4:%k\n", rho, rho_2, rho_3, neuron->rho);

    REAL accum_time = (accum)(time%neuron->window_size) * 0.001k;
    if (!accum_time){
        accum_time += 1.k;
    }
//    io_printf(IO_BUF, "time = %u, mod = %u, accum = %k, /s:%k, rate:%k, accum t:%k\n", time, time%1300, (accum)(time%1300),
//                (accum)(time%1300) * 0.001k, (accum)(time%1300) * 0.001k * (accum)syn_dynamics_neurons_in_partition,
//                accum_time);

    REAL v_mem_error;

    if (neuron->V_membrane > neuron->B){
        v_mem_error = neuron->V_membrane - neuron->B;
//        io_printf(IO_BUF, "> %k = %k - %k\n", v_mem_error, neuron->V_membrane, neuron->B);
    }
    else if (neuron->V_membrane < -neuron->B){
        v_mem_error = neuron->V_membrane + neuron->B;
//        io_printf(IO_BUF, "< %k = %k - %k\n", v_mem_error, -neuron->V_membrane, neuron->B);
    }
    else{
        v_mem_error = 0.k;
    }
//    learning_signal += v_mem_error;

//	REAL reg_error = (global_parameters->core_target_rate - global_parameters->core_pop_rate) / syn_dynamics_neurons_in_partition;
//    REAL reg_learning_signal = (global_parameters->core_pop_rate // make it work for different ts
////                                    / ((accum)(time%1300)
////                                    / (1.225k // 00000!!!!!
//                                    / (accum_time
//                                    * (accum)syn_dynamics_neurons_in_partition))
//                                    - global_parameters->core_target_rate;

//    log_info("update learning signal syn_dynamics_neurons_in_partition %u ",
//    		syn_dynamics_neurons_in_partition);

    REAL reg_learning_signal = (neuron->core_pop_rate // make it work for different ts
//                                    / ((accum)(time%1300)
//                                    / (1.225k // 00000!!!!!
                                    / (accum_time
                                    * (accum)syn_dynamics_neurons_in_partition))
                                    - neuron->core_target_rate;

//    io_printf(IO_BUF, "rls: %k\n", reg_learning_signal);
    if (time % neuron->window_size == neuron->window_size - 1 & !printed_value){ //hardcoded time of reset
//        io_printf(IO_BUF, "1 %u, rate err:%k, spikes:%k, target:%k\tL:%k, v_mem:%k\n",
//        time, reg_learning_signal, global_parameters->core_pop_rate, global_parameters->core_target_rate,
//        learning_signal-v_mem_error, v_mem_error);
//        global_parameters->core_pop_rate = 0.k;
//        REAL reg_learning_signal = ((global_parameters->core_pop_rate / 1.225k)//(accum)(time%1300))
//                                / (accum)syn_dynamics_neurons_in_partition) - global_parameters->core_target_rate;
//        io_printf(IO_BUF, "2 %u, rate at reset:%k, L:%k, rate:%k\n", time, reg_learning_signal, learning_signal, global_parameters->core_pop_rate);
        printed_value = true;
    }
    if (time % neuron->window_size == 0){
//        new_learning_signal = 0.k;
//        global_parameters->core_pop_rate = 0.k;
        printed_value = false;
    }
//    neuron->L = learning_signal * neuron->w_fb;
//    learning_signal *= neuron->w_fb;
//    if (learning_signal != 0.k && new_learning_signal != learning_signal){
//    if (new_learning_signal != learning_signal){// && time%1300 > 1100){
//        io_printf(IO_BUF, "L:%k, rL:%k, cL:%k, nL:%k\n", learning_signal, reg_learning_signal, learning_signal + reg_learning_signal, new_learning_signal);
//    if (reg_learning_signal > 0.5k || reg_learning_signal < -0.5k){
    REAL new_learning_signal = (learning_signal * neuron->w_fb) + v_mem_error;
//    }
//        new_learning_signal = learning_signal;
//    }
//    neuron->L = learning_signal;

    uint32_t test_length = (150*neuron->number_of_cues)+1000+150;
    if(neuron->number_of_cues == 0){
        test_length = neuron->window_size;
    }

    if (time % neuron->window_size > test_length * 2){ //todo make this relative to number of cues
        neuron->L = new_learning_signal + (reg_learning_signal);// * 0.1k);
    }
    else{
        neuron->L = new_learning_signal;
    }
//    neuron->L = learning_signal * neuron->w_fb; // turns of all reg
    neuron->L = new_learning_signal;
    // Copy eta here instead?
	REAL local_eta = neuron->eta;
//    if (time % 99 == 0){
//        io_printf(IO_BUF, "during B = %k, b = %k, time = %u\n", neuron->B, neuron->b, time);
//    }
    if ((time % test_length == 0 || time % test_length == 1) && neuron->number_of_cues){
//        io_printf(IO_BUF, "before B = %k, b = %k\n", neuron->B, neuron->b);
        neuron->B = neuron->b_0;
        neuron->b = 0.k;
        neuron->V_membrane = neuron->V_rest;
        neuron->refract_timer = 0;
        neuron->z = 0.k;
//        io_printf(IO_BUF, "reset B = %k, b = %k\n", neuron->B, neuron->b);
    }
//    io_printf(IO_BUF, "check B = %k, b = %k, time = %u\n", neuron->B, neuron->b, time);
    // All operations now need doing once per eprop synapse
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
//    		(rho) * neuron->syn_state[syn_ind].el_a;


    	// ******************************************************************
		// Update eligibility trace
		// ******************************************************************
    	REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
    		neuron->beta * neuron->syn_state[syn_ind].el_a);
//    		0);

    	neuron->syn_state[syn_ind].e_bar =
    			neuron->exp_TC * neuron->syn_state[syn_ind].e_bar
				+ (1 - neuron->exp_TC) * temp_elig_trace;

		// ******************************************************************
		// Update cached total weight change
		// ******************************************************************
    	REAL this_dt_weight_change =
    			local_eta * neuron->L * neuron->syn_state[syn_ind].e_bar;
    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change; // -= here to enable compiler to handle previous line (can crash when -ve is at beginning of previous line)

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
//    	if (neuron->syn_state[syn_ind].update_ready > 0){
//    	    io_printf(IO_BUF, "ff reducing %u -- update:%u\n", syn_ind, neuron->syn_state[syn_ind].update_ready - 1);
        neuron->syn_state[syn_ind].update_ready -= 1;
//    	}
//    	else{
//    	    io_printf(IO_BUF, "ff not reducing %u\n", syn_ind);
//    	}

//        io_printf(IO_BUF, "eta: %k, l: %k, ebar: %k, delta_w: %k, this dt: %k\n",
//            local_eta, neuron->L, neuron->syn_state[syn_ind].e_bar, neuron->syn_state[syn_ind].delta_w, this_dt_weight_change);

    }


    // All operations now need doing once per recurrent eprop synapse
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
    	neuron->syn_state[syn_ind].z_bar =
    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC
    			+ (1 - neuron->exp_TC) * neuron->syn_state[syn_ind].z_bar_inp; // updating z_bar is problematic, if spike could come and interrupt neuron update


		// ******************************************************************
		// Update eligibility vector
		// ******************************************************************
    	neuron->syn_state[syn_ind].el_a =
    			(neuron->psi * neuron->syn_state[syn_ind].z_bar) +
    		(rho - neuron->psi * neuron->beta) *
			neuron->syn_state[syn_ind].el_a;
//    		(rho) * neuron->syn_state[syn_ind].el_a;


    	// ******************************************************************
		// Update eligibility trace
		// ******************************************************************
    	REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
    		neuron->beta * neuron->syn_state[syn_ind].el_a);
//    		0);

    	neuron->syn_state[syn_ind].e_bar =
    			neuron->exp_TC * neuron->syn_state[syn_ind].e_bar
				+ (1 - neuron->exp_TC) * temp_elig_trace;

		// ******************************************************************
		// Update cached total weight change
		// ******************************************************************
    	REAL this_dt_weight_change =
    			local_eta * neuron->L * neuron->syn_state[syn_ind].e_bar;
    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change; // -= here to enable compiler to handle previous line (can crash when -ve is at beginning of previous line)

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
//    	if (neuron->syn_state[syn_ind].update_ready > 0){
//    	    io_printf(IO_BUF, "recducing %u -- update:%u\n", syn_ind, neuron->syn_state[syn_ind].update_ready - 1);
        neuron->syn_state[syn_ind].update_ready -= 1;
//    	}
//    	else{
//    	    io_printf(IO_BUF, "not recducing %u\n", syn_ind);
//    	}

//        io_printf(IO_BUF, "eta: %k, l: %k, ebar: %k, delta_w: %k, this dt: %k\n",
//            local_eta, neuron->L, neuron->syn_state[syn_ind].e_bar, neuron->syn_state[syn_ind].delta_w, this_dt_weight_change);

    }

    return neuron->V_membrane;
}

void neuron_model_has_spiked(neuron_t *restrict neuron) {
    // reset z to zero
    neuron->z = 0;
//    neuron->V_membrane = neuron->V_rest;  // Not sure this should be commented out
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
//    io_printf(IO_BUF, "V reset       = %11.4k mv\n\n", neuron->V_reset);
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
//    io_printf(IO_BUF, "window size   = %u ts\n", neuron->window_size);
//
//    io_printf(IO_BUF, "beta    = %k n/a\n", neuron->beta);
//
//    io_printf(IO_BUF, "adpt          = %k n/a\n", neuron->adpt);
}

#endif // _NEURON_MODEL_EPROP_ADAPTIVE_IMPL_H_
