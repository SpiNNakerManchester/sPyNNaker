/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Inlined neuron implementation following standard component model
#ifndef _NEURON_IMPL_STANDARD_H_
#define _NEURON_IMPL_STANDARD_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/models/neuron_model.h>
#include <neuron/input_types/input_type.h>
#include <neuron/additional_inputs/additional_input.h>
#include <neuron/threshold_types/threshold_type.h>
#include <neuron/synapse_types/synapse_types.h>

#include <neuron/current_sources/current_source.h>

// Further includes
#include <debug.h>
#include <bit_field.h>
#include <recording.h>

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

// This import depends on variables defined above
#include <neuron/neuron_recording.h>

//! Array of neuron states
static neuron_t *neuron_array;

//! Input states array
static input_type_t *input_type_array;

//! Additional input array
static additional_input_t *additional_input_array;

//! Threshold states array
static threshold_type_t *threshold_type_array;

//! The synapse shaping parameters
static synapse_types_t *synapse_types_array;

//! The number of steps to run per timestep
static uint n_steps_per_timestep;

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Initialise the particular implementation of the data
//! \param[in] n_neurons: The number of neurons
//! \return True if successful
static bool neuron_impl_initialise(uint32_t n_neurons) {

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

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Add inputs to the neuron
//! \param[in] synapse_type_index: the synapse type (e.g. exc. or inh.)
//! \param[in] neuron_index: the index of the neuron
//! \param[in] weights_this_timestep: weight inputs to be added
static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // simple wrapper to synapse type input function
    synapse_types_t *parameters = &synapse_types_array[neuron_index];
    synapse_types_add_neuron_input(synapse_type_index,
            parameters, weights_this_timestep);
}

