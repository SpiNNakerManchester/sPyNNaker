#ifndef _NEURON_IMPL_LEFT_RIGHT_READOUT_H_
#define _NEURON_IMPL_LEFT_RIGHT_READOUT_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/synapse_types/synapse_type_eprop_adaptive.h>
#include <neuron/models/neuron_model_left_right_readout_impl.h>
#include <neuron/input_types/input_type_current.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>
#include <neuron/threshold_types/threshold_type_static.h>

#include <neuron/current_sources/current_source.h>

// Further includes
#include <common/maths-util.h>
#include <recording.h>
#include <debug.h>
#include <random.h>
#include <log.h>

//! Indices for recording of words
enum word_recording_indices {
    //! V (somatic potential) recording index
    V_RECORDING_INDEX = 0,
    //! Gsyn_exc (excitatory synaptic conductance/current) recording index
    GSYN_EXC_RECORDING_INDEX = 1,
    //! Gsyn_inh (excitatory synaptic conductance/current) recording index
    GSYN_INH_RECORDING_INDEX = 2,
    //! Number of recorded word-sized state variables
    N_RECORDED_VARS = 3
};

//! Indices for recording of bitfields
enum bitfield_recording_indices {
    //! Spike event recording index
    SPIKE_RECORDING_BITFIELD = 0,
    //! Number of recorded bitfields
    N_BITFIELD_VARS = 1
};

#ifndef NUM_EXCITATORY_RECEPTORS
#define NUM_EXCITATORY_RECEPTORS 1
#error NUM_EXCITATORY_RECEPTORS was undefined.  It should be defined by a synapse\
       shaping include
#endif

#ifndef NUM_INHIBITORY_RECEPTORS
#define NUM_INHIBITORY_RECEPTORS 1
#error NUM_INHIBITORY_RECEPTORS was undefined.  It should be defined by a synapse\
       shaping include
#endif

#include <neuron/neuron_recording.h>

//! Array of neuron states
neuron_t *neuron_array;

//! Input states array
static input_type_t *input_type_array;

//! Additional input array
static additional_input_t *additional_input_array;

//! Threshold states array
static threshold_type_t *threshold_type_array;

//! Global parameters for the neurons
//static global_neuron_params_pointer_t global_parameters;

// The synapse shaping parameters
static synapse_types_t *synapse_types_array;

//! The number of steps to run per timestep
static uint n_steps_per_timestep;

//! Whether key is set, from neuron.c
extern bool use_key;

// TODO: are these parameters needed?
static REAL next_spike_time = 0;
//extern uint32_t time;
extern uint32_t *neuron_keys;
extern REAL learning_signal;
static uint32_t target_ind = 0;

// recording params (?)
uint32_t is_it_right = 0;
//uint32_t choice = 0;

// Left right parameters
typedef enum
{
    STATE_CUE,
    STATE_WAITING,
    STATE_PROMPT,
} left_right_state_t;

left_right_state_t current_state = 0;
uint32_t current_time = 0;
uint32_t cue_number = 0;
uint32_t current_cue_direction = 2; // 0 = left, 1 = right
uint32_t accumulative_direction = 0; // if > total_cues / 2 = right
uint32_t wait_between_cues = 50; // ms
uint32_t duration_of_cue = 100; // ms
uint32_t wait_before_result = 1000; // ms but should be a range between 500-1500
uint32_t prompt_duration = 150; //ms
//uint32_t ticks_for_mean = 0;
bool start_prompt = false;
accum softmax_0 = 0k;
accum softmax_1 = 0k;
//REAL payload;
bool completed_broadcast = true;


