///*
// * Copyright (c) 2017-2019 The University of Manchester
// *
// * This program is free software: you can redistribute it and/or modify
// * it under the terms of the GNU General Public License as published by
// * the Free Software Foundation, either version 3 of the License, or
// * (at your option) any later version.
// *
// * This program is distributed in the hope that it will be useful,
// * but WITHOUT ANY WARRANTY; without even the implied warranty of
// * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// * GNU General Public License for more details.
// *
// * You should have received a copy of the GNU General Public License
// * along with this program.  If not, see <http://www.gnu.org/licenses/>.
// */
//
//#include "neuron_model_eprop_adaptive_impl.h"
//
//#include <debug.h>
//
//bool printed_value = false;
//REAL v_mem_error;
//REAL new_learning_signal;
//extern REAL learning_signal;
////REAL local_eta;
//extern uint32_t time;
////extern global_neuron_params_pointer_t global_parameters;
//extern uint32_t syn_dynamics_neurons_in_partition;
//
//// simple Leaky I&F ODE
//static inline void lif_neuron_closed_form(
//        neuron_t *neuron, REAL V_prev, input_t input_this_timestep,
//		REAL B_t) {
//
//    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;
//
//    // update membrane voltage
//    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev))
//    		- neuron->z * B_t; // this line achieves reset
//}
//
////void neuron_model_set_global_neuron_params(
////        global_neuron_params_pointer_t params) {
////    use(params);
////
////    local_eta = params->eta;
////    io_printf(IO_BUF, "local eta = %k\n", local_eta);
////    io_printf(IO_BUF, "core_pop_rate = %k\n", params->core_pop_rate);
////    io_printf(IO_BUF, "core_target_rate = %k\n", params->core_target_rate);
////    io_printf(IO_BUF, "rate_exp_TC = %k\n\n", params->rate_exp_TC);
////    // Does Nothing - no params
////}
//
//state_t neuron_model_state_update(
//		uint16_t num_excitatory_inputs, input_t* exc_input,
//		uint16_t num_inhibitory_inputs, input_t* inh_input,
//		input_t external_bias, REAL current_offset, neuron_t *restrict neuron,  // this has a *restrict on it in LIF?
//		REAL B_t) {
//
//	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
//	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);
//
////	REAL total_exc = 0;
////	REAL total_inh = 0;
////
////	for (int i=0; i < num_excitatory_inputs; i++) {
////		total_exc += exc_input[i];
////	}
////	for (int i=0; i< num_inhibitory_inputs; i++) {
////		total_inh += inh_input[i];
////	}
//    // Get the input in nA
//    input_t input_this_timestep =
//    		exc_input[0] + exc_input[1] + neuron->I_offset + external_bias + current_offset;
//
//    lif_neuron_closed_form(
//            neuron, neuron->V_membrane, input_this_timestep, B_t);
//
//    // If outside of the refractory period
//    if (neuron->refract_timer <= 0) {
//      	// Allow spiking again
//       	neuron->A = 1;
//    } else {
//       	// Neuron cannot fire, as neuron->A=0;
//        // countdown refractory timer
//        neuron->refract_timer -= 1;
//    }
//
//
//    // ******************************************************************
//    // Update Psi (pseudo-derivative) (done once for each postsynaptic neuron)
//    // ******************************************************************
//    REAL psi_temp1 = (neuron->V_membrane - neuron->B) * (1/neuron->b_0);
//    REAL psi_temp2 = ((absk(psi_temp1)));
//    neuron->psi =  ((1.0k - psi_temp2) > 0.0k)?
//    		(1.0k/neuron->b_0) *
//			0.3k * //todo why is this commented?
//			(1.0k - psi_temp2) : 0.0k;
////	if (neuron->refract_timer){
////	    neuron->psi = 0.0k;
////	}
//    neuron->psi *= neuron->A;
//
////  This parameter is OK to update, as the actual size of the array is set in the header file, which matches the Python code.
////  This should make it possible to do a pause and resume cycle and have reliable unloading of data.
//    uint32_t total_input_synapses_per_neuron = 40; //todo should this be fixed?
//    uint32_t total_recurrent_synapses_per_neuron = 0; //todo should this be fixed?
//    uint32_t recurrent_offset = 100;
//
////    neuron->psi = neuron->psi << 10;
//
////    REAL rho = neuron->rho;//expk(-1.k / 1500.k); // adpt
//    REAL rho = (accum)decay_s1615(1.k, neuron->e_to_dt_on_tau_a);
////    REAL rho_3 = (accum)decay_s1615(1000.k, neuron->e_to_dt_on_tau_a);
////    io_printf(IO_BUF, "1:%k, 2:%k, 3:%k, 4:%k\n", rho, rho_2, rho_3, neuron->rho);
//
//    REAL accum_time = (accum)(time%neuron->window_size) * 0.001k;
//    if (!accum_time){
//        accum_time += 1.k;
//    }
////    io_printf(IO_BUF, "time = %u, mod = %u, accum = %k, /s:%k, rate:%k, accum t:%k\n", time, time%1300, (accum)(time%1300),
////                (accum)(time%1300) * 0.001k, (accum)(time%1300) * 0.001k * (accum)syn_dynamics_neurons_in_partition,
////                accum_time);
//
//    if (neuron->V_membrane > neuron->B){
//        v_mem_error = neuron->V_membrane - neuron->B;
////        io_printf(IO_BUF, "> %k = %k - %k\n", v_mem_error, neuron->V_membrane, neuron->B);
//    }
//    else if (neuron->V_membrane < -neuron->B){
//        v_mem_error = neuron->V_membrane + neuron->B;
////        io_printf(IO_BUF, "< %k = %k - %k\n", v_mem_error, -neuron->V_membrane, neuron->B);
//    }
//    else{
//        v_mem_error = 0.k;
//    }
////    learning_signal += v_mem_error;
//
////	REAL reg_error = (global_parameters->core_target_rate - global_parameters->core_pop_rate) / syn_dynamics_neurons_in_partition;
////    REAL reg_learning_signal = (global_parameters->core_pop_rate // make it work for different ts
//////                                    / ((accum)(time%1300)
//////                                    / (1.225k // 00000!!!!!
////                                    / (accum_time
////                                    * (accum)syn_dynamics_neurons_in_partition))
////                                    - global_parameters->core_target_rate;
//
//    REAL reg_learning_signal = (neuron->core_pop_rate // make it work for different ts
////                                    / ((accum)(time%1300)
////                                    / (1.225k // 00000!!!!!
//                                    / (accum_time
//                                    * (accum)syn_dynamics_neurons_in_partition))
//                                    - neuron->core_target_rate;
//
////    io_printf(IO_BUF, "rls: %k\n", reg_learning_signal);
//    if (time % neuron->window_size == neuron->window_size - 1 & !printed_value){ //hardcoded time of reset
////        io_printf(IO_BUF, "1 %u, rate err:%k, spikes:%k, target:%k\tL:%k, v_mem:%k\n",
////        time, reg_learning_signal, global_parameters->core_pop_rate, global_parameters->core_target_rate,
////        learning_signal-v_mem_error, v_mem_error);
////        global_parameters->core_pop_rate = 0.k;
////        REAL reg_learning_signal = ((global_parameters->core_pop_rate / 1.225k)//(accum)(time%1300))
////                                / (accum)syn_dynamics_neurons_in_partition) - global_parameters->core_target_rate;
////        io_printf(IO_BUF, "2 %u, rate at reset:%k, L:%k, rate:%k\n", time, reg_learning_signal, learning_signal, global_parameters->core_pop_rate);
//        printed_value = true;
//    }
//    if (time % neuron->window_size == 0){
////        new_learning_signal = 0.k;
////        global_parameters->core_pop_rate = 0.k;
//        printed_value = false;
//    }
////    neuron->L = learning_signal * neuron->w_fb;
////    learning_signal *= neuron->w_fb;
////    if (learning_signal != 0.k && new_learning_signal != learning_signal){
////    if (new_learning_signal != learning_signal){// && time%1300 > 1100){
////        io_printf(IO_BUF, "L:%k, rL:%k, cL:%k, nL:%k\n", learning_signal, reg_learning_signal, learning_signal + reg_learning_signal, new_learning_signal);
////    if (reg_learning_signal > 0.5k || reg_learning_signal < -0.5k){
//    new_learning_signal = (learning_signal * neuron->w_fb) + v_mem_error;
////    }
////        new_learning_signal = learning_signal;
////    }
////    neuron->L = learning_signal;
//
//    uint32_t test_length = (150*neuron->number_of_cues)+1000+150;
//    if(neuron->number_of_cues == 0){
//        test_length = neuron->window_size;
//    }
//
//    if (time % neuron->window_size > test_length * 2){ //todo make this relative to number of cues
//        neuron->L = new_learning_signal + (reg_learning_signal);// * 0.1k);
//    }
//    else{
//        neuron->L = new_learning_signal;
//    }
////    neuron->L = learning_signal * neuron->w_fb; // turns of all reg
//    neuron->L = new_learning_signal;
//    // Copy eta here instead?
//	REAL local_eta = neuron->eta;
////    if (time % 99 == 0){
////        io_printf(IO_BUF, "during B = %k, b = %k, time = %u\n", neuron->B, neuron->b, time);
////    }
//    if ((time % test_length == 0 || time % test_length == 1) && neuron->number_of_cues){
////        io_printf(IO_BUF, "before B = %k, b = %k\n", neuron->B, neuron->b);
//        neuron->B = neuron->b_0;
//        neuron->b = 0.k;
//        neuron->V_membrane = neuron->V_rest;
//        neuron->refract_timer = 0;
//        neuron->z = 0.k;
////        io_printf(IO_BUF, "reset B = %k, b = %k\n", neuron->B, neuron->b);
//    }
////    io_printf(IO_BUF, "check B = %k, b = %k, time = %u\n", neuron->B, neuron->b, time);
//    // All operations now need doing once per eprop synapse
//    for (uint32_t syn_ind=0; syn_ind < total_input_synapses_per_neuron; syn_ind++){
//        if ((time % test_length == 0 || time % test_length == 1) && neuron->number_of_cues){
//            neuron->syn_state[syn_ind].z_bar_inp = 0.k;
//            neuron->syn_state[syn_ind].z_bar = 0.k;
//            neuron->syn_state[syn_ind].el_a = 0.k;
//            neuron->syn_state[syn_ind].e_bar = 0.k;
//        }
//		// ******************************************************************
//		// Low-pass filter incoming spike train
//		// ******************************************************************
//    	neuron->syn_state[syn_ind].z_bar =
//    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC
//    			+
//    			(1 - neuron->exp_TC) *
//    			neuron->syn_state[syn_ind].z_bar_inp; // updating z_bar is problematic, if spike could come and interrupt neuron update
//
//
//		// ******************************************************************
//		// Update eligibility vector
//		// ******************************************************************
//    	neuron->syn_state[syn_ind].el_a =
//    			(neuron->psi * neuron->syn_state[syn_ind].z_bar) +
//    		(rho - neuron->psi * neuron->beta) *
//			neuron->syn_state[syn_ind].el_a;
////    		(rho) * neuron->syn_state[syn_ind].el_a;
//
//
//    	// ******************************************************************
//		// Update eligibility trace
//		// ******************************************************************
//    	REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
//    		neuron->beta * neuron->syn_state[syn_ind].el_a);
////    		0);
//
//    	neuron->syn_state[syn_ind].e_bar =
//    			neuron->exp_TC * neuron->syn_state[syn_ind].e_bar
//				+ (1 - neuron->exp_TC) * temp_elig_trace;
//
//		// ******************************************************************
//		// Update cached total weight change
//		// ******************************************************************
//    	REAL this_dt_weight_change =
//    			local_eta * neuron->L * neuron->syn_state[syn_ind].e_bar;
//    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change; // -= here to enable compiler to handle previous line (can crash when -ve is at beginning of previous line)
//
////    	if (!syn_ind || neuron->syn_state[syn_ind].z_bar){// || neuron->syn_state[syn_ind].z_bar_inp){
////            io_printf(IO_BUF, "total synapses = %u \t syn_ind = %u \t "
////                              "z_bar_inp = %k \t z_bar = %k \t time:%u\n"
////                              "L = %k = %k * %k = l * w_fb\n"
////                              "this dw = %k \t tot dw %k\n"
////                              ,
////                total_synapses_per_neuron,
////                syn_ind,
////                neuron->syn_state[syn_ind].z_bar_inp,
////                neuron->syn_state[syn_ind].z_bar,
////                time,
////                neuron->L, learning_signal, neuron -> w_fb,
////                this_dt_weight_change, neuron->syn_state[syn_ind].delta_w
////                );
////        }
//    	// reset input (can't have more than one spike per timestep
//    	neuron->syn_state[syn_ind].z_bar_inp = 0;
//
//    	// decrease timestep counter preventing rapid updates
////    	if (neuron->syn_state[syn_ind].update_ready > 0){
////    	    io_printf(IO_BUF, "ff reducing %u -- update:%u\n", syn_ind, neuron->syn_state[syn_ind].update_ready - 1);
//        neuron->syn_state[syn_ind].update_ready -= 1;
////    	}
////    	else{
////    	    io_printf(IO_BUF, "ff not reducing %u\n", syn_ind);
////    	}
//
////        io_printf(IO_BUF, "eta: %k, l: %k, ebar: %k, delta_w: %k, this dt: %k\n",
////            local_eta, neuron->L, neuron->syn_state[syn_ind].e_bar, neuron->syn_state[syn_ind].delta_w, this_dt_weight_change);
//
//    }
//
//
//    // All operations now need doing once per recurrent eprop synapse
//    for (uint32_t syn_ind=recurrent_offset; syn_ind < total_recurrent_synapses_per_neuron+recurrent_offset; syn_ind++){
//        if ((time % test_length == 0 || time % test_length == 1) && neuron->number_of_cues){
//            neuron->syn_state[syn_ind].z_bar_inp = 0.k;
//            neuron->syn_state[syn_ind].z_bar = 0.k;
//            neuron->syn_state[syn_ind].el_a = 0.k;
//            neuron->syn_state[syn_ind].e_bar = 0.k;
//        }
//		// ******************************************************************
//		// Low-pass filter incoming spike train
//		// ******************************************************************
//    	neuron->syn_state[syn_ind].z_bar =
//    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC
//    			+ (1 - neuron->exp_TC) * neuron->syn_state[syn_ind].z_bar_inp; // updating z_bar is problematic, if spike could come and interrupt neuron update
//
//
//		// ******************************************************************
//		// Update eligibility vector
//		// ******************************************************************
//    	neuron->syn_state[syn_ind].el_a =
//    			(neuron->psi * neuron->syn_state[syn_ind].z_bar) +
//    		(rho - neuron->psi * neuron->beta) *
//			neuron->syn_state[syn_ind].el_a;
////    		(rho) * neuron->syn_state[syn_ind].el_a;
//
//
//    	// ******************************************************************
//		// Update eligibility trace
//		// ******************************************************************
//    	REAL temp_elig_trace = neuron->psi * (neuron->syn_state[syn_ind].z_bar -
//    		neuron->beta * neuron->syn_state[syn_ind].el_a);
////    		0);
//
//    	neuron->syn_state[syn_ind].e_bar =
//    			neuron->exp_TC * neuron->syn_state[syn_ind].e_bar
//				+ (1 - neuron->exp_TC) * temp_elig_trace;
//
//		// ******************************************************************
//		// Update cached total weight change
//		// ******************************************************************
//    	REAL this_dt_weight_change =
//    			local_eta * neuron->L * neuron->syn_state[syn_ind].e_bar;
//    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change; // -= here to enable compiler to handle previous line (can crash when -ve is at beginning of previous line)
//
////    	if (!syn_ind || neuron->syn_state[syn_ind].z_bar){// || neuron->syn_state[syn_ind].z_bar_inp){
////            io_printf(IO_BUF, "total synapses = %u \t syn_ind = %u \t "
////                              "z_bar_inp = %k \t z_bar = %k \t time:%u\n"
////                              "L = %k = %k * %k = l * w_fb\n"
////                              "this dw = %k \t tot dw %k\n"
////                              ,
////                total_synapses_per_neuron,
////                syn_ind,
////                neuron->syn_state[syn_ind].z_bar_inp,
////                neuron->syn_state[syn_ind].z_bar,
////                time,
////                neuron->L, learning_signal, neuron -> w_fb,
////                this_dt_weight_change, neuron->syn_state[syn_ind].delta_w
////                );
////        }
//    	// reset input (can't have more than one spike per timestep
//    	neuron->syn_state[syn_ind].z_bar_inp = 0;
//
//    	// decrease timestep counter preventing rapid updates
////    	if (neuron->syn_state[syn_ind].update_ready > 0){
////    	    io_printf(IO_BUF, "recducing %u -- update:%u\n", syn_ind, neuron->syn_state[syn_ind].update_ready - 1);
//        neuron->syn_state[syn_ind].update_ready -= 1;
////    	}
////    	else{
////    	    io_printf(IO_BUF, "not recducing %u\n", syn_ind);
////    	}
//
////        io_printf(IO_BUF, "eta: %k, l: %k, ebar: %k, delta_w: %k, this dt: %k\n",
////            local_eta, neuron->L, neuron->syn_state[syn_ind].e_bar, neuron->syn_state[syn_ind].delta_w, this_dt_weight_change);
//
//    }
//
//    return neuron->V_membrane;
//}
//
//void neuron_model_has_spiked(neuron_t *restrict neuron) {
//    // reset z to zero
//    neuron->z = 0;
////    neuron->V_membrane = neuron->V_rest;  // Not sure this should be commented out
//    // Set refractory timer
//    neuron->refract_timer  = neuron->T_refract - 1;
//    neuron->A = 0;
//}
//
//state_t neuron_model_get_membrane_voltage(const neuron_t *neuron) {
//    return neuron->V_membrane;
//}
//
