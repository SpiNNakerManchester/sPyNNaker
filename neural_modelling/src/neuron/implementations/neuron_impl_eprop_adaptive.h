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
x *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _NEURON_IMPL_EPROP_ADAPTIVE_H_
#define _NEURON_IMPL_EPROP_ADAPTIVE_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/synapse_types/synapse_type_eprop_adaptive.h>
#include <neuron/threshold_types/threshold_type_none.h>
#include <neuron/models/neuron_model_eprop_adaptive_impl.h>
#include <neuron/input_types/input_type_current.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>

#include <neuron/current_sources/current_source.h>

// Further includes
//#include <common/out_spikes.h>
#include <recording.h>
#include <debug.h>

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

//extern uint32_t time;
extern REAL learning_signal;
//uint32_t neurons_in_pop;
uint32_t neuron_impl_neurons_in_partition;

//! Array of neuron states
neuron_t *neuron_array;

//! Input states array
static input_type_t *input_type_array;

//! Additional input array
static additional_input_t *additional_input_array;

//! Threshold states array
static threshold_type_t *threshold_type_array;

//! Global parameters for the neurons
//global_neuron_params_t global_parameters;

//! The synapse shaping parameters
static synapse_types_t *synapse_types_array;

//! The number of steps to run per timestep
static uint n_steps_per_timestep;

// Bool to regularise on the first run
static bool initial_regularise = true;

