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
#include "current_sources/current_source_impl.h"
#include "plasticity/synapse_dynamics.h"
#include <debug.h>
#include <tdma_processing.h>

//! The key to be used for this core (will be ORed with neuron ID)
static key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
static bool use_key;

//! The number of neurons on the core
static uint32_t n_neurons;

//! The recording flags
static uint32_t recording_flags = 0;

//! parameters that reside in the neuron_parameter_data_region
struct neuron_parameters {
    uint32_t has_key;
    uint32_t transmission_key;
    uint32_t n_neurons_to_simulate;
    uint32_t n_synapse_types;
    uint32_t incoming_spike_buffer_size;
};

//! Offset of start of global parameters, in words.
#define START_OF_GLOBAL_PARAMETERS \
    ((sizeof(struct neuron_parameters) + \
      sizeof(struct tdma_parameters)) / sizeof(uint32_t))

//! \brief does the memory copy for the neuron parameters
//! \param[in] address: the address where the neuron parameters are stored
//!     in SDRAM
//! \return bool which is true if the mem copy's worked, false otherwise
static bool neuron_load_neuron_parameters(address_t address) {
    log_debug("loading parameters");
    // call the neuron implementation functions to do the work
    neuron_impl_load_neuron_parameters(
        address, START_OF_GLOBAL_PARAMETERS, n_neurons);
    return true;
}

bool neuron_resume(address_t address) { // EXPORTED
    if (!neuron_recording_reset(n_neurons)){
        log_error("failed to reload the neuron recording parameters");
        return false;
    }

    log_debug("neuron_reloading_neuron_parameters: starting");
    return neuron_load_neuron_parameters(address);
}

bool neuron_initialise(
        address_t address, address_t cs_address, address_t recording_address, // EXPORTED
        uint32_t *n_neurons_value, uint32_t *n_synapse_types_value,
        uint32_t *incoming_spike_buffer_size, uint32_t *n_rec_regions_used) {
    log_debug("neuron_initialise: starting");

    // init the TDMA
    void *data_addr = address;
    tdma_processing_initialise(&data_addr);

    // cast left over SDRAM into neuron struct.
    struct neuron_parameters *params = data_addr;

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

    // Initialise for current sources
    if (!current_source_impl_initialise(cs_address)) {
        return false;
    }

    // setup recording region
    if (!neuron_recording_initialise(
            recording_address, &recording_flags, n_neurons, n_rec_regions_used)) {
        return false;
    }

    return true;
}

void neuron_pause(address_t address) { // EXPORTED
    /* Finalise any recordings that are in progress, writing back the final
     * amounts of samples recorded to SDRAM */
    if (recording_flags > 0) {
        log_debug("updating recording regions");
        neuron_recording_finalise();
    }

    // call neuron implementation function to do the work
    neuron_impl_store_neuron_parameters(
            address, START_OF_GLOBAL_PARAMETERS, n_neurons);
}

void neuron_do_timestep_update(timer_t time, uint timer_count) { // EXPORTED

    // the phase in this timer tick im in (not tied to neuron index)
    tdma_processing_reset_phase();

    // Prepare recording for the next timestep
    neuron_recording_setup_for_next_recording();

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {
        // Get any input from an injected current source
        REAL current_offset = current_source_get_offset(time, neuron_index);

        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
                synapse_dynamics_get_intrinsic_bias(time, neuron_index);

        // call the implementation function (boolean for spike)
        bool spike = neuron_impl_do_timestep_update(
            neuron_index, external_bias, current_offset);

        // If the neuron has spiked
        if (spike) {
            log_debug("neuron %u spiked at time %u", neuron_index, time);

            // Do any required synapse processing
            synapse_dynamics_process_post_synaptic_event(time, neuron_index);

            if (use_key) {
                tdma_processing_send_packet(
                    (key | neuron_index), 0, NO_PAYLOAD, timer_count);
            }
        } else {
            log_debug("the neuron %d has been determined to not spike",
                      neuron_index);
         }
    }

    log_debug("time left of the timer after tdma is %d", tc[T1_COUNT]);

    // Disable interrupts to avoid possible concurrent access
    uint cpsr = spin1_int_disable();

    // Record the recorded variables
    neuron_recording_record(time);

    // Re-enable interrupts
    spin1_mode_restore(cpsr);
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