//! \brief The number of _words_ required to hold an object of given size
//! \param[in] size: The size of object
//! \return Number of words needed to hold the object (not bytes!)
static uint32_t n_words_needed(size_t size) {
    return (size + (sizeof(uint32_t) - 1)) / sizeof(uint32_t);
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Load in the neuron parameters
//! \param[in] address: SDRAM block to read parameters from
//! \param[in] next: Offset of next address in store
//! \param[in] n_neurons: number of neurons
//! \param[in] save_initial_state: If not 0, SDRAM block to copy parameters to
static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons,
		address_t save_initial_state) {

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

#if LOG_LEVEL >= LOG_DEBUG
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
        neuron_model_print_state_variables(&neuron_array[n]);
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Do the timestep update for the particular implementation
//! \param[in] timer_count: The timer count, used for TDMA packet spreading
//! \param[in] time: The time step of the update
//! \param[in] n_neurons: The number of neurons
static void neuron_impl_do_timestep_update(
        uint32_t timer_count, uint32_t time, uint32_t n_neurons) {

    for (uint32_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

        // Get the neuron itself
        neuron_t *this_neuron = &neuron_array[neuron_index];

        // Get the input_type parameters and voltage for this neuron
        input_type_t *input_types = &input_type_array[neuron_index];

        // Get threshold and additional input parameters for this neuron
        threshold_type_t *the_threshold_type = &threshold_type_array[neuron_index];
        additional_input_t *additional_inputs = &additional_input_array[neuron_index];
        synapse_types_t *the_synapse_type = &synapse_types_array[neuron_index];

        // Loop however many times requested; do this in reverse for efficiency,
        // and because the index doesn't actually matter
        for (uint32_t i_step = n_steps_per_timestep; i_step > 0; i_step--) {
            // Get the voltage
            state_t soma_voltage = neuron_model_get_membrane_voltage(this_neuron);

            // Get the exc and inh values from the synapses
            input_t exc_values[NUM_EXCITATORY_RECEPTORS];
            input_t *exc_syn_values =
                    synapse_types_get_excitatory_input(exc_values, the_synapse_type);
            input_t inh_values[NUM_INHIBITORY_RECEPTORS];
            input_t *inh_syn_values =
                    synapse_types_get_inhibitory_input(inh_values, the_synapse_type);

            // Call functions to obtain exc_input and inh_input
            input_t *exc_input_values = input_type_get_input_value(
                    exc_syn_values, input_types, NUM_EXCITATORY_RECEPTORS);
            input_t *inh_input_values = input_type_get_input_value(
                    inh_syn_values, input_types, NUM_INHIBITORY_RECEPTORS);

            // Sum g_syn contributions from all receptors for recording
            REAL total_exc = ZERO;
            REAL total_inh = ZERO;

            for (int i = 0; i < NUM_EXCITATORY_RECEPTORS; i++) {
                total_exc += exc_input_values[i];
            }
            for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++) {
                total_inh += inh_input_values[i];
            }

            // Do recording if on the first step
            if (i_step == n_steps_per_timestep) {
                neuron_recording_record_accum(
                        V_RECORDING_INDEX, neuron_index, soma_voltage);
                neuron_recording_record_accum(
                        GSYN_EXC_RECORDING_INDEX, neuron_index, total_exc);
                neuron_recording_record_accum(
                        GSYN_INH_RECORDING_INDEX, neuron_index, total_inh);
            }

            // Call functions to convert exc_input and inh_input to current
            input_type_convert_excitatory_input_to_current(
                    exc_input_values, input_types, soma_voltage);
            input_type_convert_inhibitory_input_to_current(
                    inh_input_values, input_types, soma_voltage);

            // Get any input from an injected current source
            REAL current_offset = current_source_get_offset(time, neuron_index);

            // Get any external bias input
            input_t external_bias = additional_input_get_input_value_as_current(
                    additional_inputs, soma_voltage);

            // update neuron parameters
            state_t result = neuron_model_state_update(
                    NUM_EXCITATORY_RECEPTORS, exc_input_values,
                    NUM_INHIBITORY_RECEPTORS, inh_input_values,
                    external_bias, current_offset, this_neuron);

            // determine if a spike should occur
            bool spike_now =
                    threshold_type_is_above_threshold(result, the_threshold_type);

            // If spike occurs, communicate to relevant parts of model
            if (spike_now) {

                // Call relevant model-based functions
                // Tell the neuron model
                neuron_model_has_spiked(this_neuron);

                // Tell the additional input
                additional_input_has_spiked(additional_inputs);

                // Record the spike
                neuron_recording_record_bit(SPIKE_RECORDING_BITFIELD, neuron_index);

                // Send the spike
                send_spike(timer_count, time, neuron_index);
            }

            // Shape the existing input according to the included rule
            synapse_types_shape_input(the_synapse_type);
        }

    #if LOG_LEVEL >= LOG_DEBUG
        neuron_model_print_state_variables(this_neuron);
    #endif // LOG_LEVEL >= LOG_DEBUG
    }
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Stores neuron parameters back into SDRAM
//! \param[out] address: the address in SDRAM to start the store
//! \param[in] next: Offset of next address in store
//! \param[in] n_neurons: number of neurons
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {

    // Skip over the steps per timestep
    next += 1;

    if (sizeof(neuron_t)) {
        neuron_params_t *params = (neuron_params_t *) &address[next];
		for (uint32_t i = 0; i < n_neurons; i++) {
			neuron_model_save_state(&neuron_array[i], &params[i]);
		}
        next += n_words_needed(n_neurons * sizeof(neuron_params_t));
    }

    if (sizeof(input_type_t)) {
        input_type_params_t *params = (input_type_params_t *) &address[next];
		for (uint32_t i = 0; i < n_neurons; i++) {
			input_type_save_state(&input_type_array[i], &params[i]);
		}
        next += n_words_needed(n_neurons * sizeof(input_type_params_t));
    }

    if (sizeof(threshold_type_t)) {
        threshold_type_params_t *params = (threshold_type_params_t *) &address[next];
        for (uint32_t i = 0; i < n_neurons; i++) {
        	threshold_type_save_state(&threshold_type_array[i], &params[i]);
        }
        next += n_words_needed(n_neurons * sizeof(threshold_type_params_t));
    }

    if (sizeof(synapse_types_t)) {
        synapse_types_params_t *params = (synapse_types_params_t *) &address[next];
		for (uint32_t i = 0; i < n_neurons; i++) {
			synapse_types_save_state(&synapse_types_array[i], &params[i]);
		}
        next += n_words_needed(n_neurons * sizeof(synapse_types_params_t));
    }

    if (sizeof(additional_input_t)) {
        additional_input_params_t *params = (additional_input_params_t *) &address[next];
		for (uint32_t i = 0; i < n_neurons; i++) {
			additional_input_save_state(&additional_input_array[i], &params[i]);
		}
        next += n_words_needed(n_neurons * sizeof(additional_input_params_t));
    }
}

#if LOG_LEVEL >= LOG_DEBUG
SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Print the inputs to the neurons
//! \param[in] n_neurons: The number of neurons
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
        for (index_t i = 0; i < n_neurons; i++) {
            synapse_types_t *params = &synapse_types_array[i];
            input_t exc_values[NUM_EXCITATORY_RECEPTORS];
            input_t inh_values[NUM_INHIBITORY_RECEPTORS];
            input_t *exc_input = synapse_types_get_excitatory_input(exc_values, params);
            input_t *inh_input = synapse_types_get_inhibitory_input(inh_values, params);
            input_t input = exc_input[0] - inh_input[0];
            if (bitsk(input) != 0) {
                log_debug("Neuron %3u: input %12.6k (= ", i, input);
                synapse_types_print_input(params);
                log_debug(")");
            }
        }
    }
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Print the synapse parameters of the neurons
//! \param[in] n_neurons: The number of neurons
void neuron_impl_print_synapse_parameters(uint32_t n_neurons) {
    for (index_t n = 0; n < n_neurons; n++) {
        synapse_types_print_parameters(&synapse_types_array[n]);
    }
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Get the synapse type character for a synapse type
//! \param[in] synapse_type: The synapse type
//! \return The descriptor character (sometimes two characters)
const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
    return synapse_types_get_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_STANDARD_H_
