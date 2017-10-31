/*! \file
 *
 * \brief implementation of the neuron.h interface.
 *
 */

#include "neuron.h"
#include "models/neuron_model.h"
#include "input_types/input_type.h"
#include "additional_inputs/additional_input.h"
#include "threshold_types/threshold_type.h"
#include "synapse_types/synapse_types.h"
#include "plasticity/synapse_dynamics.h"
#include "../common/out_spikes.h"
#include "recording.h"
#include <debug.h>
#include <string.h>

// declare spin1_wfi
void spin1_wfi();

#define SPIKE_RECORDING_CHANNEL 0
#define V_RECORDING_CHANNEL 1
#define GSYN_EXCITATORY_RECORDING_CHANNEL 2
#define GSYN_INHIBITORY_RECORDING_CHANNEL 3

//! Array of neuron states
static neuron_pointer_t neuron_array;

//! Input states array
static input_type_pointer_t input_type_array;

//! Additional input array
static additional_input_pointer_t additional_input_array;

//! Threshold states array
static threshold_type_pointer_t threshold_type_array;

//! Global parameters for the neurons
static global_neuron_params_pointer_t global_parameters;

//! The key to be used for this core (will be ORed with neuron id)
static key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
static bool use_key;

//! The number of neurons on the core
static uint32_t n_neurons;

//! The recording flags
static uint32_t recording_flags;

// The synapse shaping parameters
static synapse_param_t *neuron_synapse_shaping_params;

//! storage for neuron state with timestamp
static timed_state_t *voltages;
uint32_t voltages_size;

//! storage for neuron input with timestamp
static timed_input_t *inputs_excitatory;
static timed_input_t *inputs_inhibitory;
uint32_t input_size;

//! The number of clock ticks to back off before starting the timer, in an
//! attempt to avoid overloading the network
static uint32_t random_backoff;

//! The number of clock ticks between sending each spike
static uint32_t time_between_spikes;

//! The expected current clock tick of timer_1 when the next spike can be sent
static uint32_t expected_time;

//! The number of recordings outstanding
static uint32_t n_recordings_outstanding = 0;

//! parameters that reside in the neuron_parameter_data_region in human
//! readable form
typedef enum parmeters_in_neuron_parameter_data_region {
    RANDOM_BACKOFF, TIME_BETWEEN_SPIKES, HAS_KEY, TRANSMISSION_KEY,
    N_NEURONS_TO_SIMULATE, INCOMING_SPIKE_BUFFER_SIZE,
    START_OF_GLOBAL_PARAMETERS,
} parmeters_in_neuron_parameter_data_region;


//! private method for doing output debug data on the neurons
static inline void _print_neurons() {

//! only if the models are compiled in debug mode will this method contain
//! said lines.
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_state_variables(&(neuron_array[n]));
    }
    log_debug("-------------------------------------\n");
    //}
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! private method for doing output debug data on the neurons
static inline void _print_neuron_parameters() {

//! only if the models are compiled in debug mode will this method contain
//! said lines.
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&(neuron_array[n]));
    }
    log_debug("-------------------------------------\n");
    //}
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! \brief does the memory copy for the neuron parameters
//! \param[in] address: the address where the neuron parameters are stored
//! in SDRAM
//! \return bool which is true if the mem copy's worked, false otherwise
bool _neuron_load_neuron_parameters(address_t address){
    uint32_t next = START_OF_GLOBAL_PARAMETERS;

    log_info("loading neuron global parameters");
    memcpy(global_parameters, &address[next], sizeof(global_neuron_params_t));
    next += sizeof(global_neuron_params_t) / 4;

    log_info("loading neuron local parameters");
    memcpy(neuron_array, &address[next], n_neurons * sizeof(neuron_t));
    next += (n_neurons * sizeof(neuron_t)) / 4;

    log_info("loading input type parameters");
    memcpy(input_type_array, &address[next], n_neurons * sizeof(input_type_t));
    next += (n_neurons * sizeof(input_type_t)) / 4;

    log_info("loading additional input type parameters");
    memcpy(additional_input_array, &address[next],
           n_neurons * sizeof(additional_input_t));
    next += (n_neurons * sizeof(additional_input_t)) / 4;

    log_info("loading threshold type parameters");
    memcpy(threshold_type_array, &address[next],
           n_neurons * sizeof(threshold_type_t));

    neuron_model_set_global_neuron_params(global_parameters);

    return true;
}

