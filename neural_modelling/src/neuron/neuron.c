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
 * \brief implementation of the neuron.h interface.
 */

#include "neuron.h"
#include "neuron_recording.h"
#include "implementations/neuron_impl.h"
#include "current_sources/current_source.h"
#include "plasticity/synapse_dynamics.h"
#include <debug.h>

//! The key to be used for this core (will be ORed with neuron ID)
key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
bool use_key;

//! Latest time in a timestep that any neuron has sent a spike
uint32_t latest_send_time = 0xFFFFFFFF;

//! Earliest time in a timestep that any neuron has sent a spike
uint32_t earliest_send_time = 0;

//! The number of neurons on the core
static uint32_t n_neurons;

//! The closest power of 2 >= n_neurons
static uint32_t n_neurons_peak;

//! The number of synapse types
static uint32_t n_synapse_types;

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
    uint32_t transmission_key;
    uint32_t n_neurons_to_simulate;
    uint32_t n_neurons_peak;
    uint32_t n_synapse_types;
    uint32_t ring_buffer_shifts[];
};

//! \brief does the memory copy for the neuron parameters
//! \param[in] time: the current time step
//! \return true if the memory copies worked, false otherwise
static bool neuron_load_neuron_parameters(uint32_t time) {
    log_debug("loading parameters");
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

    log_debug("neuron_reloading_neuron_parameters: starting");
    return neuron_load_neuron_parameters(time);
}

bool neuron_initialise(
        void *core_params_address, void *neuron_params_address,
        void *current_sources_address, void *recording_address,
        void *initial_values_address, uint32_t *n_rec_regions_used) {
    log_debug("neuron_initialise: starting");

    // Read the neuron parameters
    struct neuron_core_parameters *params = core_params_address;

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
    n_neurons_peak = params->n_neurons_peak;
    n_synapse_types = params->n_synapse_types;

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
