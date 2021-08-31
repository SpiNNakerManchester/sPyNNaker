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
#include "synapse/plasticity/synapse_dynamics.h"
#include <common/out_spikes.h>
#include <debug.h>
#include <simulation.h>

// declare spin1_wfi
extern void spin1_wfi(void);

// Spin1 API ticks - to know when the timer wraps
extern uint ticks;

#define SPIKE_RECORDING_CHANNEL 0
#define DMA_TAG_READ_SYNAPTIC_CONTRIBUTION 1

//! The key to be used for this core (will be ORed with neuron ID)
static key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
static bool use_key;

//! The number of neurons on the core
static uint32_t n_neurons;

static uint32_t n_synapse_types;

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

//! The synaptic contributions for the current timestep
static REAL *synaptic_contributions;

static uint32_t *synaptic_contributions_to_input_left_shifts;

static uint32_t synapse_type_index_bits;
static uint32_t synapse_index_bits;

static uint32_t memory_index;

static timer_t current_time;

static uint32_t n_neurons_power_2;

//! Size of DMA read for synaptic contributions
static size_t dma_size;

static volatile bool dma_finished;

static REAL *synaptic_region;

//! Array containing the offsets for each syn type for the contributions
static uint32_t *contribution_offset;

static uint32_t *incoming_partitions;

static uint32_t start_of_global_parameters;

//! parameters that reside in the neuron_parameter_data_region
struct neuron_parameters {
    uint32_t timer_start_offset;
    uint32_t time_between_spikes;
    uint32_t has_key;
    uint32_t transmission_key;
    uint32_t n_neurons_to_simulate;
    uint32_t n_synapse_types;
    uint32_t mem_index;
    uint32_t n_recorded_variables;
};
// The +4 is for the seeds for the background noise
#define INCOMING_PARTITIONS_PTR \
    ((sizeof(struct neuron_parameters) / sizeof(uint32_t)) + 4)

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

    uint32_t next = start_of_global_parameters;

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

void dma_done_callback(uint arg1, uint arg2) {

    use(arg1);
    use(arg2);

    dma_finished = true;
}

