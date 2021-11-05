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
#include <neuron/additional_inputs/additional_input.h>
#include <neuron/synapse_types/synapse_types_exponential_impl.h>
#include <neuron/input_types/input_type_current.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>
#include "tdma_processing.h"

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

//! Input states array
static input_type_t *input_type_array;

//! Additional input array
static additional_input_t *additional_input_array;

//! Threshold states array
static packet_firing_data_t *packet_firing_array;

//! Global parameters for the neurons
static global_neuron_params_t *global_parameters;

//! The synapse shaping parameters
static synapse_param_t *neuron_synapse_shaping_params;

//! The number of steps to run per timestep
static uint n_steps_per_timestep;

//#ifndef SOMETIMES_UNUSED
//#define SOMETIMES_UNUSED __attribute__((unused))
//#endif // !SOMETIMES_UNUSED


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
    if (sizeof(packet_firing_data_t)) {
        packet_firing_array =
                spin1_malloc(n_neurons * sizeof(packet_firing_data_t));
        if (packet_firing_array == NULL) {
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

SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Add inputs to the neuron
//! \param[in] synapse_type_index: the synapse type (e.g. exc. or inh.)
//! \param[in] neuron_index: the index of the neuron
//! \param[in] weights_this_timestep: weight inputs to be added
static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // simple wrapper to synapse type input function
    synapse_param_t *parameters =
            &neuron_synapse_shaping_params[neuron_index];
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
static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("reading parameters, next is %u, n_neurons is %u ",
            next, n_neurons);

    // Read the number of steps per timestep
    n_steps_per_timestep = address[next++];
    if (n_steps_per_timestep > 1) {
        log_info("Looping over %u steps each timestep", n_steps_per_timestep);
    } else if (n_steps_per_timestep == 0) {
        log_error("bad number of steps per timestep: 0");
    }

    if (sizeof(global_neuron_params_t)) {
        spin1_memcpy(global_parameters, &address[next],
                sizeof(global_neuron_params_t));
        next += n_words_needed(sizeof(global_neuron_params_t));
    }

    if (sizeof(neuron_t)) {
        spin1_memcpy(neuron_array, &address[next],
                n_neurons * sizeof(neuron_t));
        next += n_words_needed(n_neurons * sizeof(neuron_t));
    }

    if (sizeof(input_type_t)) {
        spin1_memcpy(input_type_array, &address[next],
                n_neurons * sizeof(input_type_t));
        next += n_words_needed(n_neurons * sizeof(input_type_t));
    }

    if (sizeof(packet_firing_data_t)) {
        spin1_memcpy(packet_firing_array, &address[next],
                n_neurons * sizeof(packet_firing_data_t));
        next += n_words_needed(n_neurons * sizeof(packet_firing_data_t));
    }

    if (sizeof(synapse_param_t)) {
        spin1_memcpy(neuron_synapse_shaping_params, &address[next],
                n_neurons * sizeof(synapse_param_t));
        next += n_words_needed(n_neurons * sizeof(synapse_param_t));
    }

    if (sizeof(additional_input_t)) {
        spin1_memcpy(additional_input_array, &address[next],
                n_neurons * sizeof(additional_input_t));
        next += n_words_needed(n_neurons * sizeof(additional_input_t));
    }

    neuron_model_set_global_neuron_params(global_parameters);

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
        uint32_t timer_count, UNUSED uint32_t time, uint32_t n_neurons) {

    for (uint32_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {
        // Get the neuron itself
        neuron_t *this_neuron = &neuron_array[neuron_index];

        // Get the input_type parameters and voltage for this neuron
        input_type_t *input_types = &input_type_array[neuron_index];

        // Get threshold and additional input parameters for this neuron
        packet_firing_data_t *the_packet_firing =
            &packet_firing_array[neuron_index];
        additional_input_t *additional_inputs =
                &additional_input_array[neuron_index];
        synapse_param_t *the_synapse_type =
                &neuron_synapse_shaping_params[neuron_index];

        // Store whether the neuron has spiked
        bool will_fire = false;

        // Loop however many times requested; do this in reverse for efficiency,
        // and because the index doesn't actually matter
        for (uint32_t i = n_steps_per_timestep; i > 0; i--) {
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

            // Call functions to convert exc_input and inh_input to current
            input_type_convert_excitatory_input_to_current(
                    exc_input_values, input_types, soma_voltage);
            input_type_convert_inhibitory_input_to_current(
                    inh_input_values, input_types, soma_voltage);

            uint32_t external_bias = additional_input_get_input_value_as_current(
                    additional_inputs, soma_voltage);

            // update neuron parameters
            state_t result = neuron_model_state_update(
                    NUM_EXCITATORY_RECEPTORS, exc_input_values,
                    NUM_INHIBITORY_RECEPTORS, inh_input_values,
                    external_bias, this_neuron);

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

                    log_debug("Sending key=0x%08x payload=0x%08x",
                            the_packet_firing->key, payload);

                    tdma_processing_send_packet(
                        the_packet_firing->key, payload,
                        WITH_PAYLOAD, timer_count);
                } else {
                    log_debug("Sending key=0x%08x", the_packet_firing->key);

                    tdma_processing_send_packet(
                        the_packet_firing->key, 0,
                        NO_PAYLOAD, timer_count);
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

    if (sizeof(global_neuron_params_t)) {
        spin1_memcpy(&address[next], global_parameters,
                sizeof(global_neuron_params_t));
        next += n_words_needed(sizeof(global_neuron_params_t));
    }

    if (sizeof(neuron_t)) {
        spin1_memcpy(&address[next], neuron_array,
                n_neurons * sizeof(neuron_t));
        next += n_words_needed(n_neurons * sizeof(neuron_t));
    }

    if (sizeof(input_type_t)) {
        spin1_memcpy(&address[next], input_type_array,
                n_neurons * sizeof(input_type_t));
        next += n_words_needed(n_neurons * sizeof(input_type_t));
    }

    if (sizeof(packet_firing_data_t)) {
        spin1_memcpy(&address[next], packet_firing_array,
                n_neurons * sizeof(packet_firing_data_t));
        next += n_words_needed(n_neurons * sizeof(packet_firing_data_t));
    }

    if (sizeof(synapse_param_t)) {
        spin1_memcpy(&address[next], neuron_synapse_shaping_params,
                n_neurons * sizeof(synapse_param_t));
        next += n_words_needed(n_neurons * sizeof(synapse_param_t));
    }

    if (sizeof(additional_input_t)) {
        spin1_memcpy(&address[next], additional_input_array,
                n_neurons * sizeof(additional_input_t));
        next += n_words_needed(n_neurons * sizeof(additional_input_t));
    }
}

#if LOG_LEVEL >= LOG_DEBUG
SOMETIMES_UNUSED // Marked unused as only used sometimes
//! \brief Print the inputs to the neurons
//! \param[in] n_neurons: The number of neurons
void neuron_impl_print_inputs(uint32_t n_neurons) {
    bool empty = true;
    for (index_t i = 0; i < n_neurons; i++) {
        synapse_param_t *params = &neuron_synapse_shaping_params[i];
        input_t exc_values[NUM_EXCITATORY_RECEPTORS];
        input_t inh_values[NUM_INHIBITORY_RECEPTORS];
        empty = empty && (0 == bitsk(
                synapse_types_get_excitatory_input(exc_values, params)
                - synapse_types_get_inhibitory_input(inh_values, params)));
    }

    if (!empty) {
        for (index_t i = 0; i < n_neurons; i++) {
            synapse_param_t *params = &neuron_synapse_shaping_params[i];
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
        synapse_types_print_parameters(&neuron_synapse_shaping_params[n]);
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