//! \brief interface for reloading neuron parameters as needed
//! \param[in] address: the address where the neuron parameters are stored
//! in SDRAM
//! \return bool which is true if the reload of the neuron parameters was
//! successful or not
bool neuron_reload_neuron_parameters(address_t address){
    log_info("neuron_reloading_neuron_parameters: starting");
    if (!_neuron_load_neuron_parameters(address)){
        return false;
    }

    // for debug purposes, print the neuron parameters
    _print_neuron_parameters();
    return true;
}

//! \brief Set up the neuron models
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[in] recording_flags_param the recordings parameters
//!            (contains which regions are active and how big they are)
//! \param[out] n_neurons_value The number of neurons this model is to emulate
//! \return True is the initialisation was successful, otherwise False
bool neuron_initialise(address_t address, uint32_t recording_flags_param,
        uint32_t *n_neurons_value, uint32_t *incoming_spike_buffer_size) {
    log_info("neuron_initialise: starting");

    random_backoff = address[RANDOM_BACKOFF];
    time_between_spikes = address[TIME_BETWEEN_SPIKES] * sv->cpu_clk;
    log_info(
        "\t back off = %u, time between spikes %u",
        random_backoff, time_between_spikes);

    // Check if there is a key to use
    use_key = address[HAS_KEY];

    // Read the spike key to use
    key = address[TRANSMISSION_KEY];

    // output if this model is expecting to transmit
    if (!use_key){
        log_info("\tThis model is not expecting to transmit as it has no key");
    }
    else{
        log_info("\tThis model is expected to transmit with key = %08x", key);
    }

    // Read the neuron details
    n_neurons = address[N_NEURONS_TO_SIMULATE];
    *n_neurons_value = n_neurons;

    // Read the size of the incoming spike buffer to use
    *incoming_spike_buffer_size = address[INCOMING_SPIKE_BUFFER_SIZE];

    // log message for debug purposes
    log_info(
        "\t neurons = %u, spike buffer size = %u, params size = %u,"
        "input type size = %u, threshold size = %u", n_neurons,
        *incoming_spike_buffer_size, sizeof(neuron_t),
        sizeof(input_type_t), sizeof(threshold_type_t));

    // allocate DTCM for the global parameter details
    if (sizeof(global_neuron_params_t) > 0) {
        global_parameters = (global_neuron_params_t *) spin1_malloc(
            sizeof(global_neuron_params_t));
        if (global_parameters == NULL) {
            log_error("Unable to allocate global neuron parameters"
                      "- Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for neuron array
    if (sizeof(neuron_t) != 0) {
        neuron_array = (neuron_t *) spin1_malloc(n_neurons * sizeof(neuron_t));
        if (neuron_array == NULL) {
            log_error("Unable to allocate neuron array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for input type array and copy block of data
    if (sizeof(input_type_t) != 0) {
        input_type_array = (input_type_t *) spin1_malloc(
            n_neurons * sizeof(input_type_t));
        if (input_type_array == NULL) {
            log_error("Unable to allocate input type array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for additional input array and copy block of data
    if (sizeof(additional_input_t) != 0) {
        additional_input_array = (additional_input_pointer_t) spin1_malloc(
            n_neurons * sizeof(additional_input_t));
        if (additional_input_array == NULL) {
            log_error("Unable to allocate additional input array"
                      " - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for threshold type array and copy block of data
    if (sizeof(threshold_type_t) != 0) {
        threshold_type_array = (threshold_type_t *) spin1_malloc(
            n_neurons * sizeof(threshold_type_t));
        if (threshold_type_array == NULL) {
            log_error("Unable to allocate threshold type array - Out of DTCM");
            return false;
        }
    }

    // load the data into the allocated DTCM spaces.
    if (!_neuron_load_neuron_parameters(address)){
        return false;
    }

    // Set up the out spikes array
    if (!out_spikes_initialize(n_neurons)) {
        return false;
    }

    recording_flags = recording_flags_param;

    voltages_size = sizeof(uint32_t) + sizeof(state_t) * n_neurons;
    voltages = (timed_state_t *) spin1_malloc(voltages_size);
    input_size = sizeof(uint32_t) + sizeof(input_struct_t) * n_neurons;
    inputs_excitatory = (timed_input_t *) spin1_malloc(input_size);
    inputs_inhibitory = (timed_input_t *) spin1_malloc(input_size);

    _print_neuron_parameters();

    // Initialise pointers to Neuron parameters in STDP code
    synapse_dynamics_stdp_mad_set_neuron_array(neuron_array);
    log_info("set pointer to neuron array in stdp code");

    synapse_dynamics_stdp_mad_set_additional_input_array(additional_input_array);
    log_info("set pointer to additional input array in stdp code");

    synapse_dynamics_stdp_mad_set_threshold_array(threshold_type_array);
    log_info("set pointer to threshold type array in stdp code");

    return true;
}

//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
void neuron_store_neuron_parameters(address_t address){

    uint32_t next = START_OF_GLOBAL_PARAMETERS;


    log_info("writing neuron global parameters");
    memcpy(&address[next], global_parameters, sizeof(global_neuron_params_t));
    next += sizeof(global_neuron_params_t) / 4;

    log_info("writing neuron local parameters");
    memcpy(&address[next], neuron_array, n_neurons * sizeof(neuron_t));
    next += (n_neurons * sizeof(neuron_t)) / 4;

    log_info("writing input type parameters");
    memcpy(&address[next], input_type_array, n_neurons * sizeof(input_type_t));
    next += (n_neurons * sizeof(input_type_t)) / 4;

    log_info("writing additional input type parameters");
    memcpy(&address[next], additional_input_array,
           n_neurons * sizeof(additional_input_t));
    next += (n_neurons * sizeof(additional_input_t)) / 4;

    log_info("writing threshold type parameters");
    memcpy(&address[next], threshold_type_array,
           n_neurons * sizeof(threshold_type_t));
}

//! \setter for the internal input buffers
//! \param[in] input_buffers_value the new input buffers
void neuron_set_neuron_synapse_shaping_params(
        synapse_param_t *neuron_synapse_shaping_params_value) {
    neuron_synapse_shaping_params = neuron_synapse_shaping_params_value;
}

void recording_done_callback() {
    n_recordings_outstanding -= 1;
}

//! \executes all the updates to neural parameters when a given timer period
//! has occurred.
//! \param[in] time the timer tick  value currently being executed
void neuron_do_timestep_update(timer_t time) {

    // Wait a random number of clock cycles
    uint32_t random_backoff_time = tc[T1_COUNT] - random_backoff;
    while (tc[T1_COUNT] > random_backoff_time) {

        // Do Nothing
    }

    // Set the next expected time to wait for between spike sending
    expected_time = tc[T1_COUNT] - time_between_spikes;

    // Wait until recordings have completed, to ensure the recording space
    // can be re-written
    while (n_recordings_outstanding > 0) {
        spin1_wfi();
    }

    // Reset the out spikes before starting
    out_spikes_reset();

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

        // Get the parameters for this neuron
        neuron_pointer_t neuron = &neuron_array[neuron_index];
        input_type_pointer_t input_type = &input_type_array[neuron_index];
        threshold_type_pointer_t threshold_type =
            &threshold_type_array[neuron_index];
        additional_input_pointer_t additional_input =
            &additional_input_array[neuron_index];
        state_t voltage = neuron_model_get_membrane_voltage(neuron);

        // If we should be recording potential, record this neuron parameter
        voltages->states[neuron_index] = voltage;

        // Get excitatory and inhibitory input from synapses and convert it
        // to current input
        input_t exc_input_value = input_type_get_input_value(
            synapse_types_get_excitatory_input(
                &(neuron_synapse_shaping_params[neuron_index])),
            input_type);
        input_t inh_input_value = input_type_get_input_value(
            synapse_types_get_inhibitory_input(
                &(neuron_synapse_shaping_params[neuron_index])),
            input_type);
        input_t exc_input = input_type_convert_excitatory_input_to_current(
            exc_input_value, input_type, voltage);
        input_t inh_input = input_type_convert_inhibitory_input_to_current(
            inh_input_value, input_type, voltage);

        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
            synapse_dynamics_get_intrinsic_bias(time, neuron_index) +
            additional_input_get_input_value_as_current(
                additional_input, voltage);

        // If we should be recording input, record the values
        inputs_excitatory->inputs[neuron_index].input = exc_input_value;
        inputs_inhibitory->inputs[neuron_index].input = inh_input_value;

        // update neuron parameters
        state_t result = neuron_model_state_update(
            exc_input, inh_input, external_bias, neuron);

        // determine if a spike should occur
        bool spike = threshold_type_is_above_threshold(result, threshold_type);

        // If the neuron has spiked
        if (spike) {
            log_debug("neuron %u spiked at time %u", neuron_index, time);

            // Tell the neuron model
            neuron_model_has_spiked(neuron);

            // Tell the additional input
            additional_input_has_spiked(additional_input);

            // Do any required synapse processing
            synapse_dynamics_process_post_synaptic_event(time, neuron_index);

            // Record the spike
            out_spikes_set_spike(neuron_index);

            if (use_key) {

                // Wait until the expected time to send
                while (tc[T1_COUNT] > expected_time) {

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

    // record neuron state (membrane potential) if needed
    if (recording_is_channel_enabled(recording_flags, V_RECORDING_CHANNEL)) {
        n_recordings_outstanding += 1;
        voltages->time = time;
        recording_record_and_notify(
            V_RECORDING_CHANNEL, voltages, voltages_size,
            recording_done_callback);
    }

    // record neuron inputs (excitatory) if needed
    if (recording_is_channel_enabled(
            recording_flags, GSYN_EXCITATORY_RECORDING_CHANNEL)) {
        n_recordings_outstanding += 1;
        inputs_excitatory->time = time;
        recording_record_and_notify(
            GSYN_EXCITATORY_RECORDING_CHANNEL, inputs_excitatory, input_size,
            recording_done_callback);
    }

    // record neuron inputs (inhibitory) if needed
    if (recording_is_channel_enabled(
            recording_flags, GSYN_INHIBITORY_RECORDING_CHANNEL)) {
        n_recordings_outstanding += 1;
        inputs_inhibitory->time = time;
        recording_record_and_notify(
            GSYN_INHIBITORY_RECORDING_CHANNEL, inputs_inhibitory, input_size,
            recording_done_callback);
    }

    // do logging stuff if required
    out_spikes_print();
    _print_neurons();

    // Record any spikes this timestep
    if (recording_is_channel_enabled(
            recording_flags, SPIKE_RECORDING_CHANNEL)) {
        if (!out_spikes_is_empty()) {
            n_recordings_outstanding += 1;
            out_spikes_record(
                SPIKE_RECORDING_CHANNEL, time, recording_done_callback);
        }
    }

    // Re-enable interrupts
    spin1_mode_restore(cpsr);
}