//! \brief Set up the neuron models
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[in] recording_flags_param the recordings parameters
//!            (contains which regions are active and how big they are)
//! \param[out] n_neurons_value The number of neurons this model is to emulate
//! \return True is the initialisation was successful, otherwise False
bool neuron_initialise(address_t address, uint32_t *timer_offset) {

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
    n_synapse_types = params->n_synapse_types;

    start_of_global_parameters = INCOMING_PARTITIONS_PTR + n_synapse_types;

    memory_index = params->mem_index;

    // Read number of recorded variables
    n_recorded_vars = params->n_recorded_variables;

     // Avoids offset problems with a single neuron assuming min power = 2
    n_neurons_power_2 = (n_neurons == 1) ? 2 : n_neurons;
    uint32_t log_n_neurons = 1;
    if (n_neurons != 1) {
        if (!is_power_of_2(n_neurons)) {
            n_neurons_power_2 = next_power_of_2(n_neurons);
        }
        log_n_neurons = ilog_2(n_neurons_power_2);
    }

    uint32_t n_synapse_types_power_2 = n_synapse_types;
    if (!is_power_of_2(n_synapse_types)) {
        n_synapse_types_power_2 = next_power_of_2(n_synapse_types);
    }
    uint32_t log_n_synapse_types = ilog_2(n_synapse_types_power_2);

    synapse_type_index_bits = log_n_neurons + log_n_synapse_types;
    synapse_index_bits = log_n_neurons;

    incoming_partitions = (uint32_t *) spin1_malloc(n_synapse_types * sizeof(uint32_t));
    if (incoming_partitions == NULL) {
        log_error("Could not allocate space for incoming_partitions");
        return false;
    }

    contribution_offset = (uint32_t *) spin1_malloc(n_synapse_types * sizeof(uint32_t));

    uint8_t total_partitions = 0;
    
    for (index_t i = 0; i < n_synapse_types; i++) {

        contribution_offset[i] = total_partitions * n_neurons_power_2;

        incoming_partitions[i] =
            *(address + INCOMING_PARTITIONS_PTR + i);

        if(incoming_partitions[i] == 0) {
            // Should be a very rare case, ensures we don't break
            // the memory offset for syn cores and keeps max efficiency
            total_partitions++;
        }
        else {
            total_partitions += incoming_partitions[i];
        }
    }

    uint32_t incoming_partitions_power_2 = total_partitions;
    if (!is_power_of_2(total_partitions)) {
        incoming_partitions_power_2 = next_power_of_2(total_partitions);
    }
    uint32_t log_incoming_partitions = ilog_2(incoming_partitions_power_2);

    uint32_t contribution_bits =
        log_n_neurons + log_incoming_partitions;
    uint32_t contribution_size = 1 << contribution_bits;

    dma_size = contribution_size * sizeof(REAL);

    dma_finished = false;


    //Allocate the region in SDRAM for synaptic contribution. Size is dma_size.
    //Flag = 1 allocates with lock in order to avoid multiple accesses
    synaptic_region = (REAL *) sark_xalloc(sv->sdram_heap, dma_size, memory_index, 1);

    //set the region to 0 (necessary for the first timestep and for syn cores that never receive spikes)
    for(index_t i = 0; i < contribution_size; i++) {
        synaptic_region[i] = 0.0k;
    }

    // Call the neuron implementation initialise function to setup DTCM etc.
    if (!neuron_impl_initialise(n_neurons)) {
        return false;
    }

    // Tag the postsynaptic region with memory_index+18. Still a unique id and saves space in DTCM
    // Memory_index is the core ID, +18 guarantees not to replicate a tag with another core ID
    neuron_impl_allocate_postsynaptic_region(memory_index+18, n_neurons);

    neuron_impl_set_background_noise_params(address + INCOMING_PARTITIONS_PTR - 4, n_neurons);

    // Allocate space for the synaptic contribution buffer
    synaptic_contributions = (REAL *) spin1_malloc(dma_size);
    if (synaptic_contributions == NULL) {
        log_error("Unable to allocate Synaptic contribution buffers");
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

    simulation_dma_transfer_done_callback_on(
        DMA_TAG_READ_SYNAPTIC_CONTRIBUTION, dma_done_callback);

    return true;
}

//! \brief stores neuron parameter back into SDRAM
//! \param[in] address: the address in SDRAM to start the store
void neuron_store_neuron_parameters(address_t address) { // EXPORTED
    uint32_t next = start_of_global_parameters;

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
    
    current_time = time;

    spin1_dma_transfer (
        DMA_TAG_READ_SYNAPTIC_CONTRIBUTION, synaptic_region,
        synaptic_contributions, DMA_READ, dma_size);
    
    while (!dma_finished);

    dma_finished = false;

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

    register REAL sum;

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {
        
        for (index_t synapse_type_index = 0; synapse_type_index < n_synapse_types; synapse_type_index++) {

            register uint32_t buff_index = contribution_offset[synapse_type_index] + neuron_index;

            //Add the values from synaptic_contributions
            sum = 0;

            for (index_t i = 0; i < incoming_partitions[synapse_type_index]; i++) {

                sum = sat_accum_sum(sum, synaptic_contributions[buff_index]);
                buff_index += n_neurons_power_2;

            }

            //MAKE IT INLINE?
            neuron_impl_add_inputs(synapse_type_index, neuron_index, sum);
        }    
        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
                synapse_dynamics_get_intrinsic_bias(time, neuron_index);

        // call the implementation function (boolean for spike)
        // MAKE IT INLINE
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

            // Record the spike (or rate update)
            out_spikes_set_spike(spike_recording_indexes[neuron_index]);

            // Do any required synapse processing
            neuron_impl_process_post_synaptic_event(neuron_index);

              //io_printf(IO_BUF, "ur %k, vr %k, t %d\n", neuron_impl_post_syn_urate(neuron_index), neuron_impl_post_syn_vrate(neuron_index), time);

            if(use_key){
                // Send the spike
                while (!spin1_send_mc_packet(
                    key | neuron_index, neuron_impl_get_v(neuron_index), WITH_PAYLOAD)) {
                    spin1_delay_us(1);
                }
            }
//            }
        } else {
            log_debug("the neuron %d has been determined to not spike",
                    neuron_index);
        }
    }

    // Start the DMA with the postsynaptic contributions for the syn cores
    neuron_impl_send_postsynaptic_buffer(n_neurons);

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