static bool neuron_impl_initialise(uint32_t n_neurons) {
    // allocate DTCM for the global parameter details
//    if (sizeof(global_neuron_params_t)) {
//        global_parameters = spin1_malloc(sizeof(global_neuron_params_t));
//        if (global_parameters == NULL) {
//            log_error("Unable to allocate global neuron parameters"
//                    "- Out of DTCM");
//            return false;
//        }
//    }

    // Allocate DTCM for neuron array
    if (sizeof(neuron_t)) {
        neuron_array = spin1_malloc(n_neurons * sizeof(neuron_t));
        if (neuron_array == NULL) {
            log_error("Unable to allocate neuron array - Out of DTCM %u %u",
            		n_neurons, sizeof(neuron_t));
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
    if (sizeof(synapse_types_t)) {
        synapse_types_array =
                spin1_malloc(n_neurons * sizeof(synapse_types_t));
        if (synapse_types_array == NULL) {
            log_error("Unable to allocate synapse types array - Out of DTCM");
            return false;
        }
    }

    return true;
}

static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // simple wrapper to synapse type input function
    synapse_types_t *parameters = &synapse_types_array[neuron_index];
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

    // get number of neurons running on this core for use during execution
    neuron_impl_neurons_in_partition = n_neurons;

    // Read the number of steps per timestep
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

    //

//    if (sizeof(global_neuron_params_t)) {
//        log_debug("writing neuron global parameters");
//        spin1_memcpy(global_parameters, &address[next],
//                sizeof(global_neuron_params_t));
//        next += n_words_needed(sizeof(global_neuron_params_t));
//    }

//    if (sizeof(neuron_t)) {
//        log_debug("reading neuron local parameters");
//        spin1_memcpy(neuron_array, &address[next],
//                n_neurons * sizeof(neuron_t));
//        next += n_words_needed(n_neurons * sizeof(neuron_t));
//    }
//
//    if (sizeof(input_type_t)) {
//        log_debug("reading input type parameters");
//        spin1_memcpy(input_type_array, &address[next],
//                n_neurons * sizeof(input_type_t));
//        next += n_words_needed(n_neurons * sizeof(input_type_t));
//    }
//
//    if (sizeof(threshold_type_t)) {
//        log_debug("reading threshold type parameters");
//        spin1_memcpy(threshold_type_array, &address[next],
//                n_neurons * sizeof(threshold_type_t));
//        next += n_words_needed(n_neurons * sizeof(threshold_type_t));
//    }
//
//    if (sizeof(synapse_param_t)) {
//        log_debug("reading synapse parameters");
//        spin1_memcpy(neuron_synapse_shaping_params, &address[next],
//                n_neurons * sizeof(synapse_param_t));
//        next += n_words_needed(n_neurons * sizeof(synapse_param_t));
//    }
//
//    if (sizeof(additional_input_t)) {
//        log_debug("reading additional input type parameters");
//        spin1_memcpy(additional_input_array, &address[next],
//                n_neurons * sizeof(additional_input_t));
//        next += n_words_needed(n_neurons * sizeof(additional_input_t));
//    }

    // Global parameters are no longer a thing, so work out where these need to go
//    neuron_model_set_global_neuron_params(global_parameters);

    // **********************************************
    // ******** for eprop regularisation ************
    // **********************************************

    // I don't think the below is necessary any more assuming these get set correctly
    // in the neuron model (these are now set in neuron_model_initialise() )
//    if (initial_regularise) {
//    	global_parameters->core_target_rate = global_parameters->core_target_rate;
////    			* n_neurons; // scales target rate depending on number of neurons
//    	global_parameters->core_pop_rate = 0.k;//global_parameters->core_pop_rate;
////    			* n_neurons; // scale initial value, too
//
//    	initial_regularise = false;
//    }

    // This can probably be commented out at some point as well
//    for (index_t n = 0; n < n_neurons; n++) {
//        neuron_model_print_parameters(&neuron_array[n]);
//        log_debug("Neuron id %u", n);
//        neuron_model_print_state_variables(&neuron_array[n]);
//    }

#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
        neuron_model_print_state_variables(&neuron_array[n]);
    }
    log_debug("-------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}

//static bool neuron_impl_do_timestep_update(index_t neuron_index,
//        input_t external_bias, state_t *recorded_variable_values) {

static void neuron_impl_do_timestep_update(
		uint32_t timer_count, uint32_t time, uint32_t n_neurons) {

//	if (neuron_index == 0) {
//		// Decay global rate trace (only done once per core per timestep)
//		global_parameters->core_pop_rate = global_parameters->core_pop_rate
//				* global_parameters->rate_exp_TC;
//	}

	for (uint32_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

//		log_info("timestep_update neuron_index %u time %u ", neuron_index, time);

		// Get the neuron itself
		neuron_t *neuron = &neuron_array[neuron_index];

		// Decay the "global" rate trace
		neuron->core_pop_rate = neuron->core_pop_rate * neuron->rate_exp_TC;

		// Get the input_type parameters and voltage for this neuron
		input_type_t *input_type = &input_type_array[neuron_index];

		// Get threshold and additional input parameters for this neuron
	//    threshold_type_pointer_t threshold_type =
	//            &threshold_type_array[neuron_index];
		additional_input_t *additional_input =
				&additional_input_array[neuron_index];
		synapse_types_t *synapse_type =
				&synapse_types_array[neuron_index];

		// This would be where a steps per timestep loop begins if desired

		// Get the voltage
		state_t voltage = neuron_model_get_membrane_voltage(neuron);
		state_t B_t = neuron->B; // cache last timestep threshold level
		state_t z_t = neuron->z;

	//    recorded_variable_values[V_RECORDING_INDEX] = voltage;

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

	//    // Sum g_syn contributions from all receptors for recording
	//    REAL total_exc = 0;
	//    REAL total_inh = 0;
	//
	//    for (int i = 0; i < NUM_EXCITATORY_RECEPTORS; i++) {
	//        total_exc += exc_input_values[i];
	//    }
	//    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++) {
	//        total_inh += inh_input_values[i];
	//    }

	//    // Call functions to get the input values to be recorded
	//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = total_exc;
	//    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] =
	//    		global_parameters->core_pop_rate;

		// Call functions to convert exc_input and inh_input to current
		input_type_convert_excitatory_input_to_current(
				exc_input_values, input_type, voltage);
		input_type_convert_inhibitory_input_to_current(
				inh_input_values, input_type, voltage);

		REAL current_offset = current_source_get_offset(time, neuron_index);

		input_t external_bias = additional_input_get_input_value_as_current(
				additional_input, voltage);

		// determine if a spike should occur
		threshold_type_update_threshold(neuron->z, neuron);

		// Record B
	//    if (neuron_index == 0){
	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = global_parameters->core_pop_rate / neurons_in_pop; // divide by neurons on core to get average per neuron contribution to core pop rate
	////        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[neuron_index].el_a; // divide by neurons on core to get average per neuron contribution to core pop rate
	//    }
	//    else{
	//
	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] =
	//        		B_t; // neuron->B;
	////                neuron->L;
	//    //    		neuron->syn_state[0].z_bar;
	//    //    		global_parameters->core_target_rate;
	//    //    	neuron->syn_state[0].e_bar;
	//    //    	neuron->syn_state[neuron_index].el_a;
	//    //    		exc_input_values[0]; // record input input (signed)
	//    //    		learning_signal * neuron->w_fb;
	//    }
	//    if(neuron_index % 2 == 0){
	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].el_a;
	////        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].delta_w;
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].e_bar;
	////        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_value;
	//    }
	////    else if (neuron_index == 0){
	////    }
	//    else{
	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].el_a;
	////        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].delta_w;
	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].e_bar;
	////        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_input_values;
	//    }

		// Simplified what was below this to choose which delta_w to record for different indices
		if ((neuron_index == 0) || (neuron_index == 1) || (neuron_index == 2)) {
//			log_info("z_bar_inp %k (10 + neuron_index) %u L %k time %u",
//					neuron->syn_state[10+neuron_index].z_bar_inp, 10+neuron_index, neuron->L, time);
			neuron_recording_record_accum(
					GSYN_INH_RECORDING_INDEX, neuron_index,
					neuron->syn_state[10+neuron_index].delta_w);
		}
		else {
//			log_info("z_bar_inp %k neuron_index %u L %k time %u",
//					neuron->syn_state[0+neuron_index].z_bar_inp, neuron_index, neuron->L, time);
			neuron_recording_record_accum(
					GSYN_INH_RECORDING_INDEX, neuron_index,
					neuron->syn_state[0+neuron_index].delta_w);
		}

//		if(neuron_index == 0){
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].el_a;
//			recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].delta_w;
//	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].e_bar;
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_value;
//		}
//	//    else if (neuron_index == 0){
//	//    }
//		else if(neuron_index == 1){
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[20+neuron_index].el_a;
//			recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].delta_w;
//	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].e_bar;
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_value;
//		}
//		else if(neuron_index == 2){
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[20+neuron_index].el_a;
//			recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].delta_w;
//	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].e_bar;
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_value;
//		}
//		else{
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].el_a;
//			recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].delta_w;
//	//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].e_bar;
//	//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_input_values;
//		}
//	//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[neuron_index].el_a;
//	//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->B;

//		log_info("Updating neuron parameters B_t = %k ", B_t);

		// update neuron parameters
		state_t result = neuron_model_state_update(
				NUM_EXCITATORY_RECEPTORS, exc_input_values,
				NUM_INHIBITORY_RECEPTORS, inh_input_values,
				external_bias, current_offset, neuron, B_t);

//		REAL accum_time = (accum)(time%13000) * 0.001;
//		if (!accum_time){
//			accum_time += 1.k;
//		}
	//    REAL reg_learning_signal = (global_parameters->core_pop_rate
	////                                    / ((accum)(time%1300)
	////                                    / (1.225k
	//                                    / (accum_time
	//                                    * (accum)neuron_impl_neurons_in_partition))
	//                                    - global_parameters->core_target_rate;
	//    REAL reg_learning_signal = global_parameters->core_target_rate - (global_parameters->core_pop_rate / neuron_impl_neurons_in_partition);
	//    REAL reg_learning_signal = (global_parameters->core_pop_rate / neuron_impl_neurons_in_partition) - global_parameters->core_target_rate;
//		REAL reg_learning_signal = (
//				neuron->core_pop_rate / neuron_impl_neurons_in_partition) - neuron->core_target_rate;
		REAL reg_learning_signal = kdivui(
				neuron->core_pop_rate, neuron_impl_neurons_in_partition) - neuron->core_target_rate;
