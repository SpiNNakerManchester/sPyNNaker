#include "neuron_model_shd_readout_impl.h"

#include <debug.h>

extern uint32_t time;
extern REAL learning_signal[20];
REAL local_eta;
REAL v_mem_error;
bool printed_variables = false;

// simple Leaky I&F ODE
static inline void _lif_neuron_closed_form(
        neuron_pointer_t neuron, REAL V_prev, input_t input_this_timestep) {

    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // update membrane voltage
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev));
}

void neuron_model_set_global_neuron_params(
        global_neuron_params_pointer_t params) {
    use(params);

    local_eta = params->eta;
    io_printf(IO_BUF, "local eta = %k\n", local_eta);

    // Does Nothing - no params
}

state_t neuron_model_state_update(
		uint16_t num_excitatory_inputs, input_t* exc_input,
		uint16_t num_inhibitory_inputs, input_t* inh_input,
		input_t external_bias, neuron_pointer_t neuron, REAL dummy) {

	log_debug("Exc 1: %12.6k, Exc 2: %12.6k", exc_input[0], exc_input[1]);
	log_debug("Inh 1: %12.6k, Inh 2: %12.6k", inh_input[0], inh_input[1]);
	use(dummy);

//	if (time < 2){
//	        io_printf(IO_BUF, "sizeof synapse state: %k %u\n\n", sizeof(neuron->syn_state[0]),
//                                                                 sizeof(neuron->syn_state[0]));
//	}

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
                exc_input[0] + exc_input[1] + neuron->I_offset;

        _lif_neuron_closed_form(
            neuron, neuron->V_membrane, input_this_timestep);
    } else {

        // countdown refractory timer
        neuron->refract_timer -= 1;
    }

    uint32_t total_synapses_per_neuron = 100; //todo should this be fixed?

    if (neuron->V_membrane > 9.k){
        v_mem_error = neuron->V_membrane - 9.k;
//        io_printf(IO_BUF, "> %k = %k - %k\n", v_mem_error, neuron->V_membrane, neuron->B);
    }
    else if (neuron->V_membrane < -9.k){
        v_mem_error = neuron->V_membrane + 9.k;
//        io_printf(IO_BUF, "< %k = %k - %k\n", v_mem_error, -neuron->V_membrane, neuron->B);
    }
    else{
        v_mem_error = 0.k;
    }
//    if(v_mem_error > 1.k){
//        v_mem_error = 1.k;
//    }
//    if(v_mem_error < -1.k){
//        v_mem_error = -1.k;
//    }
    neuron->L = 0.k;//v_mem_error*0.01k;
    for (uint32_t n_ind=0; n_ind < 20; n_ind++){
        if (n_ind == (uint32_t)dummy){
            neuron->L += learning_signal[n_ind];// * neuron->w_fb[n_ind];
        }
//        if (time % 51 == 0){
//            io_printf(IO_BUF, "%u - %u - L:%k\n", (uint32_t)dummy, n_ind, learning_signal[n_ind]);
//        }
    }
    if (time % 1000 == 0 || time % 1000 == 1){
        neuron->V_membrane = neuron->V_reset;
//        io_printf(IO_BUF, "%u total - L:%k - v_mem_error:%k\n", time, neuron->L, v_mem_error);
    }
