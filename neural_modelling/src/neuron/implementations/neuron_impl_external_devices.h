/*
 * Copyright (c) 2017 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Inlined neuron implementation following standard component model
#ifndef _NEURON_IMPL_EXTERNAL_DEVICES_H_
#define _NEURON_IMPL_EXTERNAL_DEVICES_H_

#include "neuron_impl.h"

//! What sort of message payload should we send?
enum send_type {
    SEND_TYPE_INT = 0, //!< Message payload is an `int32_t`
    SEND_TYPE_UINT,    //!< Message payload is an `uint32_t`
    SEND_TYPE_ACCUM,   //!< Message payload is an `accum`
    SEND_TYPE_UACCUM,  //!< Message payload is an `unsigned accum`
    SEND_TYPE_FRACT,   //!< Message payload is a `fract`
    SEND_TYPE_UFRACT,  //!< Message payload is an `unsigned fract`
};

// Includes for model parts used in this implementation

#include <neuron/models/neuron_model_lif_impl.h>
#include <neuron/synapse_types/synapse_types_exponential_impl.h>
#include <neuron/input_types/input_type_current.h>

#include <neuron/current_sources/current_source_impl.h>
#include <neuron/current_sources/current_source.h>

// Further includes
#include <debug.h>


//! The definition of the threshold
typedef struct packet_firing_data_t {
    //! The key to send to update the value
    uint32_t key;
    //! A scaling factor (>0) if the value is to be sent as payload,
    //! False (0) if just the key
    uint32_t value_as_payload;
    //! The minimum allowed value to send as the payload.
    //! Values below are clipped to this value
    accum min_value;
    //! The maximum allowed value to send as the payload.
    //! Values above are clipped to this value
    accum max_value;
    //! The time between sending the value
    uint32_t timesteps_between_sending;
    //! The time until the next sending of the value (initially 0)
    uint32_t time_until_next_send;
    //! Send type
    enum send_type type;
} packet_firing_data_t;

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
    PACKET_RECORDING_BITFIELD = 0,
    //! Number of recorded bitfields
    N_BITFIELD_VARS = 1
};

// This import depends on variables defined above
#include <neuron/neuron_recording.h>

//! Array of neuron states
static neuron_t *neuron_array;

//! Threshold states array
static packet_firing_data_t *packet_firing_array;

//! The synapse shaping parameters
static synapse_types_t *synapse_types_array;

//! The number of steps to run per timestep
static uint n_steps_per_timestep;

// Typesafe magic reinterpret cast
static inline uint _int_bits(int value) {
    typedef union _int_bits_union {
        int int_value;
        uint uint_value;
    } _int_bits_union;

    _int_bits_union converter;
    converter.int_value = value;
    return converter.uint_value;
}

//! \brief Converts the value into the right form for sending as a payload
//! \param[in] type: what type of payload are we really dealing with
//! \param[in] value: the value, after scaling
//! \return The word to go in the multicast packet payload
static inline uint _get_payload(enum send_type type, accum value) {
    switch (type) {
    case SEND_TYPE_INT:
        return _int_bits((int) value);
    case SEND_TYPE_UINT:
        return (uint) value;
    case SEND_TYPE_ACCUM:
        return _int_bits(bitsk(value));
    case SEND_TYPE_UACCUM:
        return bitsuk((unsigned accum) value);
    case SEND_TYPE_FRACT:
        return _int_bits(bitslr((long fract) value));
    case SEND_TYPE_UFRACT:
        return bitsulr((long unsigned fract) value);
    default:
        log_error("Unknown enum value %u", value);
        rt_error(RTE_SWERR);
    }
    return 0;
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Initialise the particular implementation of the data
//! \param[in] n_neurons: The number of neurons
//! \return True if successful
static bool neuron_impl_initialise(uint32_t n_neurons) {

    // Allocate DTCM for neuron array
	log_info("Initialising for %u neurons", n_neurons);
	neuron_array = spin1_malloc(n_neurons * sizeof(neuron_t));
	if (neuron_array == NULL) {
		log_error("Unable to allocate neuron array - Out of DTCM");
		return false;
	}

    // Allocate DTCM for packet firing array and copy block of data
	packet_firing_array =
			spin1_malloc(n_neurons * sizeof(packet_firing_data_t));
	if (packet_firing_array == NULL) {
		log_error("Unable to allocate packet firing array - Out of DTCM");
		return false;
	}

    // Allocate DTCM for synapse shaping parameters
	synapse_types_array =
			spin1_malloc(n_neurons * sizeof(synapse_types_t));
	if (synapse_types_array == NULL) {
		log_error("Unable to allocate synapse parameters array"
				" - Out of DTCM");
		return false;
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
static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons,
		address_t save_initial_state) {

    // Read the number of steps per timestep
    n_steps_per_timestep = address[next++];
    if (n_steps_per_timestep > 1) {
        log_info("Looping over %u steps each timestep", n_steps_per_timestep);
    } else if (n_steps_per_timestep == 0) {
        log_error("bad number of steps per timestep: 0");
    }

	neuron_params_t *neuron_params = (neuron_params_t *) &address[next];
	for (uint32_t i = 0; i < n_neurons; i++) {
		neuron_model_initialise(&neuron_array[i], &neuron_params[i], n_steps_per_timestep);
	}
	next += n_words_needed(n_neurons * sizeof(neuron_params_t));

	spin1_memcpy(packet_firing_array, &address[next],
			n_neurons * sizeof(packet_firing_data_t));
	next += n_words_needed(n_neurons * sizeof(packet_firing_data_t));

	synapse_types_params_t *synapse_params = (synapse_types_params_t *) &address[next];
	for (uint32_t i = 0; i < n_neurons; i++) {
		synapse_types_initialise(&synapse_types_array[i], &synapse_params[i], n_steps_per_timestep);
	}
	next += n_words_needed(n_neurons * sizeof(synapse_types_params_t));

    // If we are to save the initial state, copy the whole of the parameters
	// to the initial state
	if (save_initial_state) {
		spin1_memcpy(save_initial_state, address, next * sizeof(uint32_t));
	}

#if LOG_LEVEL >= LOG_DEBUG
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! \brief Determines if the device should fire
//! \param[in] packet_firing: The parameters to use to determine if it
//!                           should fire now
//! \return True if the neuron should fire
static bool _test_will_fire(packet_firing_data_t *packet_firing) {
    if (packet_firing->time_until_next_send == 0) {
        packet_firing->time_until_next_send =
                packet_firing->timesteps_between_sending;
        --packet_firing->time_until_next_send;
        return true;
    }
    --packet_firing->time_until_next_send;
    return false;
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Do the timestep update for the particular implementation
//! \param[in] timer_count: The timer count, used for TDMA packet spreading
//! \param[in] time: The time step of the update
//! \param[in] n_neurons: The number of neurons
static void neuron_impl_do_timestep_update(
        UNUSED uint32_t timer_count, UNUSED uint32_t time, uint32_t n_neurons) {

    for (uint32_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {
        // Get the neuron itself
        neuron_t *this_neuron = &neuron_array[neuron_index];

        // Get threshold and additional input parameters for this neuron
        packet_firing_data_t *the_packet_firing =
            &packet_firing_array[neuron_index];
        synapse_types_t *the_synapse_type =
                &synapse_types_array[neuron_index];

        // Store whether the neuron has spiked
        bool will_fire = false;

        // Loop however many times requested; do this in reverse for efficiency,
        // and because the index doesn't actually matter
        for (uint32_t i = n_steps_per_timestep; i > 0; i--) {
            // Get the voltage
            state_t soma_voltage = neuron_model_get_membrane_voltage(this_neuron);

            // Get the exc and inh values from the synapses
            input_t exc_values[NUM_EXCITATORY_RECEPTORS];
            input_t *exc_input_values =
                    synapse_types_get_excitatory_input(exc_values, the_synapse_type);
            input_t inh_values[NUM_INHIBITORY_RECEPTORS];
            input_t *inh_input_values =
                    synapse_types_get_inhibitory_input(inh_values, the_synapse_type);

            // Sum g_syn contributions from all receptors for recording
            REAL total_exc = 0;
            REAL total_inh = 0;

            for (int i = 0; i < NUM_EXCITATORY_RECEPTORS; i++) {
                total_exc += exc_input_values[i];
            }
            for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++) {
                total_inh += inh_input_values[i];
            }

            // Do recording if on the first step
            if (i == n_steps_per_timestep) {
                neuron_recording_record_accum(
                        V_RECORDING_INDEX, neuron_index, soma_voltage);
                neuron_recording_record_accum(
                        GSYN_EXC_RECORDING_INDEX, neuron_index, total_exc);
                neuron_recording_record_accum(
                        GSYN_INH_RECORDING_INDEX, neuron_index, total_inh);
            }

            // Get any input from an injected current source
            REAL current_offset = current_source_get_offset(time, neuron_index);

            // update neuron parameters
            state_t result = neuron_model_state_update(
                    NUM_EXCITATORY_RECEPTORS, exc_input_values,
                    NUM_INHIBITORY_RECEPTORS, inh_input_values,
                    0, current_offset, this_neuron);

            // determine if a packet should fly
            will_fire = _test_will_fire(the_packet_firing);

            // If spike occurs, communicate to relevant parts of model
            if (will_fire) {
                if (the_packet_firing->value_as_payload) {
                    accum value_to_send = result;
                    if (result > the_packet_firing->max_value) {
                        value_to_send = the_packet_firing->max_value;
                    }
                    if (result < the_packet_firing->min_value) {
                        value_to_send = the_packet_firing->min_value;
                    }

                    uint payload = _get_payload(
                        the_packet_firing->type,
                        value_to_send * the_packet_firing->value_as_payload);

                    send_spike_mc_payload(the_packet_firing->key, payload);
                } else {
                    send_spike_mc(the_packet_firing->key);
                }
            }

            // Shape the existing input according to the included rule
            synapse_types_shape_input(the_synapse_type);
        }

        if (will_fire) {
            // Record the spike
            neuron_recording_record_bit(PACKET_RECORDING_BITFIELD, neuron_index);
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

	neuron_params_t *neuron_params = (neuron_params_t *) &address[next];
	for (uint32_t i = 0; i < n_neurons; i++) {
		neuron_model_save_state(&neuron_array[i], &neuron_params[i]);
	}
	next += n_words_needed(n_neurons * sizeof(neuron_params_t));

	spin1_memcpy(&address[next], packet_firing_array,
			n_neurons * sizeof(packet_firing_data_t));
	next += n_words_needed(n_neurons * sizeof(packet_firing_data_t));

	synapse_types_params_t *synapse_params = (synapse_types_params_t *) &address[next];
	for (uint32_t i = 0; i < n_neurons; i++) {
		synapse_types_save_state(&synapse_types_array[i], &synapse_params[i]);
	}
	next += n_words_needed(n_neurons * sizeof(synapse_types_params_t));
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
                synapse_types_get_excitatory_input(exc_values, params)
                - synapse_types_get_inhibitory_input(inh_values, params)));
    }

    if (!empty) {
        for (index_t i = 0; i < n_neurons; i++) {
            synapse_types_t *params = &synapse_types_array[i];
            input_t exc_values[NUM_EXCITATORY_RECEPTORS];
            input_t inh_values[NUM_INHIBITORY_RECEPTORS];
            input_t input = synapse_types_get_excitatory_input(exc_values, params)
                    - synapse_types_get_inhibitory_input(inh_values, params);
            if (bitsk(input) != 0) {
                log_debug("%3u: %12.6k (= ", i, input);
                synapse_types_print_input(params);
                log_debug(")\n");
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

#endif // _NEURON_IMPL_EXTERNAL_DEVICES_H_