//		recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = reg_learning_signal;//global_parameters->core_pop_rate;
		neuron_recording_record_accum(
				GSYN_EXC_RECORDING_INDEX, neuron_index, reg_learning_signal);

		// Also update Z (including using refractory period information)
		// TODO: there's quite a few divides lurking in this code, it may
		//       be worth looking to see if any of them can be replaced

//		log_info("Check: voltage %k neuron->B %k time %u", voltage, neuron->B, time);

		// Can't replace this (yet) with kdivk as that only works for positive accums
		state_t nu = (voltage - neuron->B)/neuron->B;

		if (nu > ZERO){
			neuron->z = 1.0k * neuron->A; // implements refractory period
		}


		bool spike = z_t;

//		log_info("time %u neuron_index %u z_t %u spike %u z %k nu %k",
//				time, neuron_index, z_t, spike, neuron->z, nu);


		// *********************************************************
		// Record updated state
		// Record  V (just as cheap to set then to gate later)
//		recorded_variable_values[V_RECORDING_INDEX] = voltage; // result;
		neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, voltage);


	//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] =
	//    		neuron->syn_state[0].delta_w;
	//    		neuron->syn_state[0].z_bar;
	//    		exc_input_values[0]; // record input input (signed)
	//    		z_t;
	//    		global_parameters->core_pop_rate;
	//    		neuron->B;
	//    		neuron->syn_state[0].z_bar;

	//    // Record B
	//    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] =
	////    		B_t; // neuron->B;
	////    		global_parameters->core_target_rate;
	////    	neuron->syn_state[0].e_bar;
	//    	neuron->syn_state[0].el_a;
	//    		total_inh; // total synaptic input from input layer
		// *********************************************************


		// If spike occurs, communicate to relevant parts of model
		if (spike) {
	//        io_printf(IO_BUF, "neuron %u spiked with beta = %k, B_t = %k\n", neuron_index, neuron->beta, neuron->B);
			// Call relevant model-based functions
			// Tell the neuron model
			neuron_model_has_spiked(neuron);
	//        io_printf(IO_BUF, "neuron %u thresholded beta = %k, B_t = %k\n", neuron_index, neuron->beta, neuron->B);

			// Tell the additional input
			additional_input_has_spiked(additional_input);

			// Add contribution from this neuron's spike to global rate trace
			// Make sure it's the same across all neurons
			for (uint32_t n_ind=0; n_ind < n_neurons; n_ind++) {
				neuron_t *global_neuron = &neuron_array[n_ind];
				global_neuron->core_pop_rate += 1.0k;
			}

			// Record spike
			neuron_recording_record_bit(SPIKE_RECORDING_BITFIELD, neuron_index);

			// Send spike
			send_spike(timer_count, time, neuron_index);
		}

		// Shape the existing input according to the included rule
		synapse_types_shape_input(synapse_type);

		// The steps per timestep loop would end here if it was used

#if LOG_LEVEL >= LOG_DEBUG
		neuron_model_print_state_variables(neuron);
#endif // LOG_LEVEL >= LOG_DEBUG

//		// Return the boolean to the model timestep update
//		return spike;
	}
}

//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("writing parameters");
    //if (global_parameters == NULL) {
    //   log_error("global parameter storage not allocated");
    //   rt_error(RTE_SWERR);
    //   return;
    //}

    // Skip steps per timestep
    next += 1;

//    if (sizeof(global_neuron_params_t)) {
//        log_debug("writing neuron global parameters");
//        spin1_memcpy(&address[next], global_parameters,
//                sizeof(global_neuron_params_t));
//        next += n_words_needed(sizeof(global_neuron_params_t));
//    }

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

    // Not completely sure this next loop for printing is necessary
    log_debug("****** STORING ******");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
        log_debug("Neuron id %u", n);
        neuron_model_print_state_variables(&neuron_array[n]);
    }
    log_debug("****** STORING COMPLETE ******");

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

    log_debug("neuron 0 'global' parameters, core_target_rate, core_pop_rate %k %k",
    		&neuron_array[0].core_target_rate, &neuron_array[0].core_pop_rate);
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
	    synapse_types_print_parameters(&synapse_types_array[n]);
	}
	log_debug("-------------------------------------\n");
}

const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
	return synapse_types_get_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_STANDARD_H_
