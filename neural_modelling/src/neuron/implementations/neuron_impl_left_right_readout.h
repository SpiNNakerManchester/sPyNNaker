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

// The synapse shaping parameters
static synapse_types_t *synapse_types_array;

//! The number of steps to run per timestep
static uint n_steps_per_timestep;

//! Whether key is set, from neuron.c
extern bool use_key;

extern uint32_t *neuron_keys;
extern REAL learning_signal;

// recording params (TODO: check these aren't needed?)
//uint32_t is_it_right = 0;
//uint32_t choice = 0;

// Left right state parameters
typedef enum
{
    STATE_CUE,
    STATE_WAITING,
    STATE_PROMPT,
} left_right_state_t;

// Left right parameters
left_right_state_t current_state = 0;
uint32_t current_time = 0;
uint32_t cue_number = 0;
uint32_t current_cue_direction = 2; // 0 = left, 1 = right
uint32_t accumulative_direction = 0; // if > total_cues / 2 = right
uint32_t wait_between_cues = 50; // ms
uint32_t duration_of_cue = 100; // ms
uint32_t wait_before_result = 1000; // ms but should be a range between 500-1500
uint32_t prompt_duration = 150; //ms
bool start_prompt = false;
accum softmax_0 = 0k;
accum softmax_1 = 0k;
bool completed_broadcast = true;


