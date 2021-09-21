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

#ifndef _NEURON_IMPL_SEMD_H_
#define _NEURON_IMPL_SEMD_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/models/neuron_model_lif_impl.h>
#include <neuron/threshold_types/threshold_type_static.h>
#include <synapse/synapse_types/synapse_types_exponential_impl.h>

// Further includes
#include <common/out_spikes.h>
#include <recording.h>
#include <debug.h>

#define V_RECORDING_INDEX 0
#define GSYN_EXCITATORY_RECORDING_INDEX 1
#define GSYN_INHIBITORY_RECORDING_INDEX 2

typedef struct input_type_current_semd_t {
    // multiplicator
    REAL multiplicator[NUM_INHIBITORY_RECEPTORS];

    // previous input value
    REAL inh_input_previous[NUM_INHIBITORY_RECEPTORS];
} input_type_current_semd_t;

#define SCALING_FACTOR 40.0k

static input_type_current_semd_t *input_type_array;

//! Array of neuron states
static neuron_pointer_t neuron_array;

//! Threshold states array
static threshold_type_pointer_t threshold_type_array;

// The synapse shaping parameters
static synapse_param_t *neuron_synapse_shaping_params;

static bool neuron_impl_initialise(uint32_t n_neurons) {
    // Allocate DTCM for neuron array
    neuron_array = spin1_malloc(n_neurons * sizeof(neuron_t));
    if (neuron_array == NULL) {
        log_error("Unable to allocate neuron array - Out of DTCM");
        return false;
    }

    // Allocate DTCM for input type array and copy block of data
    input_type_array =
            spin1_malloc(n_neurons * sizeof(input_type_current_semd_t));
    if (input_type_array == NULL) {
        log_error("Unable to allocate input type array - Out of DTCM");
        return false;
    }

    // Allocate DTCM for threshold type array and copy block of data
    threshold_type_array = spin1_malloc(n_neurons * sizeof(threshold_type_t));
    if (threshold_type_array == NULL) {
        log_error("Unable to allocate threshold type array - Out of DTCM");
        return false;
    }

    // Allocate DTCM for synapse shaping parameters
    neuron_synapse_shaping_params =
            spin1_malloc(n_neurons * sizeof(synapse_param_t));
    if (neuron_synapse_shaping_params == NULL) {
        log_error("Unable to allocate synapse parameters array"
            " - Out of DTCM");
        return false;
    }

    return true;
}

static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // simple wrapper to synapse type input function
    synapse_param_t *parameters = &neuron_synapse_shaping_params[neuron_index];
    synapse_types_add_neuron_input(synapse_type_index,
            parameters, weights_this_timestep);
}

static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("writing parameters, next is %u, n_neurons is %u ",
            next, n_neurons);

    log_debug("writing neuron local parameters");
    spin1_memcpy(neuron_array, &address[next], n_neurons * sizeof(neuron_t));
    next += (n_neurons * sizeof(neuron_t)) / 4;

    log_debug("writing input type parameters");
    spin1_memcpy(input_type_array, &address[next],
            n_neurons * sizeof(input_type_current_semd_t));
    next += (n_neurons * sizeof(input_type_current_semd_t)) / 4;

    log_debug("writing threshold type parameters");
    spin1_memcpy(threshold_type_array, &address[next],
            n_neurons * sizeof(threshold_type_t));
    next += (n_neurons * sizeof(threshold_type_t)) / 4;

    log_debug("writing synapse parameters");
    spin1_memcpy(neuron_synapse_shaping_params, &address[next],
            n_neurons * sizeof(synapse_param_t));
}

static bool neuron_impl_do_timestep_update(index_t neuron_index,
        input_t external_bias, state_t *recorded_variable_values) {
    // Get the neuron itself
    neuron_pointer_t neuron = &neuron_array[neuron_index];

    // Get the input_type parameters and voltage for this neuron
    input_type_current_semd_t *input_type = &input_type_array[neuron_index];

    // Get threshold synapse parameters for this neuron
    threshold_type_pointer_t threshold_type =
            &threshold_type_array[neuron_index];
    synapse_param_pointer_t synapse_type =
            &neuron_synapse_shaping_params[neuron_index];

    // Get the voltage
    state_t voltage = neuron_model_get_membrane_voltage(neuron);
    recorded_variable_values[V_RECORDING_INDEX] = voltage;

    // Get the exc and inh values from the synapses
    input_t* exc_input_values =
            synapse_types_get_excitatory_input(synapse_type);
    input_t* inh_input_values =
            synapse_types_get_inhibitory_input(synapse_type);

    // Set the inhibitory multiplicator value
    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++) {
        if ((inh_input_values[i] >= 0.01) &&
                (input_type->multiplicator[i] == 0) &&
                (input_type->inh_input_previous[i] == 0)) {
            input_type->multiplicator[i] = exc_input_values[i];
        } else if (inh_input_values[i] < 0.01) {
            input_type->multiplicator[i] = 0;
        }
        input_type->inh_input_previous[i] = inh_input_values[i];
    }

    // Sum g_syn contributions from all receptors for recording
    REAL total_exc = 0;
    REAL total_inh = 0;

    for (int i = 0; i < NUM_EXCITATORY_RECEPTORS; i++) {
        total_exc += exc_input_values[i];
    }
    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++) {
        total_inh += inh_input_values[i];
    }

    // Call functions to get the input values to be recorded
    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = total_exc;
    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = total_inh;

    // This changes inhibitory to excitatory input
    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++) {
        inh_input_values[i] = -inh_input_values[i] * SCALING_FACTOR
                * input_type->multiplicator[i];
    }

    // update neuron parameters
    state_t result = neuron_model_state_update(
            NUM_EXCITATORY_RECEPTORS, exc_input_values,
            NUM_INHIBITORY_RECEPTORS, inh_input_values, external_bias, neuron);

    // determine if a spike should occur
    bool spike = threshold_type_is_above_threshold(result, threshold_type);

    // If spike occurs, communicate to relevant parts of model
    if (spike) {
        // Call relevant model-based functions
        // Tell the neuron model
        neuron_model_has_spiked(neuron);
    }

    // Shape the existing input according to the included rule
    synapse_types_shape_input(synapse_type);

    // Return the boolean to the model timestep update
    return spike;
}

//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("writing parameters");

    log_debug("writing neuron local parameters");
    spin1_memcpy(&address[next], neuron_array,
            n_neurons * sizeof(neuron_t));
    next += (n_neurons * sizeof(neuron_t)) / 4;

    log_debug("writing input type parameters");
    spin1_memcpy(&address[next], input_type_array,
            n_neurons * sizeof(input_type_current_semd_t));
    next += (n_neurons * sizeof(input_type_current_semd_t)) / 4;

    log_debug("writing threshold type parameters");
    spin1_memcpy(&address[next], threshold_type_array,
            n_neurons * sizeof(threshold_type_t));
    next += (n_neurons * sizeof(threshold_type_t)) / 4;

    log_debug("writing synapse parameters");
    spin1_memcpy(&address[next], neuron_synapse_shaping_params,
            n_neurons * sizeof(synapse_param_t));
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

#endif // _NEURON_IMPL_SEMD_H_
