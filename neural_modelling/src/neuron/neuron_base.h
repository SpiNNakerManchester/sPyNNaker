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

/*! \file
 *
 * \brief implementation of the neuron.h interface.
 *
 */

#include "neuron.h"
#include "neuron_recording.h"
#include "implementations/neuron_impl_base_api.h"
#include "plasticity/synapse_dynamics.h"
#include <debug.h>

// Spin1 API ticks - to know when the timer wraps
extern uint ticks;

#define SPIKE_RECORDING_CHANNEL 0

//! The key to be used for this core (will be ORed with neuron ID)
static key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
static bool use_key;

//! The number of neurons on the core
static uint32_t n_neurons;

//! The number of clock ticks between sending each spike
static uint32_t time_between_spikes;

//! The expected current clock tick of timer_1 when the next spike can be sent
static uint32_t expected_time;

//! parameters that reside in the neuron_parameter_data_region
struct neuron_parameters {
    uint32_t timer_start_offset;
    uint32_t time_between_spikes;
    uint32_t has_key;
    uint32_t transmission_key;
    uint32_t n_neurons_to_simulate;
    uint32_t n_synapse_types;
    uint32_t incoming_spike_buffer_size;
};

#define START_OF_GLOBAL_PARAMETERS \
    (sizeof(struct neuron_parameters) / sizeof(uint32_t))

//! \brief does the memory copy for the neuron parameters
//! \param[in] address: the address where the neuron parameters are stored
//! in SDRAM
//! \return bool which is true if the mem copy's worked, false otherwise
static bool neuron_load_neuron_parameters(address_t address) {
    log_debug("loading parameters");
    // call the neuron implementation functions to do the work
    neuron_impl_load_neuron_parameters(
        address, START_OF_GLOBAL_PARAMETERS, n_neurons);
    return true;
}

bool neuron_reload_neuron_parameters(address_t address) { // EXPORTED
    log_debug("neuron_reloading_neuron_parameters: starting");
    return neuron_load_neuron_parameters(address);
}

//! \brief Set up the neuron models
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[in] recording_flags_param the recordings parameters
//!            (contains which regions are active and how big they are)
//! \param[out] n_neurons_value The number of neurons this model is to emulate
//! \return True is the initialisation was successful, otherwise False
bool neuron_initialise(address_t address, uint32_t *n_neurons_value, // EXPORTED
        uint32_t *n_synapse_types_value, uint32_t *incoming_spike_buffer_size,
        uint32_t *timer_offset) {
    log_debug("neuron_initialise: starting");
    struct neuron_parameters *params = (void *) address;

    *timer_offset = params->timer_start_offset;
    time_between_spikes = params->time_between_spikes * sv->cpu_clk;
    log_debug("\t back off = %u, time between spikes %u",
            *timer_offset, time_between_spikes);

    // Check if there is a key to use
    use_key = params->has_key;

    // Read the spike key to use
    key = params->transmission_key;

    // output if this model is expecting to transmit
    if (!use_key) {
        log_debug("\tThis model is not expecting to transmit as it has no key");
    } else {
        log_debug("\tThis model is expected to transmit with key = %08x", key);
    }

    // Read the neuron details
    n_neurons = params->n_neurons_to_simulate;
    *n_neurons_value = n_neurons;
    *n_synapse_types_value = params->n_synapse_types;

    // Read the size of the incoming spike buffer to use
    *incoming_spike_buffer_size = params->incoming_spike_buffer_size;

    log_debug("\t n_neurons = %u, spike buffer size = %u", n_neurons,
            *incoming_spike_buffer_size);

    // Call the neuron implementation initialise function to setup DTCM etc.
    if (!neuron_impl_initialise(n_neurons)) {
        return false;
    }

    // load the data into the allocated DTCM spaces.
    if (!neuron_load_neuron_parameters(address)) {
        return false;
    }

    return true;
}

//! \brief stores neuron parameter back into SDRAM
//! \param[in] address: the address in SDRAM to start the store
void neuron_store_neuron_parameters(address_t address) { // EXPORTED
    // call neuron implementation function to do the work
    neuron_impl_store_neuron_parameters(
        address, START_OF_GLOBAL_PARAMETERS, n_neurons);
}

void neuron_add_inputs( // EXPORTED
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    neuron_impl_add_inputs(
            synapse_type_index, neuron_index, weights_this_timestep);
}

#if LOG_LEVEL >= LOG_DEBUG
void neuron_print_inputs(void) { // EXPORTED
	neuron_impl_print_inputs(n_neurons);
}

void neuron_print_synapse_parameters(void) { // EXPORTED
	neuron_impl_print_synapse_parameters(n_neurons);
}

const char *neuron_get_synapse_type_char(uint32_t synapse_type) { // EXPORTED
	return neuron_impl_get_synapse_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG
