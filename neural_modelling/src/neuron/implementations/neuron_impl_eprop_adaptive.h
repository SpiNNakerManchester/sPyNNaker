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

#ifndef _NEURON_IMPL_STANDARD_H_
#define _NEURON_IMPL_STANDARD_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/synapse_types/synapse_type_eprop_adaptive.h>
#include <neuron/threshold_types/threshold_type_none.h>
#include <neuron/models/neuron_model_eprop_adaptive_impl.h>
#include <neuron/input_types/input_type_current.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>


// Further includes
#include <common/out_spikes.h>
#include <recording.h>
#include <debug.h>

#define V_RECORDING_INDEX 0
#define GSYN_EXCITATORY_RECORDING_INDEX 1
#define GSYN_INHIBITORY_RECORDING_INDEX 2

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

extern uint32_t time;
extern REAL learning_signal[20];
//uint32_t neurons_in_pop;
uint32_t syn_dynamics_neurons_in_partition;

//! Array of neuron states
neuron_pointer_t neuron_array;

//! Input states array
static input_type_pointer_t input_type_array;

//! Additional input array
static additional_input_pointer_t additional_input_array;

//! Threshold states array
static threshold_type_pointer_t threshold_type_array;

//! Global parameters for the neurons
global_neuron_params_pointer_t global_parameters;

// The synapse shaping parameters
static synapse_param_t *neuron_synapse_shaping_params;

// Bool to regularise on the first run
static bool initial_regularise = true;

static bool neuron_impl_initialise(uint32_t n_neurons) {
    // allocate DTCM for the global parameter details
    if (sizeof(global_neuron_params_t)) {
        global_parameters = spin1_malloc(sizeof(global_neuron_params_t));
        if (global_parameters == NULL) {
            log_error("Unable to allocate global neuron parameters"
                    "- Out of DTCM");
            return false;
        }
    }

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
    if (sizeof(synapse_param_t)) {
        neuron_synapse_shaping_params =
                spin1_malloc(n_neurons * sizeof(synapse_param_t));
        if (neuron_synapse_shaping_params == NULL) {
            log_error("Unable to allocate synapse parameters array"
                    " - Out of DTCM");
            return false;
        }
    }

    return true;
}

static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // simple wrapper to synapse type input function
    synapse_param_pointer_t parameters =
            &neuron_synapse_shaping_params[neuron_index];
    synapse_types_add_neuron_input(synapse_type_index,
            parameters, weights_this_timestep);
}

static uint32_t n_words_needed(uint32_t size) {
    return (size + (sizeof(uint32_t) - 1)) / sizeof(uint32_t);
}

static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("reading parameters, next is %u, n_neurons is %u ",
            next, n_neurons);

    syn_dynamics_neurons_in_partition = n_neurons; // get number of neurons running on this core for use during execution

    if (sizeof(global_neuron_params_t)) {
        log_debug("writing neuron global parameters");
        spin1_memcpy(global_parameters, &address[next],
                sizeof(global_neuron_params_t));
        next += n_words_needed(sizeof(global_neuron_params_t));
    }

    if (sizeof(neuron_t)) {
        log_debug("reading neuron local parameters");
        spin1_memcpy(neuron_array, &address[next],
                n_neurons * sizeof(neuron_t));
        next += n_words_needed(n_neurons * sizeof(neuron_t));
    }

    if (sizeof(input_type_t)) {
        log_debug("reading input type parameters");
        spin1_memcpy(input_type_array, &address[next],
                n_neurons * sizeof(input_type_t));
        next += n_words_needed(n_neurons * sizeof(input_type_t));
    }

    if (sizeof(threshold_type_t)) {
        log_debug("reading threshold type parameters");
        spin1_memcpy(threshold_type_array, &address[next],
                n_neurons * sizeof(threshold_type_t));
        next += n_words_needed(n_neurons * sizeof(threshold_type_t));
    }

    if (sizeof(synapse_param_t)) {
        log_debug("reading synapse parameters");
        spin1_memcpy(neuron_synapse_shaping_params, &address[next],
                n_neurons * sizeof(synapse_param_t));
        next += n_words_needed(n_neurons * sizeof(synapse_param_t));
    }

    if (sizeof(additional_input_t)) {
        log_debug("reading additional input type parameters");
        spin1_memcpy(additional_input_array, &address[next],
                n_neurons * sizeof(additional_input_t));
        next += n_words_needed(n_neurons * sizeof(additional_input_t));
    }

    neuron_model_set_global_neuron_params(global_parameters);

    // **********************************************
    // ******** for eprop regularisation ************
    // **********************************************
    if (initial_regularise) {
    	global_parameters->core_target_rate = global_parameters->core_target_rate;
//    			* n_neurons; // scales target rate depending on number of neurons
    	global_parameters->core_pop_rate = global_parameters->core_target_rate * syn_dynamics_neurons_in_partition;//0.k;//global_parameters->core_pop_rate;
//    			* n_neurons; // scale initial value, too

    	initial_regularise = false;
    }

    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
        log_debug("Neuron id %u", n);
        neuron_model_print_state_variables(&neuron_array[n]);
    }

