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

/*! \file
 * \brief implementation of the neuron.h interface.
 */

#include "neuron.h"
#include "neuron_recording.h"
#include "implementations/neuron_impl.h"
#include "current_sources/current_source.h"
#include "plasticity/synapse_dynamics.h"
#include <debug.h>

//! The keys to be used by the neurons (one per neuron)
uint32_t *neuron_keys;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
bool use_key;

//! Latest time in a timestep that any neuron has sent a spike
uint32_t latest_send_time = 0xFFFFFFFF;

//! Earliest time in a timestep that any neuron has sent a spike
uint32_t earliest_send_time = 0;

//! The colour of the time step to handle delayed spikes
uint32_t colour = 0;

//! The number of neurons on the core
static uint32_t n_neurons;

//! The closest power of 2 >= n_neurons
static uint32_t n_neurons_peak;

//! The number of synapse types
static uint32_t n_synapse_types;

//! The mask of the colour
static uint32_t colour_mask;

//! Amount to left shift the ring buffer by to make it an input
static uint32_t *ring_buffer_to_input_left_shifts;

//! The address where the actual neuron parameters start
static void *saved_neuron_params_address;

//! The address for the current source parameters
static void *current_source_address;

//! The address to save initial values to
static void *saved_initial_values_address;

//! parameters that reside in the neuron_parameter_data_region
struct neuron_core_parameters {
    uint32_t has_key;
    uint32_t n_neurons_to_simulate;
    uint32_t n_neurons_peak;
    uint32_t n_colour_bits;
    uint32_t n_synapse_types;
    uint32_t ring_buffer_shifts[];
    // Following this struct in memory (as it can't be expressed in C) is:
    // uint32_t neuron_keys[n_neurons_to_simulate];
};

//! \brief does the memory copy for the neuron parameters
//! \param[in] time: the current time step
//! \return true if the memory copies worked, false otherwise
static bool neuron_load_neuron_parameters(uint32_t time) {
    address_t save_address = NULL;
    if (time == 0) {
    	save_address = saved_initial_values_address;
    }
    neuron_impl_load_neuron_parameters(saved_neuron_params_address, 0, n_neurons,
    		save_address);
    return true;
}

bool neuron_resume(uint32_t time) { // EXPORTED
    if (!neuron_recording_reset(n_neurons)){
        log_error("failed to reload the neuron recording parameters");
        return false;
    }

    // (re)load the current source parameters
    current_source_load_parameters(current_source_address);

    return neuron_load_neuron_parameters(time);
}

bool neuron_initialise(
        void *core_params_address, void *neuron_params_address,
        void *current_sources_address, void *recording_address,
        void *initial_values_address, uint32_t *n_rec_regions_used) {
    // Read the neuron parameters
    struct neuron_core_parameters *params = core_params_address;

    // Check if there is a key to use
    use_key = params->has_key;

    // Read the neuron details
    n_neurons = params->n_neurons_to_simulate;
    n_neurons_peak = params->n_neurons_peak;
    n_synapse_types = params->n_synapse_types;

    // Get colour details
    colour_mask = (1 << params->n_colour_bits) - 1;

    // Set up ring buffer left shifts
    uint32_t ring_buffer_bytes = n_synapse_types * sizeof(uint32_t);
    ring_buffer_to_input_left_shifts = spin1_malloc(ring_buffer_bytes);
    if (ring_buffer_to_input_left_shifts == NULL) {
        log_error("Not enough memory to allocate ring buffer");
        return false;
    }

    // read in ring buffer to input left shifts
    spin1_memcpy(
            ring_buffer_to_input_left_shifts, params->ring_buffer_shifts,
            ring_buffer_bytes);

    // The key list comes after the ring buffer shifts
    uint32_t *neuron_keys_sdram =
            (uint32_t *) &params->ring_buffer_shifts[n_synapse_types];
    uint32_t neuron_keys_size = n_neurons * sizeof(uint32_t);
    neuron_keys = spin1_malloc(neuron_keys_size);
    if (neuron_keys == NULL) {
        log_error("Not enough memory to allocate neuron keys");
        return false;
    }
    spin1_memcpy(neuron_keys, neuron_keys_sdram, neuron_keys_size);

    // Store where the actual neuron parameters start
    saved_neuron_params_address = neuron_params_address;
    current_source_address = current_sources_address;
    saved_initial_values_address = initial_values_address;

    log_info("\t n_neurons = %u, peak %u, n_synapse_types %u",
            n_neurons, n_neurons_peak, n_synapse_types);

    // Call the neuron implementation initialise function to setup DTCM etc.
    if (!neuron_impl_initialise(n_neurons)) {
        return false;
    }

    // load the neuron data into the allocated DTCM spaces.
    if (!neuron_load_neuron_parameters(0)) {
        return false;
    }

    // Initialise for current sources
    if (!current_source_initialise(current_sources_address, n_neurons)) {
        return false;
    }

    // load the current source data into the allocated DTCM spaces
    if (!current_source_load_parameters(current_sources_address)) {
        return false;
    }

    // setup recording region
    if (!neuron_recording_initialise(
            recording_address, n_neurons, n_rec_regions_used)) {
        return false;
    }

    return true;
}

void neuron_pause(void) { // EXPORTED

    // call neuron implementation function to do the work
    neuron_impl_store_neuron_parameters(saved_neuron_params_address, 0, n_neurons);
}

void neuron_do_timestep_update(timer_t time, uint timer_count) { // EXPORTED

    // Prepare recording for the next timestep
    neuron_recording_setup_for_next_recording();

    neuron_impl_do_timestep_update(timer_count, time, n_neurons);

    // Record the recorded variables
    neuron_recording_record(time);

    // Update the colour
    colour = (colour + 1) & colour_mask;
}

void neuron_transfer(weight_t *syns) { // EXPORTED
    uint32_t synapse_index = 0;
    uint32_t ring_buffer_index = 0;
    for (uint32_t s_i = n_synapse_types; s_i > 0; s_i--) {
        uint32_t rb_shift = ring_buffer_to_input_left_shifts[synapse_index];
        uint32_t neuron_index = 0;
        for (uint32_t n_i = n_neurons_peak; n_i > 0; n_i--) {
            weight_t value = syns[ring_buffer_index];
            if (value > 0) {
                if (neuron_index > n_neurons) {
                    log_error("Neuron index %u out of range", neuron_index);
                    rt_error(RTE_SWERR);
                }
                input_t val_to_add = synapse_row_convert_weight_to_input(
                        value, rb_shift);
                neuron_impl_add_inputs(synapse_index, neuron_index, val_to_add);
            }
            syns[ring_buffer_index] = 0;
            ring_buffer_index++;
            neuron_index++;
        }
        synapse_index++;
    }
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