static bool neuron_impl_initialise(uint32_t n_neurons) {

    // allocate DTCM for the global parameter details
//    if (sizeof(global_neuron_params_t) > 0) {
//        global_parameters = (global_neuron_params_t *) spin1_malloc(
//            sizeof(global_neuron_params_t));
//        if (global_parameters == NULL) {
//            log_error("Unable to allocate global neuron parameters"
//                      "- Out of DTCM");
//            return false;
//        }
//    }

    // Allocate DTCM for neuron array
    if (sizeof(neuron_t) != 0) {
        neuron_array = spin1_malloc(n_neurons * sizeof(neuron_t));
        if (neuron_array == NULL) {
            log_error("Unable to allocate neuron array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for input type array and copy block of data
    if (sizeof(input_type_t) != 0) {
        input_type_array = spin1_malloc(n_neurons * sizeof(input_type_t));
        if (input_type_array == NULL) {
            log_error("Unable to allocate input type array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for additional input array and copy block of data
    if (sizeof(additional_input_t) != 0) {
        additional_input_array = spin1_malloc(
        		n_neurons * sizeof(additional_input_t));
        if (additional_input_array == NULL) {
            log_error("Unable to allocate additional input array"
                      " - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for threshold type array and copy block of data
    if (sizeof(threshold_type_t) != 0) {
        threshold_type_array = spin1_malloc(
            n_neurons * sizeof(threshold_type_t));
        if (threshold_type_array == NULL) {
            log_error("Unable to allocate threshold type array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for synapse shaping parameters
    if (sizeof(synapse_types_t) != 0) {
        synapse_types_array = spin1_malloc(
            n_neurons * sizeof(synapse_types_t));
        if (synapse_types_array == NULL) {
            log_error("Unable to allocate synapse parameters array"
                " - Out of DTCM");
            return false;
        }
    }

    // Seed the random input
    validate_mars_kiss64_seed(neuron_array->kiss_seed);

    // Initialise pointers to Neuron parameters in STDP code
//    synapse_dynamics_set_neuron_array(neuron_array);
//    log_info("set pointer to neuron array in stdp code");

    return true;
}

static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // simple wrapper to synapse type input function
    synapse_types_t *parameters =
            &(synapse_types_array[neuron_index]);
    synapse_types_add_neuron_input(synapse_type_index,
            parameters, weights_this_timestep);
}

static uint32_t n_words_needed(uint32_t size) {
    return (size + (sizeof(uint32_t) - 1)) / sizeof(uint32_t);
}

static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons,
		address_t save_initial_state) {
    log_debug("reading parameters, next is %u, n_neurons is %u ",
        next, n_neurons);

    // Number of steps per timestep
    n_steps_per_timestep = address[next++];
    if (n_steps_per_timestep == 0) {
    	log_error("bad number of steps per timestep: 0");
    	rt_error(RTE_SWERR);
    }

    if (sizeof(neuron_t)) {
    	neuron_params_t *params = (neuron_params_t *) &address[next];
		for (uint32_t i = 0; i < n_neurons; i++) {
			neuron_model_initialise(&neuron_array[i], &params[i],
					n_steps_per_timestep);
		}
        next += n_words_needed(n_neurons * sizeof(neuron_params_t));
    }

    if (sizeof(input_type_t)) {
    	input_type_params_t *params = (input_type_params_t *) &address[next];
		for (uint32_t i = 0; i < n_neurons; i++) {
			input_type_initialise(&input_type_array[i], &params[i],
					n_steps_per_timestep);
		}
        next += n_words_needed(n_neurons * sizeof(input_type_params_t));
    }

    if (sizeof(threshold_type_t)) {
    	threshold_type_params_t *params = (threshold_type_params_t *) &address[next];
        for (uint32_t i = 0; i < n_neurons; i++) {
        	threshold_type_initialise(&threshold_type_array[i], &params[i],
        			n_steps_per_timestep);
        }
        next += n_words_needed(n_neurons * sizeof(threshold_type_params_t));
    }

    if (sizeof(synapse_types_t)) {
    	synapse_types_params_t *params = (synapse_types_params_t *) &address[next];
		for (uint32_t i = 0; i < n_neurons; i++) {
			synapse_types_initialise(&synapse_types_array[i], &params[i],
					n_steps_per_timestep);
		}
        next += n_words_needed(n_neurons * sizeof(synapse_types_params_t));
    }

    if (sizeof(additional_input_t)) {
    	additional_input_params_t *params = (additional_input_params_t *) &address[next];
        for (uint32_t i = 0; i < n_neurons; i++) {
        	additional_input_initialise(&additional_input_array[i], &params[i],
        			n_steps_per_timestep);
        }
        next += n_words_needed(n_neurons * sizeof(additional_input_params_t));
    }

    // If we are to save the initial state, copy the whole of the parameters
    // to the initial state
    if (save_initial_state) {
    	spin1_memcpy(save_initial_state, address, next * sizeof(uint32_t));
    }
//    io_printf(IO_BUF, "\nPrinting global params\n");
//    io_printf(IO_BUF, "seed 1: %u \n", global_parameters->kiss_seed[0]);
//    io_printf(IO_BUF, "seed 2: %u \n", global_parameters->kiss_seed[1]);
//    io_printf(IO_BUF, "seed 3: %u \n", global_parameters->kiss_seed[2]);
//    io_printf(IO_BUF, "seed 4: %u \n", global_parameters->kiss_seed[3]);
//    io_printf(IO_BUF, "ticks_per_second: %k \n\n", global_parameters->ticks_per_second);
////    io_printf(IO_BUF, "prob_command: %k \n\n", global_parameters->prob_command);
//    io_printf(IO_BUF, "rate on: %k \n\n", global_parameters->rate_on);
//    io_printf(IO_BUF, "rate off: %k \n\n", global_parameters->rate_off);
//    io_printf(IO_BUF, "mean 0: %k \n\n", global_parameters->mean_0);
//    io_printf(IO_BUF, "mean 1: %k \n\n", global_parameters->mean_1);
//    io_printf(IO_BUF, "poisson key: %u \n\n", global_parameters->p_key);
//    io_printf(IO_BUF, "poisson pop size: %u \n\n", global_parameters->p_pop_size);


    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
    }

//    io_printf(IO_BUF, "size of global params: %u",
//    		sizeof(global_neuron_params_t));



    #if LOG_LEVEL >= LOG_DEBUG
        log_debug("-------------------------------------\n");
        for (index_t n = 0; n < n_neurons; n++) {
            neuron_model_print_parameters(&neuron_array[n]);
        }
        log_debug("-------------------------------------\n");
        //}
    #endif // LOG_LEVEL >= LOG_DEBUG
}




static void neuron_impl_do_timestep_update(
		uint32_t timer_count, uint32_t time, uint32_t n_neurons) {

	for (uint32_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

//		log_info("neuron_index %u time %u n_neurons %u", neuron_index, time, n_neurons);

		// Get the neuron itself
		neuron_t *neuron = &neuron_array[neuron_index];
		bool spike = false;

	//    current_time = time & 0x3ff; // repeats on a cycle of 1024 entries in array

	//    io_printf(IO_BUF, "Updating Neuron Index: %u\n", neuron_index);
	//    io_printf(IO_BUF, "Target: %k\n\n",
	//    		global_parameters->target_V[target_ind]);

		// Get the input_type parameters and voltage for this neuron
		input_type_t *input_type = &input_type_array[neuron_index];

		// Get threshold and additional input parameters for this neuron
		threshold_type_t *threshold_type =
				&threshold_type_array[neuron_index];
		additional_input_t *additional_input =
				&additional_input_array[neuron_index];
		synapse_types_t *synapse_type =
				&synapse_types_array[neuron_index];

		// Get the voltage
		state_t voltage = neuron_model_get_membrane_voltage(neuron);

		// Get the exc and inh values from the synapses
		input_t exc_values[NUM_EXCITATORY_RECEPTORS];
		input_t* exc_syn_values = synapse_types_get_excitatory_input(
				exc_values, synapse_type);
		input_t inh_values[NUM_INHIBITORY_RECEPTORS];
		input_t* inh_syn_values = synapse_types_get_inhibitory_input(
				inh_values, synapse_type);

		// Call functions to obtain exc_input and inh_input
		input_t* exc_input_values = input_type_get_input_value(
				exc_syn_values, input_type, NUM_EXCITATORY_RECEPTORS);
		input_t* inh_input_values = input_type_get_input_value(
				inh_syn_values, input_type, NUM_INHIBITORY_RECEPTORS);

		// Sum g_syn contributions from all receptors for recording
	//    REAL total_exc = 0;
	//    REAL total_inh = 0;
	//
	//    for (int i = 0; i < NUM_EXCITATORY_RECEPTORS-1; i++){
	//    	total_exc += exc_input_values[i];
	//    }
	//    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS-1; i++){
	//    	total_inh += inh_input_values[i];
	//    }

		// Call functions to get the input values to be recorded
	//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = total_exc;
	//    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = total_inh;

		// Call functions to convert exc_input and inh_input to current
		input_type_convert_excitatory_input_to_current(
				exc_input_values, input_type, voltage);
		input_type_convert_inhibitory_input_to_current(
				inh_input_values, input_type, voltage);

		REAL current_offset = current_source_get_offset(time, neuron_index);

		input_t external_bias = additional_input_get_input_value_as_current(
				additional_input, voltage);

		if (neuron_index == 0){
	//        io_printf(IO_BUF, "n0 - ");
			// update neuron parameters
			state_t result = neuron_model_state_update(
					NUM_EXCITATORY_RECEPTORS, exc_input_values,
					NUM_INHIBITORY_RECEPTORS, inh_input_values,
					external_bias, current_offset, neuron, -50k);
			// Finally, set global membrane potential to updated value
			for (uint32_t glob_n = 0; glob_n < n_neurons; glob_n++) {
				// Get the neuron itself
				neuron_t *glob_neuron = &neuron_array[glob_n];
				glob_neuron->readout_V_0 = result;
			}
//			global_parameters->readout_V_0 = result;

		} else if (neuron_index == 1){
	//        io_printf(IO_BUF, "n1 - ");
			// update neuron parameters
	//        learning_signal *= -1.k;
			state_t result = neuron_model_state_update(
					NUM_EXCITATORY_RECEPTORS, exc_input_values,
					NUM_INHIBITORY_RECEPTORS, inh_input_values,
					external_bias, current_offset, neuron, -50k);
	//        learning_signal *= -1.k;
			// Finally, set global membrane potential to updated value
			for (uint32_t glob_n = 0; glob_n < n_neurons; glob_n++) {
				// Get the neuron itself
				neuron_t *glob_neuron = &neuron_array[glob_n];
				glob_neuron->readout_V_1 = result;
			}
//			global_parameters->readout_V_1 = result;
		}
	//    if (neuron_index == 0){
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = global_parameters->readout_V_0;
	//    }
	//    else if (neuron_index == 1){
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = global_parameters->readout_V_1;
	//    }
	//    io_printf(IO_BUF, "state = %u - %u\n", current_state, time);
		if (cue_number == 0 && completed_broadcast){ // reset start of new test
	//        io_printf(IO_BUF, "time entering reset %u\n", time);
	//        io_printf(IO_BUF, "Resetting\n");
			completed_broadcast = false;
			current_time = time;
			current_state = STATE_CUE;
			accumulative_direction = 0;
			// error params
//			global_parameters->cross_entropy = 0.k;
			neuron->cross_entropy = 0.k;
			learning_signal = 0.k;
//			global_parameters->mean_0 = 0.k;
//			global_parameters->mean_1 = 0.k;
			neuron->mean_0 = 0.k;
			neuron->mean_1 = 0.k;
			softmax_0 = 0k;
			softmax_1 = 0k;
			if (use_key) {
				// I don't understand, this just sends zero
				// Oh, maybe it's a "completed" signal
				send_spike_mc_payload(
						neuron_keys[neuron_index], bitsk(neuron->cross_entropy));
//				while (!spin1_send_mc_packet(
//						neuron_keys[neuron_index],
//						bitsk(neuron->cross_entropy), 1)) {
//					spin1_delay_us(1);
//				}
			}
		}
	//    io_printf(IO_BUF, "current_state = %u, cue_number = %u, direction = %u, time = %u\n", current_state, cue_number, current_cue_direction, time);
		// In this state the environment is giving the left/right cues to the agent
		if (current_state == STATE_CUE){
	//        io_printf(IO_BUF, "time entering cue %u\n", time);
			if (neuron_index == 0){
				// if it's current in the waiting time between cues do nothing
	//            if ((time - current_time) % (wait_between_cues + duration_of_cue) < wait_between_cues){
	//                 do nothing?
	//            }
				// begin sending left/right cue
				if ((time - current_time) %
						(wait_between_cues + duration_of_cue) >= wait_between_cues){
					// pick broadcast if just entered
					if ((time - current_time) %
							(wait_between_cues + duration_of_cue) == wait_between_cues){
						// pick new value and broadcast
						REAL random_value = (REAL)(mars_kiss64_seed(
								neuron->kiss_seed) / (REAL)0xffffffff); // 0-1
						if (random_value < 0.5k){
							current_cue_direction = 0;
						}
						else{
							current_cue_direction = 1;
						}
	//                    current_cue_direction = (current_cue_direction + 1) % 2;
						accumulative_direction += current_cue_direction;
						REAL payload;
						payload = neuron->rate_on;
//	                    io_printf(IO_BUF, "poisson setting 1, direction = %u\n", current_cue_direction);
						for (int j = current_cue_direction*neuron->p_pop_size;
								j < current_cue_direction*neuron->p_pop_size + neuron->p_pop_size; j++){
//							log_info("current cue direction %u payload %k key index %u time %u neuron_index %u",
//									current_cue_direction, payload, j, time, neuron_index);
							send_spike_mc_payload(neuron->p_key | j, bitsk(payload));
//							spin1_send_mc_packet(
//									neuron->p_key | j, bitsk(payload), WITH_PAYLOAD);
						}
					}
				}
				// turn off and reset if finished
				else if ((time - current_time) % (wait_between_cues + duration_of_cue) == 0 && (time - current_time) > 0){//(wait_between_cues + duration_of_cue) - 1){
					cue_number += 1;
					REAL payload;
					payload = neuron->rate_off;
	//                    io_printf(IO_BUF, "poisson setting 2, direction = %u\n", current_cue_direction);
					for (int j = current_cue_direction*neuron->p_pop_size;
							j < current_cue_direction*neuron->p_pop_size + neuron->p_pop_size; j++){
						send_spike_mc_payload(neuron->p_key | j, bitsk(payload));
//						spin1_send_mc_packet(
//								neuron->p_key | j, bitsk(payload), WITH_PAYLOAD);
					}
					if (cue_number >= neuron->number_of_cues){
						current_state = (current_state + 1) % 3;
					}
				}
			}
		}
		else if (current_state == STATE_WAITING){
	//        io_printf(IO_BUF, "time entering wait %u\n", time);
			// waiting for prompt, all things ok
			if (cue_number >= neuron->number_of_cues){
				current_time = time;
				cue_number = 0;
			}
			if ((time - current_time) >= wait_before_result){
				current_state = (current_state + 1) % 3;
				start_prompt = true;
			}
		}
		else if (current_state == STATE_PROMPT){
	//        io_printf(IO_BUF, "time entering prompt %u\n", time);
			if (start_prompt && neuron_index == 1){
				current_time = time;
				// send packets to the variable poissons with the updated states
				for (int i = 0; i < 4; i++){
					REAL payload;
					payload = neuron->rate_on;
	//                io_printf(IO_BUF, "poisson setting 3, turning on prompt\n");
					for (int j = 2*neuron->p_pop_size;
							j < 2*neuron->p_pop_size + neuron->p_pop_size; j++){
						send_spike_mc_payload(neuron->p_key | j, bitsk(payload));
//						spin1_send_mc_packet(
//								neuron->p_key | j, bitsk(payload), WITH_PAYLOAD);
					}
				}
			}
			if (neuron_index == 2){ // this is the error source
				// Switched to always broadcasting error but with packet
	//            ticks_for_mean += 1; //todo is it a running error like this over prompt?
				start_prompt = false;
	//            io_printf(IO_BUF, "maybe here - %k - %k\n", global_parameters->mean_0, global_parameters->mean_1);
	//            io_printf(IO_BUF, "ticks %u - accum %k - ", ticks_for_mean, (accum)ticks_for_mean);
				// Softmax of the exc and inh inputs representing 1 and 0 respectively
				// may need to scale to stop huge numbers going in the exp
	//            io_printf(IO_BUF, "v0 %k - v1 %k\n", global_parameters->readout_V_0, global_parameters->readout_V_1);
	//            global_parameters->mean_0 += global_parameters->readout_V_0;
	//            global_parameters->mean_1 += global_parameters->readout_V_1;
				// divide -> * 1/x
	//            io_printf(IO_BUF, " umm ");
	//            accum exp_0 = expk(global_parameters->mean_0 / (accum)ticks_for_mean);
	//            accum exp_1 = expk(global_parameters->mean_1 / (accum)ticks_for_mean);
				accum exp_0 = expk(neuron->readout_V_0);// * 0.1k);
				accum exp_1 = expk(neuron->readout_V_1);// * 0.1k);
	//            io_printf(IO_BUF, "or here - ");
				// Um... how can an exponential be zero?
				if (exp_0 == 0k && exp_1 == 0k){
					if (neuron->readout_V_0 > neuron->readout_V_1){
						softmax_0 = 1k;
						softmax_1 = 0k;
					}
					else{
						softmax_0 = 0k;
						softmax_1 = 1k;
					}
				}
				else{
	//                accum denominator = 1.k  / (exp_1 + exp_0);
					softmax_0 = exp_0 / (exp_1 + exp_0);
					softmax_1 = exp_1 / (exp_1 + exp_0);
				}
	//            io_printf(IO_BUF, "soft0 %k - soft1 %k - v0 %k - v1 %k\n", softmax_0, softmax_1, global_parameters->readout_V_0, global_parameters->readout_V_1);
				// What to do if log(0)?
				if (accumulative_direction > neuron->number_of_cues >> 1){
					for (uint32_t glob_n = 0; glob_n < n_neurons; glob_n++) {
						// Get the neuron itself
						neuron_t *glob_neuron = &neuron_array[glob_n];
						glob_neuron->cross_entropy = -logk(softmax_1);
					}
					learning_signal = softmax_0;
					is_it_right = 1;
				}
				else{
					for (uint32_t glob_n = 0; glob_n < n_neurons; glob_n++) {
						// Get the neuron itself
						neuron_t *glob_neuron = &neuron_array[glob_n];
						glob_neuron->cross_entropy = -logk(softmax_0);
					}
					learning_signal = softmax_0 - 1.k;
					is_it_right = 0;
				}
	//            if (learning_signal > 0.5){
	//                learning_signal = 1k;
	//            }
	//            else if (learning_signal < -0.5){
	//                learning_signal = -1k;
	//            }
	//            else{
	//                learning_signal = 0k;
	//            }
				if (use_key) {
					send_spike_mc_payload(neuron_keys[neuron_index], bitsk(learning_signal));
//					while (!spin1_send_mc_packet(
//							neuron_keys[neuron_index],  bitsk(learning_signal), 1 )) {
//						spin1_delay_us(1);
//					}
				}
	//            if(learning_signal){
	//                io_printf(IO_BUF, "learning signal before cast = %k\n", learning_signal);
	//            }
	//            learning_signal = global_parameters->cross_entropy;
	//            recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] =
	//            io_printf(IO_BUF, "broadcasting error\n");
			}
			if ((time - current_time) >= prompt_duration && neuron_index == 0){
	//            io_printf(IO_BUF, "time entering end of test %u\n", time);
	//            io_printf(IO_BUF, "poisson setting 4, turning off prompt\n");
				current_state = 0;
				completed_broadcast = true;
				for (int i = 0; i < 4; i++){
					REAL payload;
					payload = neuron->rate_off;
					for (int j = 2*neuron->p_pop_size;
							j < 2*neuron->p_pop_size + neuron->p_pop_size; j++){
						send_spike_mc_payload(neuron->p_key | j, payload);
//						spin1_send_mc_packet(
//								neuron->p_key | j, payload, WITH_PAYLOAD);
					}
				}
			}
		}

	//    learning_signal = global_parameters->cross_entropy;

//		recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = learning_signal;//exc_input_values[0];//neuron->syn_state[1].update_ready;//
//		recorded_variable_values[V_RECORDING_INDEX] = voltage;
//		log_info("neuron_index %u time %u record learning signal %k",
//				neuron_index, time, learning_signal);
		neuron_recording_record_accum(
				GSYN_INH_RECORDING_INDEX, neuron_index, learning_signal);
		neuron_recording_record_accum(
				V_RECORDING_INDEX, neuron_index, voltage);
	//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = ;
	//    if (neuron_index == 2){
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = accumulative_direction;
	//    }
	//    else {
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = 3.5;
	//    }
		if (neuron_index == 2){ //this neuron does nothing
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[90].z_bar;
	//        recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[90].z_bar;
//			recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[50].delta_w;
			neuron_recording_record_accum(
					GSYN_EXC_RECORDING_INDEX, neuron_index,
					neuron->syn_state[50].delta_w);
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = is_it_right;
		}
		else if (neuron_index == 1){
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[40].z_bar;
	//        recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[55].z_bar;
//			recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[40].delta_w;
			neuron_recording_record_accum(
					GSYN_EXC_RECORDING_INDEX, neuron_index,
					neuron->syn_state[40].delta_w);
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = softmax_0;
		}
		else{
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[0].z_bar;
	//        recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[1].z_bar;
//			recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[0].delta_w;
			neuron_recording_record_accum(
					GSYN_EXC_RECORDING_INDEX, neuron_index,
					neuron->syn_state[0].delta_w);
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = softmax_0;
		}

		// If spike occurs, communicate to relevant parts of model
		if (spike) {
			// Call relevant model-based functions
			// Tell the neuron model
	//        neuron_model_has_spiked(neuron);

			// Tell the additional input
			additional_input_has_spiked(additional_input);
		}

		// Shape the existing input according to the included rule
		synapse_types_shape_input(synapse_type);

		#if LOG_LEVEL >= LOG_DEBUG
			neuron_model_print_state_variables(neuron);
		#endif // LOG_LEVEL >= LOG_DEBUG

		// Return the boolean to the model timestep update
		//    return spike;
	}

//	log_info("end of do_timestep_update time %u", time);
}





//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("writing parameters");

    // Skip steps per timestep
    next += 1;

    if (sizeof(neuron_t)) {
        log_debug("writing neuron local parameters");
//        spin1_memcpy(&address[next], neuron_array,
//                n_neurons * sizeof(neuron_t));
        neuron_params_t *params = (neuron_params_t *) &address[next];
        for (uint32_t i = 0; i < n_neurons; i++) {
        	neuron_model_save_state(&neuron_array[i], &params[i]);
        }
        next += n_words_needed(n_neurons * sizeof(neuron_params_t));
    }

    if (sizeof(input_type_t)) {
        log_debug("writing input type parameters");
        input_type_params_t *params = (input_type_params_t *) &address[next];
        for (uint32_t i = 0; i < n_neurons; i++) {
        	input_type_save_state(&input_type_array[i], &params[i]);
        }
        next += n_words_needed(n_neurons * sizeof(input_type_params_t));
    }

    if (sizeof(threshold_type_t)) {
        log_debug("writing threshold type parameters");
        threshold_type_params_t *params = (threshold_type_params_t *) &address[next];
        for (uint32_t i = 0; i < n_neurons; i++) {
        	threshold_type_save_state(&threshold_type_array[i], &params[i]);
        }
        next += n_words_needed(n_neurons * sizeof(threshold_type_params_t));
    }

    if (sizeof(synapse_types_t)) {
        log_debug("writing synapse parameters");
        synapse_types_params_t *params = (synapse_types_params_t *) &address[next];
        for (uint32_t i = 0; i < n_neurons; i++) {
        	synapse_types_save_state(&synapse_types_array[i], &params[i]);
        }
        next += n_words_needed(n_neurons * sizeof(synapse_types_params_t));
    }

    if (sizeof(additional_input_t)) {
        log_debug("writing additional input type parameters");
        additional_input_params_t *params = (additional_input_params_t *) &address[next];
        for (uint32_t i = 0; i < n_neurons; i++) {
        	additional_input_save_state(&additional_input_array[i], &params[i]);
        }
        next += n_words_needed(n_neurons * sizeof(additional_input_params_t));
    }
}

#if LOG_LEVEL >= LOG_DEBUG
void neuron_impl_print_inputs(uint32_t n_neurons) {
	bool empty = true;
	for (index_t i = 0; i < n_neurons; i++) {
		synapse_types_t *params = &synapse_types_array[i];
		input_t exc_values[NUM_EXCITATORY_RECEPTORS];
		input_t inh_values[NUM_INHIBITORY_RECEPTORS];
		empty = empty && (0 == bitsk(
		        synapse_types_get_excitatory_input(exc_values, params)[0]
		        - synapse_types_get_inhibitory_input(inh_values, params)[0]));
	}

	if (!empty) {
		log_debug("-------------------------------------\n");

		for (index_t i = 0; i < n_neurons; i++) {
			synapse_types_t *params = &synapse_types_array[i];
			input_t exc_values[NUM_EXCITATORY_RECEPTORS];
			input_t inh_values[NUM_INHIBITORY_RECEPTORS];
			input_t input =
			        synapse_types_get_excitatory_input(exc_values, params)[0]
			        - synapse_types_get_inhibitory_input(inh_values, params)[1];
			if (bitsk(input) != 0) {
				log_debug("%3u: %12.6k (= ", i, input);
				synapse_types_print_input(params);
				log_debug(")\n");
			}
		}
		log_debug("-------------------------------------\n");
	}
}

void neuron_impl_print_synapse_parameters(uint32_t n_neurons) {
	log_debug("-------------------------------------\n");
	for (index_t n = 0; n < n_neurons; n++) {
	    synapse_types_print_parameters(&(neuron_synapse_shaping_params[n]));
	}
	log_debug("-------------------------------------\n");
}

const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
	return synapse_types_get_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_LEFT_RIGHT_READOUT_H_
