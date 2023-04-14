#ifndef _NEURON_IMPL_SINUSOID_READOUT_H_
#define _NEURON_IMPL_SINUSOID_READOUT_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/synapse_types/synapse_type_eprop_adaptive.h>
#include <neuron/models/neuron_model_sinusoid_readout_impl.h>
#include <neuron/input_types/input_type_current.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>
#include <neuron/threshold_types/threshold_type_static.h>

#include <neuron/current_sources/current_source.h>

// Further includes
#include <common/maths-util.h>
#include <recording.h>
#include <debug.h>
#include <random.h>
#include <log.h> // maybe not needed?

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

////! Global parameters for the neurons
//static global_neuron_params_pointer_t global_parameters;

// The synapse shaping parameters
static synapse_types_t *synapse_types_array;

//! The number of steps to run per timestep
static uint n_steps_per_timestep;

// TODO: check if these other parameters are needed
static REAL next_spike_time = 0;
extern uint32_t time;
extern key_t key;
extern REAL learning_signal;
static uint32_t target_ind = 0;


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
    if (sizeof(neuron_t)) {
        neuron_array = spin1_malloc(n_neurons * sizeof(neuron_t));
        if (neuron_array == NULL) {
            log_error("Unable to allocate neuron array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for input type array and copy block of data
    if (sizeof(input_type_t)) {
        input_type_array = spin1_malloc(n_neurons * sizeof(input_type_t));
        if (input_type_array == NULL) {
            log_error("Unable to allocate input type array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for additional input array and copy block of data
    if (sizeof(additional_input_t)) {
        additional_input_array =
        		spin1_malloc(n_neurons * sizeof(additional_input_t));
        if (additional_input_array == NULL) {
            log_error("Unable to allocate additional input array"
                      " - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for threshold type array and copy block of data
    if (sizeof(threshold_type_t)) {
        threshold_type_array =
        		spin1_malloc(n_neurons * sizeof(threshold_type_t));
        if (threshold_type_array == NULL) {
            log_error("Unable to allocate threshold type array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for synapse shaping parameters
    if (sizeof(synapse_types_t) != 0) {
        synapse_types_array =
        		spin1_malloc(n_neurons * sizeof(synapse_types_t));
        if (synapse_types_array == NULL) {
            log_error("Unable to allocate synapse parameters array"
                " - Out of DTCM");
            return false;
        }
    }

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
//    io_printf(IO_BUF, "seed 1: %u \n", global_parameters->spike_source_seed[0]);
//    io_printf(IO_BUF, "seed 2: %u \n", global_parameters->spike_source_seed[1]);
//    io_printf(IO_BUF, "seed 3: %u \n", global_parameters->spike_source_seed[2]);
//    io_printf(IO_BUF, "seed 4: %u \n", global_parameters->spike_source_seed[3]);
//    io_printf(IO_BUF, "eta: %k \n\n", neuron_array[0]->eta);


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
		// Get the neuron itself
		neuron_t *neuron = &neuron_array[neuron_index];
		bool spike = false;
//		neuron_t *neuron_zero = &neuron_array[0];

		target_ind = time & 0x3ff; // repeats on a cycle of 1024 entries in array

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

		// This is clearly overwritten so why is it here?
//		recorded_variable_values[V_RECORDING_INDEX] = voltage;
//		neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, voltage);
		if (neuron_index == 0){
				// update neuron parameters
			state_t result = neuron_model_state_update(
						NUM_EXCITATORY_RECEPTORS, exc_input_values,
						NUM_INHIBITORY_RECEPTORS, inh_input_values,
						external_bias, current_offset, neuron, 0.0k);

			// Calculate error
			REAL error = result - neuron->target_V[target_ind];
			learning_signal = error;
			// Record Error
	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] =
	//                error;
	//                neuron->syn_state[3].delta_w;
	//                neuron->syn_state[0].z_bar;

//			log_info("neuron_index %u time %u voltage %k result %k exc input %k targetV %k",
//					neuron_index, time, voltage, result, exc_input_values[0],
//					neuron->target_V[target_ind]);

			// Record readout
			neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, result);
//			neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, voltage);
//			recorded_variable_values[V_RECORDING_INDEX] =
//							result;
		//                    neuron->syn_state[0].z_bar;

			// Send error (learning signal) as packet with payload
			// ToDo can't I just alter the global variable here?
			// Another option is just to use "send_spike" instead... ?
			while (!spin1_send_mc_packet(
					key | neuron_index,  bitsk(error), 1 )) {
				spin1_delay_us(1);
			}
		}
		else{
			// Record 'Error'
			neuron_recording_record_accum(
					V_RECORDING_INDEX, neuron_index,
					neuron->target_V[target_ind]);
//			recorded_variable_values[V_RECORDING_INDEX] =
//	//                neuron->syn_state[0].z_bar;
//					global_parameters->target_V[target_ind];
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] =
//	//                - global_parameters->target_V[target_ind];
		}
//		recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[neuron_index*20].z_bar;
		neuron_recording_record_accum(
				GSYN_INH_RECORDING_INDEX, neuron_index,
				neuron->syn_state[neuron_index*20].z_bar);
		// Record target
//		recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] =
//	//        			global_parameters->target_V[target_ind];
//						neuron->syn_state[neuron_index*20].delta_w;
//	//        			exc_input_values[0];
		neuron_recording_record_accum(
				GSYN_EXC_RECORDING_INDEX, neuron_index,
				neuron->syn_state[neuron_index*20].delta_w);

		// If spike occurs, communicate to relevant parts of model
		// TODO I don't know why this is here
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
//		return spike;
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
	    synapse_types_print_parameters(&(synapse_types_array[n]));
	}
	log_debug("-------------------------------------\n");
}

const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
	return synapse_types_get_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_SINUSOID_READOUT_H_
