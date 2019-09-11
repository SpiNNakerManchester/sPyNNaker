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
#include "implementations/neuron_impl.h"
#include "plasticity/synapse_dynamics.h"
#include <common/out_spikes.h>
#include <debug.h>

// declare spin1_wfi
extern void spin1_wfi(void);

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

//! Number of timesteps between spike recordings
static uint32_t spike_recording_rate;

//! Number of neurons recording spikes
static uint32_t n_spike_recording_words;

//! Count of timesteps until next spike recording
static uint32_t spike_recording_count;

//! Increment of count until next spike recording
//! - 0 if not recorded, 1 if recorded
static uint32_t spike_recording_increment;

//! The index to record each spike to for each neuron
static uint8_t *spike_recording_indexes;

//! The number of variables that *can* be recorded - might not be enabled
static uint32_t n_recorded_vars;

//! The number of timesteps between each variable recording
static uint32_t *var_recording_rate;

//! Count of timesteps until next variable recording
static uint32_t *var_recording_count;

//! Increment of count until next variable recording
//! - 0 if not recorded, 1 if recorded
static uint32_t *var_recording_increment;

//! The index to record each variable to for each neuron
static uint8_t **var_recording_indexes;

//! The values of the recorded variables
static timed_state_t **var_recording_values;

//! The size of the recorded variables in bytes for a timestep
static uint32_t *var_recording_size;

//! The number of clock ticks between sending each spike
static uint32_t time_between_spikes;

//! The expected current clock tick of timer_1 when the next spike can be sent
static uint32_t expected_time;

//! The number of recordings outstanding
static uint32_t n_recordings_outstanding = 0;

//! parameters that reside in the neuron_parameter_data_region
struct neuron_parameters {
    uint32_t timer_start_offset;
    uint32_t time_between_spikes;
    uint32_t has_key;
    uint32_t transmission_key;
    uint32_t n_neurons_to_simulate;
    uint32_t n_synapse_types;
    uint32_t incoming_spike_buffer_size;
    uint32_t n_recorded_variables;
};
#define START_OF_GLOBAL_PARAMETERS \
    (sizeof(struct neuron_parameters) / sizeof(uint32_t))

static void reset_record_counter(void) {
    if (spike_recording_rate == 0) {
        // Setting increment to zero means spike_index will never equal
        // spike_rate
        spike_recording_increment = 0;
        // Index is not rate so does not record. Nor one so we never reset
        spike_recording_count = 2;
    } else {
        // Increase one each call so count gets to rate
        spike_recording_increment = 1;
        // Using rate here so that the zero time is recorded
        spike_recording_count = spike_recording_rate;
        // Reset as first pass we record no matter what the rate is
        out_spikes_reset();
    }
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        if (var_recording_rate[i] == 0) {
            // Setting increment to zero means count will never equal rate
            var_recording_increment[i] = 0;
            // Count is not rate so does not record
            var_recording_count[i] = 1;
        } else {
            // Increase one each call so count gets to rate
            var_recording_increment[i] = 1;
            // Using rate here so that the zero time is recorded
            var_recording_count[i] = var_recording_rate[i];
        }
    }
}

//! \brief does the memory copy for the neuron parameters
//! \param[in] address: the address where the neuron parameters are stored
//! in SDRAM
//! \return bool which is true if the mem copy's worked, false otherwise
static bool neuron_load_neuron_parameters(address_t address) {
    uint32_t next = START_OF_GLOBAL_PARAMETERS;

    log_debug("loading parameters");
    uint32_t n_words_for_n_neurons = (n_neurons + 3) >> 2;

    // Load spike recording details
    spike_recording_rate = address[next++];
    uint32_t n_neurons_recording_spikes = address[next++];
    n_spike_recording_words = get_bit_field_size(n_neurons_recording_spikes);
    spin1_memcpy(spike_recording_indexes, &address[next],
            n_neurons * sizeof(uint8_t));
    next += n_words_for_n_neurons;

    // Load other variable recording details
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        var_recording_rate[i] = address[next++];
        uint32_t n_neurons_recording_var = address[next++];
        var_recording_size[i] =
                (n_neurons_recording_var + 1) * sizeof(uint32_t);
        spin1_memcpy(var_recording_indexes[i], &address[next],
                n_neurons * sizeof(uint8_t));
        next += n_words_for_n_neurons;
    }

    // call the neuron implementation functions to do the work
    neuron_impl_load_neuron_parameters(address, next, n_neurons);
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

    // Read number of recorded variables
    n_recorded_vars = params->n_recorded_variables;

    log_debug("\t n_neurons = %u, spike buffer size = %u", n_neurons,
            *incoming_spike_buffer_size);

    // Call the neuron implementation initialise function to setup DTCM etc.
    if (!neuron_impl_initialise(n_neurons)) {
        return false;
    }

    // Set up the out spikes array - this is always n_neurons in size to ensure
    // it continues to work if changed between runs, but less might be used in
    // any individual run
    if (!out_spikes_initialize(n_neurons)) {
        return false;
    }

    // Allocate recording space
    spike_recording_indexes = spin1_malloc(n_neurons * sizeof(uint8_t));
    if (spike_recording_indexes == NULL) {
        log_error("Could not allocate space for spike_recording_indexes");
        return false;
    }
    var_recording_rate = spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_rate == NULL) {
        log_error("Could not allocate space for var_recording_rate");
        return false;
    }
    var_recording_count = spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_count == NULL) {
        log_error("Could not allocate space for var_recording_count");
        return false;
    }
    var_recording_increment = spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_increment == NULL) {
        log_error("Could not allocate space for var_recording_increment");
        return false;
    }
    var_recording_indexes = spin1_malloc(n_recorded_vars * sizeof(uint8_t *));
    if (var_recording_indexes == NULL) {
        log_error("Could not allocate space for var_recording_indexes");
        return false;
    }
    var_recording_size = spin1_malloc(n_recorded_vars * sizeof(uint32_t));
    if (var_recording_size == NULL) {
        log_error("Could not allocate space for var_recording_size");
        return false;
    }
    var_recording_values =
            spin1_malloc(n_recorded_vars * sizeof(timed_state_t *));
    if (var_recording_values == NULL) {
        log_error("Could not allocate space for var_recording_values");
        return false;
    }
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        var_recording_indexes[i] = spin1_malloc(n_neurons * sizeof(uint8_t));
        var_recording_values[i] = spin1_malloc(
                sizeof(uint32_t) + (sizeof(state_t) * n_neurons));
        if (var_recording_values[i] == NULL) {
            log_error("Could not allocate space for var_recording_values[%d]",
                    i);
            return false;
        }
    }

    // load the data into the allocated DTCM spaces.
    if (!neuron_load_neuron_parameters(address)) {
        return false;
    }

    reset_record_counter();

    return true;
}

