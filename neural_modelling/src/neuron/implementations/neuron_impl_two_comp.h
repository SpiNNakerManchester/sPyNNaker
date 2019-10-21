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

#ifndef _NEURON_IMPL_TWO_COMP_H_
#define _NEURON_IMPL_TWO_COMP_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/synapse_types/synapse_types_two_comp_excitatory_exponential_impl.h>
#include <neuron/models/neuron_model_lif_two_comp_impl.h>
#include <neuron/input_types/input_type_two_comp.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>
#include <neuron/threshold_types/threshold_type_static.h>

// Further includes
#include <common/out_spikes.h>
#include <recording.h>
#include <debug.h>
#include <random.h>

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

//! Array of neuron states
static neuron_pointer_t neuron_array;

//! Input states array
static input_type_pointer_t input_type_array;

//! Additional input array
static additional_input_pointer_t additional_input_array;

//! Threshold states array
static threshold_type_pointer_t threshold_type_array;

//! Global parameters for the neurons
static global_neuron_params_pointer_t global_parameters;

// The synapse shaping parameters
static synapse_param_t *neuron_synapse_shaping_params;

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

#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
    }
    log_debug("-------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}



// &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

// Poisson Spike Source Functions

static inline REAL slow_spike_source_get_time_to_spike(
        REAL mean_inter_spike_interval_in_ticks, neuron_pointer_t neuron) {
    return exponential_dist_variate(
            mars_kiss64_seed,
			global_parameters->spike_source_seed
			)
        * mean_inter_spike_interval_in_ticks;
}



static inline void set_spike_source_rate(neuron_pointer_t neuron, REAL rate,
		threshold_type_pointer_t threshold_type) {

	REAL rate_scale = 50.0k;
	rate = rate * rate_scale;

	// clip rate to avoid divide by 0 and overflow
	if (rate < 0.001){
		rate = 0.001;
	} else if (rate > (threshold_type->threshold_value * rate_scale)) {
		rate = threshold_type->threshold_value * rate_scale;
	}

	REAL rate_diff = neuron->rate_at_last_setting - rate;

//	// ensure rate_diff is absolute
//	if REAL_COMPARE(rate_diff, <, REAL_CONST(0.0))
	if (rate_diff < 0.0k){
		rate_diff = -rate_diff;
	}


	// Has rate changed by more than a predefined threshold since it was last
	// used to update the mean isi ticks?
	if ((rate_diff) > neuron->rate_update_threshold){
		// then update the rate
		neuron->rate_at_last_setting = rate;

		// Update isi ticks based on new rate
		neuron->mean_isi_ticks =
		//                rate *
		////				global_parameters->ticks_per_second; // shouldn't this be ticks_per_second/rate?
		//				neuron->ticks_per_second   ; // shouldn't this be ticks_per_second/rate?
		    		(global_parameters->ticks_per_second / rate); // shouldn't this be ticks_per_second/rate?

		// Account for time that's already passed since previous spike
	    neuron->time_to_spike_ticks = neuron->mean_isi_ticks
	    		- neuron->time_since_last_spike;
	} // else stick with existing rate and isi ticks - they're within threshold
}


static inline bool timer_update_determine_poisson_spiked(neuron_pointer_t neuron) {
	// NOTE: ALL SOURCES TREATED AS SLOW SOURCES!!!
	// NOTE: NO SOURCE CAN SPIKE MORE THAN ONCE PER TIMESTEP
    // If this spike source should spike now

	bool has_spiked = false;

	// Advance by one timestep
	// Subtract tick
    neuron->time_to_spike_ticks -= 1.0k;

    // Add tick to time since last spike (to enable for dynamic rate change)
    neuron->time_since_last_spike += 1.0k;


    if (neuron->time_to_spike_ticks <= 0.0k){
        // Update time to spike
    	REAL next_spike_time = slow_spike_source_get_time_to_spike(
                neuron->mean_isi_ticks, neuron);

        neuron->time_to_spike_ticks += next_spike_time;

//    	neuron->time_to_spike_ticks += slow_spike_source_get_time_to_spike(
//    			                neuron->mean_isi_ticks, neuron);

        // Set time since last spike to zero, so we start counting from here
        neuron->time_since_last_spike = 0;

        has_spiked = true;
    }

    return has_spiked;
}

// &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&


static bool neuron_impl_do_timestep_update(index_t neuron_index,
        input_t external_bias, state_t *recorded_variable_values) {
    // Get the neuron itself
    neuron_pointer_t neuron = &neuron_array[neuron_index];

    // Get the input_type parameters and voltage for this neuron
    input_type_pointer_t input_type = &input_type_array[neuron_index];

    // Get threshold and additional input parameters for this neuron
    threshold_type_pointer_t threshold_type =
            &threshold_type_array[neuron_index];
    additional_input_pointer_t additional_input =
            &additional_input_array[neuron_index];
    synapse_param_pointer_t synapse_type =
            &neuron_synapse_shaping_params[neuron_index];

    // Get the voltage
    //state_t voltage = neuron_model_get_membrane_voltage(neuron);
    state_t voltage = neuron->U_membrane;

    // Get the exc and inh values from the synapses
    input_t* exc_value = synapse_types_get_excitatory_input(synapse_type);
    input_t* inh_value = synapse_types_get_inhibitory_input(synapse_type);

    // Call functions to obtain exc_input and inh_input
    input_t* exc_input_values = input_type_get_input_value(
            exc_value, input_type, NUM_EXCITATORY_RECEPTORS);
    input_t* inh_input_values = input_type_get_input_value(
            inh_value, input_type, NUM_INHIBITORY_RECEPTORS);

    // Sum g_syn contributions from all receptors for recording
    REAL total_exc = 0;
    REAL total_inh = 0;

    for (int i = 0; i < NUM_EXCITATORY_RECEPTORS; i++) {
        total_exc += exc_input_values[i];
    }
    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++) {
        total_inh += inh_input_values[i];
    }


    // Call functions to convert exc_input and inh_input to current
    input_type_convert_excitatory_input_to_current(
            exc_input_values, input_type, voltage);
    input_type_convert_inhibitory_input_to_current(
            inh_input_values, input_type, voltage);

    external_bias += additional_input_get_input_value_as_current(
            additional_input, voltage);

    // update neuron parameters
    state_t result = neuron_model_state_update(
            NUM_EXCITATORY_RECEPTORS, exc_input_values,
            NUM_INHIBITORY_RECEPTORS, inh_input_values,
            external_bias, neuron);

    // Call functions to get the input values to be recorded
    recorded_variable_values[V_RECORDING_INDEX] = neuron->U_membrane;
    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->V;
    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->rate_at_last_setting;

    // ************************************************************************
    // determine if a spike should occur
    // bool spike = threshold_type_is_above_threshold(result, threshold_type);
    REAL rate = result;

    // Instead of threshold, update Poisson rate based on membrane potential
    set_spike_source_rate(neuron, rate, threshold_type);

    // and then update Poisson process to determine if spiked
    bool spike = timer_update_determine_poisson_spiked(neuron);
    // ************************************************************************

    // If spike occurs, communicate to relevant parts of model
    if (spike) {
        // Call relevant model-based functions
        // Tell the neuron model
        neuron_model_has_spiked(neuron);

        // Tell the additional input
        additional_input_has_spiked(additional_input);
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