#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
    }
    log_debug("-------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}

static bool neuron_impl_do_timestep_update(index_t neuron_index,
        input_t external_bias, state_t *recorded_variable_values) {


	if (neuron_index == 0) {
		// Decay global rate trace (only done once per core per timestep)
		global_parameters->core_pop_rate = global_parameters->core_pop_rate
				* global_parameters->rate_exp_TC;
	}


    // Get the neuron itself
    neuron_pointer_t neuron = &neuron_array[neuron_index];

    // Get the input_type parameters and voltage for this neuron
    input_type_pointer_t input_type = &input_type_array[neuron_index];

    // Get threshold and additional input parameters for this neuron
//    threshold_type_pointer_t threshold_type =
//            &threshold_type_array[neuron_index];
    additional_input_pointer_t additional_input =
            &additional_input_array[neuron_index];
    synapse_param_pointer_t synapse_type =
            &neuron_synapse_shaping_params[neuron_index];

    // Get the voltage
    state_t voltage = neuron_model_get_membrane_voltage(neuron);
    state_t B_t = neuron->B; // cache last timestep threshold level
    state_t z_t = neuron->z;

//    recorded_variable_values[V_RECORDING_INDEX] = voltage;

    // Get the exc and inh values from the synapses
    input_t* exc_value = synapse_types_get_excitatory_input(synapse_type);
    input_t* inh_value = synapse_types_get_inhibitory_input(synapse_type);

    // Call functions to obtain exc_input and inh_input
    input_t* exc_input_values = input_type_get_input_value(
            exc_value, input_type, NUM_EXCITATORY_RECEPTORS);
    input_t* inh_input_values = input_type_get_input_value(
            inh_value, input_type, NUM_INHIBITORY_RECEPTORS);

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

    external_bias += additional_input_get_input_value_as_current(
            additional_input, voltage);

    // determine if a spike should occur
    threshold_type_update_threshold(neuron->z, neuron);

//    if(time % 1000 > 100 && time % 1000 < 600){
    neuron->neuron_rate = neuron->neuron_rate * 0.9998k;//global_parameters->rate_exp_TC;
//    }


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
    if(neuron_index % 4 == 0){
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].el_a;
        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].delta_w * global_parameters->eta;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[600+neuron_index].e_bar;
//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[600+neuron_index].z_bar_inp;
//        recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[600+neuron_index].z_bar_inp;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->L;
//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].e_bar;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_value;
    }
//    else if (neuron_index == 0){
//    }
    else if(neuron_index % 4 == 1){
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[20+neuron_index].el_a;
        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[200+neuron_index].delta_w * global_parameters->eta;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[590+neuron_index].e_bar;
//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[590+neuron_index].z_bar_inp;
//        recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[590+neuron_index].z_bar;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->L;
//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].e_bar;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_value;
    }
    else if(neuron_index % 4 == 2){
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[20+neuron_index].el_a;
        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[500+neuron_index].delta_w * global_parameters->eta;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[500+neuron_index].e_bar;
//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[500+neuron_index].z_bar_inp;
//        recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[500+neuron_index].z_bar;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->L;
//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].e_bar;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_value;
    }
    else{
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[10+neuron_index].el_a;
        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].delta_w * global_parameters->eta;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].e_bar;
//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].z_bar_inp;
//        recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].z_bar;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->L;
//        recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[0+neuron_index].e_bar;
//        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = *exc_input_values;
    }
//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[neuron_index].el_a;
//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->B;
    // update neuron parameters
    state_t result = neuron_model_state_update(
            NUM_EXCITATORY_RECEPTORS, exc_input_values,
            NUM_INHIBITORY_RECEPTORS, inh_input_values,
            external_bias, neuron, B_t);

//    REAL accum_time = (accum)(time%13000) * 0.001;
//    if (!accum_time){
//        accum_time += 1.k;
//    }
//    REAL reg_learning_signal = (global_parameters->core_pop_rate
////                                    / ((accum)(time%1300)
////                                    / (1.225k
//                                    / (accum_time
//                                    * (accum)syn_dynamics_neurons_in_partition))
//                                    - global_parameters->core_target_rate;
//    REAL reg_learning_signal = global_parameters->core_target_rate - (global_parameters->core_pop_rate / syn_dynamics_neurons_in_partition);
//    REAL reg_learning_signal = (global_parameters->core_pop_rate / syn_dynamics_neurons_in_partition) - global_parameters->core_target_rate;
//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] =
//                                            neuron->neuron_rate;
//                                            neuron->L;
//                                            neuron->syn_state[neuron_index].z_bar;
                                            //reg_learning_signal;//




    // Also update Z (including using refractory period information)
    state_t nu = (voltage - neuron->B)/neuron->B;

    if (nu > ZERO){
    	neuron->z = 1.0k * neuron->A; // implements refractory period
    }

    bool spike = z_t;



    // *********************************************************
    // Record updated state
    // Record  V (just as cheap to set then to gate later)
    recorded_variable_values[V_RECORDING_INDEX] = voltage; // result;