static bool neuron_impl_initialise(uint32_t n_neurons) {

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

		// Get the neuron itself
		neuron_t *neuron = &neuron_array[neuron_index];
//		bool spike = false;

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

		// Call functions to convert exc_input and inh_input to current
		input_type_convert_excitatory_input_to_current(
				exc_input_values, input_type, voltage);
		input_type_convert_inhibitory_input_to_current(
				inh_input_values, input_type, voltage);

		REAL current_offset = current_source_get_offset(time, neuron_index);

		input_t external_bias = additional_input_get_input_value_as_current(
				additional_input, voltage);

		if (neuron_index == 0){
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
		} else if (neuron_index == 1){
			// update neuron parameters
			state_t result = neuron_model_state_update(
					NUM_EXCITATORY_RECEPTORS, exc_input_values,
					NUM_INHIBITORY_RECEPTORS, inh_input_values,
					external_bias, current_offset, neuron, -50k);

			// Finally, set global membrane potential to updated value
			for (uint32_t glob_n = 0; glob_n < n_neurons; glob_n++) {
				// Get the neuron itself
				neuron_t *glob_neuron = &neuron_array[glob_n];
				glob_neuron->readout_V_1 = result;
			}
		}

		if (cue_number == 0 && completed_broadcast){ // reset start of new test
			completed_broadcast = false;
			current_time = time;
			current_state = STATE_CUE;
			accumulative_direction = 0;
			// error params
			neuron->cross_entropy = 0.k;
			learning_signal = 0.k;
			neuron->mean_0 = 0.k;
			neuron->mean_1 = 0.k;
			softmax_0 = 0k;
			softmax_1 = 0k;
			if (use_key) {
				// This sends a "completed" signal
				send_spike_mc_payload(
						neuron_keys[neuron_index], bitsk(neuron->cross_entropy));
//				while (!spin1_send_mc_packet(
//						neuron_keys[neuron_index],
//						bitsk(neuron->cross_entropy), 1)) {
//					spin1_delay_us(1);
//				}
			}
		}

		// In this state the environment is giving the left/right cues to the agent
		if (current_state == STATE_CUE) {
			if (neuron_index == 0) {
				// if it's currently in the waiting time between cues do nothing

				// Otherwise, begin sending left/right cue
				if ((time - current_time) %
						(wait_between_cues + duration_of_cue) >= wait_between_cues) {
					// pick broadcast if just entered
					if ((time - current_time) %
							(wait_between_cues + duration_of_cue) == wait_between_cues){
						// pick new value and broadcast
//						REAL random_value = kdivui(
//								(REAL)(mars_kiss64_seed(neuron->kiss_seed)), UINT32_MAX); // 0-1
						REAL random_value = (
								(REAL)mars_kiss64_seed(neuron->kiss_seed) / (REAL)UINT32_MAX); // 0-1
						if (random_value < 0.5k) {
							current_cue_direction = 0;
						}
						else{
							current_cue_direction = 1;
						}
						accumulative_direction += current_cue_direction;
						REAL payload;
						payload = neuron->rate_on;
						for (int j = current_cue_direction*neuron->p_pop_size;
								j < current_cue_direction*neuron->p_pop_size + neuron->p_pop_size; j++){
							send_spike_mc_payload(neuron->p_key | j, bitsk(payload));
//							spin1_send_mc_packet(
//									neuron->p_key | j, bitsk(payload), WITH_PAYLOAD);
						}
					}
				}
				// turn off and reset if finished
				else if ((time - current_time) % (wait_between_cues + duration_of_cue) == 0 &&
						(time - current_time) > 0) {//(wait_between_cues + duration_of_cue) - 1){
					cue_number += 1;
					REAL payload;
					payload = neuron->rate_off;
					for (int j = current_cue_direction*neuron->p_pop_size;
							j < current_cue_direction*neuron->p_pop_size + neuron->p_pop_size; j++) {
						send_spike_mc_payload(neuron->p_key | j, bitsk(payload));
//						spin1_send_mc_packet(
//								neuron->p_key | j, bitsk(payload), WITH_PAYLOAD);
					}
					if (cue_number >= neuron->number_of_cues) {
						current_state = (current_state + 1) % 3;
					}
				}
			}
		}
		else if (current_state == STATE_WAITING){
			// waiting for prompt, all things ok
			if (cue_number >= neuron->number_of_cues) {
				current_time = time;
				cue_number = 0;
			}
			if ((time - current_time) >= wait_before_result) {
				current_state = (current_state + 1) % 3;
				start_prompt = true;
			}
		}
		else if (current_state == STATE_PROMPT){
			if (start_prompt && neuron_index == 1){
				current_time = time;
				// send packets to the variable poissons with the updated states
				for (int i = 0; i < 4; i++){
					REAL payload;
					payload = neuron->rate_on;
					for (int j = 2*neuron->p_pop_size;
							j < 2*neuron->p_pop_size + neuron->p_pop_size; j++){
						send_spike_mc_payload(neuron->p_key | j, bitsk(payload));
//						spin1_send_mc_packet(
//								neuron->p_key | j, bitsk(payload), WITH_PAYLOAD);
					}
				}
			}

			// This is the error source
			if (neuron_index == 2) {
				// Switched to always broadcasting error but with packet
				start_prompt = false;
				accum exp_0 = expk(neuron->readout_V_0);// * 0.1k);
				accum exp_1 = expk(neuron->readout_V_1);// * 0.1k);

				// TODO: I'm not sure how an exponential can be zero?
				// Set up softmax calculation
				if (exp_0 == 0k && exp_1 == 0k) {
					if (neuron->readout_V_0 > neuron->readout_V_1) {
						softmax_0 = 1k;
						softmax_1 = 0k;
					}
					else {
						softmax_0 = 0k;
						softmax_1 = 1k;
					}
				}
				else {
					// These divides are okay in kdivk because exp is always positive
					softmax_0 = kdivk(exp_0, (exp_1 + exp_0));
					softmax_1 = kdivk(exp_1, (exp_1 + exp_0));
				}

				// What to do if log(0)?
				if (accumulative_direction > neuron->number_of_cues >> 1){
					for (uint32_t glob_n = 0; glob_n < n_neurons; glob_n++) {
						// Get the neuron itself
						neuron_t *glob_neuron = &neuron_array[glob_n];
						glob_neuron->cross_entropy = -logk(softmax_1);
					}
					learning_signal = softmax_0;
//					is_it_right = 1;
				}
				else{
					for (uint32_t glob_n = 0; glob_n < n_neurons; glob_n++) {
						// Get the neuron itself
						neuron_t *glob_neuron = &neuron_array[glob_n];
						glob_neuron->cross_entropy = -logk(softmax_0);
					}
					learning_signal = softmax_0 - 1.k;
//					is_it_right = 0;
				}
				if (use_key) {
					send_spike_mc_payload(neuron_keys[neuron_index], bitsk(learning_signal));
//					while (!spin1_send_mc_packet(
//							neuron_keys[neuron_index],  bitsk(learning_signal), 1 )) {
//						spin1_delay_us(1);
//					}
				}
			}

			// The current broadcast may have completed so check
			if ((time - current_time) >= prompt_duration && neuron_index == 0){
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

		// Record learning signal and voltage
		neuron_recording_record_accum(
				GSYN_INH_RECORDING_INDEX, neuron_index, learning_signal);
		neuron_recording_record_accum(
				V_RECORDING_INDEX, neuron_index, voltage);

		// Record delta_w from different synapse states depending on neuron index
		if (neuron_index == 2) {
			neuron_recording_record_accum(
					GSYN_EXC_RECORDING_INDEX, neuron_index,
					neuron->syn_state[50].delta_w);
		}
		else if (neuron_index == 1) {
			neuron_recording_record_accum(
					GSYN_EXC_RECORDING_INDEX, neuron_index,
					neuron->syn_state[40].delta_w);
		}
		else {
			neuron_recording_record_accum(
					GSYN_EXC_RECORDING_INDEX, neuron_index,
					neuron->syn_state[0].delta_w);
		}

		// This model doesn't spike so this can be commented out
//		if (spike) {
//			// Call relevant model-based functions
//			// Tell the neuron model
//	//        neuron_model_has_spiked(neuron);
//
//			// Tell the additional input
//			additional_input_has_spiked(additional_input);
//		}

		// Shape the existing input according to the included rule
		synapse_types_shape_input(synapse_type);

		#if LOG_LEVEL >= LOG_DEBUG
			neuron_model_print_state_variables(neuron);
		#endif // LOG_LEVEL >= LOG_DEBUG
	}
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