//! \brief stores neuron parameter back into SDRAM
//! \param[in] address: the address in SDRAM to start the store
void neuron_store_neuron_parameters(address_t address) { // EXPORTED
    uint32_t next = START_OF_GLOBAL_PARAMETERS;

    uint32_t n_words_for_n_neurons = (n_neurons + 3) >> 2;
    next += (n_words_for_n_neurons + 2) * (n_recorded_vars + 1);

    // call neuron implementation function to do the work
    neuron_impl_store_neuron_parameters(address, next, n_neurons);
}

static void recording_done_callback(void) {
    n_recordings_outstanding--;
}

//! \executes all the updates to neural parameters when a given timer period
//! has occurred.
//! \param[in] time the timer tick  value currently being executed
void neuron_do_timestep_update( // EXPORTED
        timer_t time, uint timer_count, uint timer_period) {
    // Set the next expected time to wait for between spike sending
    expected_time = sv->cpu_clk * timer_period;

    // Wait until recordings have completed, to ensure the recording space
    // can be re-written
    while (n_recordings_outstanding > 0) {
        spin1_wfi();
    }

    // Reset the out spikes before starting if a beginning of recording
    if (spike_recording_count == 1) {
        out_spikes_reset();
    }

    // Set up an array for storing the recorded variable values
    state_t recorded_variable_values[n_recorded_vars];

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {
        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
                synapse_dynamics_get_intrinsic_bias(time, neuron_index);

        // call the implementation function (boolean for spike)
        bool spike = neuron_impl_do_timestep_update(
                neuron_index, external_bias, recorded_variable_values);

        // Write the recorded variable values
        for (uint32_t i = 0; i < n_recorded_vars; i++) {
            uint32_t index = var_recording_indexes[i][neuron_index];
            var_recording_values[i]->states[index] =
                    recorded_variable_values[i];
        }

        // If the neuron has spiked
        if (spike) {
            log_debug("neuron %u spiked at time %u", neuron_index, time);

            // Record the spike
            out_spikes_set_spike(spike_recording_indexes[neuron_index]);

            // Do any required synapse processing
            synapse_dynamics_process_post_synaptic_event(time, neuron_index);

            if (use_key) {
                // Wait until the expected time to send
                while ((ticks == timer_count) &&
                        (tc[T1_COUNT] > expected_time)) {
                    // Do Nothing
                }
                expected_time -= time_between_spikes;

                // Send the spike
                while (!spin1_send_mc_packet(
                        key | neuron_index, 0, NO_PAYLOAD)) {
                    spin1_delay_us(1);
                }
            }
        } else {
            log_debug("the neuron %d has been determined to not spike",
                    neuron_index);
        }
    }

    // Disable interrupts to avoid possible concurrent access
    uint cpsr = 0;
    cpsr = spin1_int_disable();

    // Record the recorded variables
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        if (var_recording_count[i] == var_recording_rate[i]) {
            var_recording_count[i] = 1;
            n_recordings_outstanding++;
            var_recording_values[i]->time = time;
            recording_record_and_notify(
                    i + 1, var_recording_values[i], var_recording_size[i],
                    recording_done_callback);
        } else {
            var_recording_count[i] += var_recording_increment[i];
        }
    }

    // Record any spikes this timestep
    if (spike_recording_count == spike_recording_rate) {
        spike_recording_count = 1;
        if (out_spikes_record(
                SPIKE_RECORDING_CHANNEL, time, n_spike_recording_words,
                recording_done_callback)) {
            n_recordings_outstanding++;
        }
    } else {
        spike_recording_count += spike_recording_increment;
    }

    // do logging stuff if required
    out_spikes_print();

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