//    recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[350+neuron_index].z_bar; // result;
//    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].e_bar;
//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].z_bar_inp;
//    recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].z_bar;
//    recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].e_bar;
//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].z_bar_inp;
//    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[300+neuron_index].z_bar;
//    recorded_variable_values[V_RECORDING_INDEX] = neuron->syn_state[300].e_bar;
//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = voltage;
//    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[300].z_bar;


    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] =
//    		neuron->syn_state[0].delta_w;
//    		neuron->syn_state[0].z_bar;
//    		exc_input_values[0]; // record input input (signed)
//    		z_t;
//    		global_parameters->core_pop_rate;
//    		neuron->B;
    		neuron->neuron_rate;
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
        global_parameters->core_pop_rate += 1k;
        neuron->neuron_rate += 1k;
    }

    // Shape the existing input according to the included rule
    synapse_types_shape_input(synapse_type);

#if LOG_LEVEL >= LOG_DEBUG
    neuron_model_print_state_variables(neuron);
#endif // LOG_LEVEL >= LOG_DEBUG

    // Return the boolean to the model timestep update
    return spike;
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

    if (sizeof(global_neuron_params_t)) {
        log_debug("writing neuron global parameters");
        spin1_memcpy(&address[next], global_parameters,
                sizeof(global_neuron_params_t));
        next += n_words_needed(sizeof(global_neuron_params_t));
    }

    if (sizeof(neuron_t)) {
        log_debug("writing neuron local parameters");
        spin1_memcpy(&address[next], neuron_array,
                n_neurons * sizeof(neuron_t));
        next += n_words_needed(n_neurons * sizeof(neuron_t));
    }

    log_debug("****** STORING ******");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
        log_debug("Neuron id %u", n);
        neuron_model_print_state_variables(&neuron_array[n]);
    }
    log_debug("****** STORING COMPLETE ******");

    if (sizeof(input_type_t)) {
        log_debug("writing input type parameters");
        spin1_memcpy(&address[next], input_type_array,
                n_neurons * sizeof(input_type_t));
        next += n_words_needed(n_neurons * sizeof(input_type_t));
    }

    if (sizeof(threshold_type_t)) {
        log_debug("writing threshold type parameters");
        spin1_memcpy(&address[next], threshold_type_array,
                n_neurons * sizeof(threshold_type_t));
        next += n_words_needed(n_neurons * sizeof(threshold_type_t));
    }

    if (sizeof(synapse_param_t)) {
        log_debug("writing synapse parameters");
        spin1_memcpy(&address[next], neuron_synapse_shaping_params,
                n_neurons * sizeof(synapse_param_t));
        next += n_words_needed(n_neurons * sizeof(synapse_param_t));
    }

    if (sizeof(additional_input_t)) {
        log_debug("writing additional input type parameters");
        spin1_memcpy(&address[next], additional_input_array,
                n_neurons * sizeof(additional_input_t));
        next += n_words_needed(n_neurons * sizeof(additional_input_t));
    }

    log_debug("global_parameters, core_target_rate, core_pop_rate %k %k",
    		global_parameters->core_target_rate, global_parameters->core_pop_rate);
}

#if LOG_LEVEL >= LOG_DEBUG
void neuron_impl_print_inputs(uint32_t n_neurons) {
	bool empty = true;
	for (index_t i = 0; i < n_neurons; i++) {
		empty = empty && (0 == bitsk(
		        synapse_types_get_excitatory_input(&neuron_synapse_shaping_params[i])
		        - synapse_types_get_inhibitory_input(&neuron_synapse_shaping_params[i])));
	}

	if (!empty) {
		log_debug("-------------------------------------\n");

		for (index_t i = 0; i < n_neurons; i++) {
			input_t input =
			        synapse_types_get_excitatory_input(&neuron_synapse_shaping_params[i])
			        - synapse_types_get_inhibitory_input(&neuron_synapse_shaping_params[i]);
			if (bitsk(input) != 0) {
				log_debug("%3u: %12.6k (= ", i, input);
				synapse_types_print_input(&neuron_synapse_shaping_params[i]);
				log_debug(")\n");
			}
		}
		log_debug("-------------------------------------\n");
	}
}

void neuron_impl_print_synapse_parameters(uint32_t n_neurons) {
	log_debug("-------------------------------------\n");
	for (index_t n = 0; n < n_neurons; n++) {
	    synapse_types_print_parameters(&neuron_synapse_shaping_params[n]);
	}
	log_debug("-------------------------------------\n");
}

const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
	return synapse_types_get_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_STANDARD_H_