//    if (time % 51 == 0){
////        io_printf(IO_BUF, "%u update_ready = %d\n", time, neuron->syn_state[0].update_ready);
//        io_printf(IO_BUF, "vmem = %k, L = %k\n", v_mem_error, neuron->L);
//    }

    // All operations now need doing once per eprop synapse
    for (uint32_t syn_ind=0; syn_ind < total_synapses_per_neuron; syn_ind++){
        if (time % 1000 == 0 || time % 1000 == 1){
            neuron->syn_state[syn_ind].z_bar = 0.k;
//            neuron->syn_state[syn_ind].z_bar_inp = 0.k;
        }
		// ******************************************************************
		// Low-pass filter incoming spike train
		// ******************************************************************
    	neuron->syn_state[syn_ind].z_bar =
    			neuron->syn_state[syn_ind].z_bar * neuron->exp_TC;
//    			+ (1 - neuron->exp_TC) *
//    			+
//    			neuron->syn_state[syn_ind].z_bar_inp; // updating z_bar is problematic, if spike could come and interrupt neuron update


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
//    	this_dt_weight_change += v_mem_error * 0.01k;

//        if (time % 51 == 0 && syn_ind % 19 == 0){
////            io_printf(IO_BUF, "%u update_ready = %d\n", time, neuron->syn_state[0].update_ready);
//            io_printf(IO_BUF, "thisdw = %k, vmemdw = %k\n", this_dt_weight_change, v_mem_error * 0.01k);
//        }

    	neuron->syn_state[syn_ind].delta_w -= this_dt_weight_change;
//    	if ((time % 51 == 0 && !syn_ind && !printed_variables) || neuron->syn_state[syn_ind].delta_w > 1000.k){// || neuron->syn_state[syn_ind].z_bar){// || neuron->syn_state[syn_ind].z_bar_inp){
//            io_printf(IO_BUF, "total synapses = %u \t syn_ind = %u \t "
//                              "z_bar_inp = %k \t z_bar = %k \t time:%u\n"
//                              "L = %k & %k = v_merr\n"
//                              "this dw = %k \t tot dw %k\n\n"
//                              ,
//                total_synapses_per_neuron,
//                syn_ind,
//                neuron->syn_state[syn_ind].z_bar_inp,
//                neuron->syn_state[syn_ind].z_bar,
//                time,
//                neuron->L, v_mem_error,
//                this_dt_weight_change, neuron->syn_state[syn_ind].delta_w
//                );
//            printed_variables = true;
//        }
//        if (time % 51 == 1){
//            printed_variables = false;
//        }
    	// reset input (can't have more than one spike per timestep
//        neuron->syn_state[syn_ind].z_bar_inp = 0;


    	// decrease timestep counter preventing rapid updates
//    	if (neuron->syn_state[syn_ind].update_ready > 0){
//    	if (time % 1000 == 999){
        neuron->syn_state[syn_ind].update_ready -= 1;
//    	}

    }

    return neuron->V_membrane;
}

void neuron_model_has_spiked(neuron_pointer_t neuron) {

    // reset membrane voltage
    neuron->V_membrane = neuron->V_reset;

    // reset refractory timer
    neuron->refract_timer  = neuron->T_refract;
}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->V_membrane;
}

void neuron_model_print_state_variables(restrict neuron_pointer_t neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
}

void neuron_model_print_parameters(restrict neuron_pointer_t neuron) {
    io_printf(IO_BUF, "V reset       = %11.4k mv\n", neuron->V_reset);
    io_printf(IO_BUF, "V rest        = %11.4k mv\n", neuron->V_rest);

    io_printf(IO_BUF, "I offset      = %11.4k nA\n", neuron->I_offset);
    io_printf(IO_BUF, "R membrane    = %11.4k Mohm\n", neuron->R_membrane);

    io_printf(IO_BUF, "exp(-ms/(RC)) = %11.4k [.]\n", neuron->exp_TC);

    io_printf(IO_BUF, "T refract     = %u timesteps\n", neuron->T_refract);

    io_printf(IO_BUF, "learning      = %k n/a\n", neuron->L);

    io_printf(IO_BUF, "window      = %u n/a\n", neuron->window_size);

//    io_printf(IO_BUF, "feedback w    = %k n/a\n\n", neuron->w_fb);
//
//    io_printf(IO_BUF, "T refract     = %u timesteps\n", neuron->T_refract);
//    io_printf(IO_BUF, "mean_isi_ticks  = %k\n", neuron->mean_isi_ticks);
//    io_printf(IO_BUF, "time_to_spike_ticks  = %k \n",
//    		neuron->time_to_spike_ticks);
//
//    io_printf(IO_BUF, "Seed 1: %u\n", neuron->spike_source_seed[0]);
//    io_printf(IO_BUF, "Seed 2: %u\n", neuron->spike_source_seed[1]);
//    io_printf(IO_BUF, "Seed 3: %u\n", neuron->spike_source_seed[2]);
//    io_printf(IO_BUF, "Seed 4: %u\n", neuron->spike_source_seed[3]);
//    io_printf(IO_BUF, "seconds per tick: %u\n", neuron->seconds_per_tick);
//    io_printf(IO_BUF, "ticks per second: %k\n", neuron->ticks_per_second);
}
