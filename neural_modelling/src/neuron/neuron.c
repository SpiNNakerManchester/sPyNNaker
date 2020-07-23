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
#include "plasticity/synapse_dynamics.h"
#include <debug.h>
#include <utils.h>

//! The key to be used for this core (will be ORed with neuron ID)
static key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
static bool use_key;

//! The number of neurons on the core
static uint32_t n_neurons;

//! The number of clock ticks between sending each spike
static uint32_t time_between_spikes;

//! The number of clock ticks between core index's
static uint32_t time_between_cores;

//! The next change in the time between spikes
static uint32_t core_slot;

//! The expected current clock tick of timer_1 when the next spike can be sent
static uint32_t expected_time;

//! the initial offset
static uint32_t initial_offset;

//! n times the core got behind its tdma
static uint32_t n_behind_times = 0;

//! The recording flags
static uint32_t recording_flags = 0;

//!
static uint32_t phase;

//! parameters that reside in the neuron_parameter_data_region
struct neuron_parameters {
    uint32_t core_slot;
    uint32_t time_between_spikes;
    uint32_t time_between_cores;
    uint32_t initial_offset;
    uint32_t has_key;
    uint32_t transmission_key;
    uint32_t n_neurons_to_simulate;
    uint32_t n_synapse_types;
    uint32_t incoming_spike_buffer_size;
};

//! Offset of start of global parameters, in words.
#define START_OF_GLOBAL_PARAMETERS \
    (sizeof(struct neuron_parameters) / sizeof(uint32_t))

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

bool neuron_initialise(address_t address, address_t recording_address, // EXPORTED
        uint32_t *n_neurons_value, uint32_t *n_synapse_types_value,
        uint32_t *incoming_spike_buffer_size) {
    log_debug("neuron_initialise: starting");
    struct neuron_parameters *params = (void *) address;

    time_between_spikes = params->time_between_spikes * sv->cpu_clk;
    time_between_cores = params->time_between_cores * sv->cpu_clk;
    core_slot = params->core_slot;
    initial_offset = params->initial_offset * sv->cpu_clk;
    log_info("\t time between spikes %u", time_between_spikes);
    log_info("\t time between core index's %u", time_between_cores);
    log_info("\t core slot %u", core_slot);
    log_info("\t initial offset %u", initial_offset);

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

    log_info(
        "\t n_neurons = %u, spike buffer size = %u",
        n_neurons, *incoming_spike_buffer_size);

    // Call the neuron implementation initialise function to setup DTCM etc.
    if (!neuron_impl_initialise(n_neurons)) {
        return false;
    }

    // load the data into the allocated DTCM spaces.
    if (!neuron_load_neuron_parameters(address)) {
        return false;
    }

    // setup recording region
    if (!neuron_recording_initialise(
            recording_address, &recording_flags, n_neurons)) {
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

    if (n_behind_times > 0) {
        log_error("core fell behind its tdma slot %d times", n_behind_times);
    }

    // call neuron implementation function to do the work
    neuron_impl_store_neuron_parameters(
            address, START_OF_GLOBAL_PARAMETERS, n_neurons);
}

//! \brief internal method for sending a spike with the TDMA tie in
//! \param[in] neuron_index: the neuron index.
//! \param[in] phase: the current phase this vertex thinks its in.
static inline void neuron_tdma_spike_processing(
        index_t neuron_index, uint timer_period, uint timer_count) {
    // Spin1 API ticks - to know when the timer wraps
    extern uint ticks;

    // if we're too early. select the next index to where we are and wait
    if (neuron_index > phase) {
        int tc1_count = tc[T1_COUNT];
        int how_much_time_has_passed = (sv->cpu_clk * timer_period) - tc1_count;
        //log_info("neuron index %d and phase %d", neuron_index, phase);
        //log_info("how much time has passed is %u", how_much_time_has_passed);
        bool found_phase_id = false;
        while (!found_phase_id) {
            int time_when_phase_started = time_between_spikes * phase;
            //log_info(
            //    "time_when_phase_started = %d for phase %d",
            //    time_when_phase_started, phase);

            int time_when_phase_slot_started =
                time_when_phase_started + initial_offset +
                (time_between_cores * core_slot);
            //log_info(
            //    "time_when_phase_slot_started = %d", time_when_phase_slot_started);

            if (time_when_phase_slot_started < how_much_time_has_passed) {
                log_debug("up phase id");
                phase += 1;
            }
            else{
                found_phase_id = true;
                log_debug("phase id %d", phase);
            }
            if (phase > n_neurons) {
                log_info(
                    "missed the whole TDMA. go NOW! for neuron %d on tick %d",
                    neuron_index, ticks);
                while (!spin1_send_mc_packet(
                        key | neuron_index, 0, NO_PAYLOAD)) {
                    spin1_delay_us(1);
                }
                return;
            }
        }
    }

    // Set the next expected time to wait for between spike sending
    expected_time = (
        (sv->cpu_clk * timer_period) -
        ((phase * time_between_spikes) + (time_between_cores * core_slot) +
         initial_offset));

    // Wait until the expected time to send
    int counter = 0;
    while ((ticks == timer_count) && (tc[T1_COUNT] > expected_time)) {
        counter +=1;
        // Do Nothing
    }
    if (counter == 0) {
        n_behind_times += 1;
    }

    // Send the spike
    while (!spin1_send_mc_packet(key | neuron_index, 0, NO_PAYLOAD)) {
        spin1_delay_us(1);
    }

    phase += 1;
}

void neuron_do_timestep_update( // EXPORTED
        timer_t time, uint timer_count, uint timer_period) {

    // the phase in this timer tick im in (not tied to neuron index)
    phase = 0;

    // Prepare recording for the next timestep
    neuron_recording_setup_for_next_recording();

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
                synapse_dynamics_get_intrinsic_bias(time, neuron_index);

        // call the implementation function (boolean for spike)
        bool spike = neuron_impl_do_timestep_update(neuron_index, external_bias);

        // If the neuron has spiked
        if (spike) {
            log_debug("neuron %u spiked at time %u", neuron_index, time);

            // Do any required synapse processing
            synapse_dynamics_process_post_synaptic_event(time, neuron_index);

            if (use_key) {
                 neuron_tdma_spike_processing(
                     neuron_index, timer_period, timer_count);
            }
        } else {
            log_debug("the neuron %d has been determined to not spike",
                      neuron_index);
         }
    }

    //log_info("time left of the timer after tdma is %d", tc[T1_COUNT]);

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
