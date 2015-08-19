/*! \file
 *
 * \brief implementation of the neuron.h interface.
 *
 */

#include "neuron.h"
#include "models/neuron_model.h"
#include "input_types/input_type.h"
#include "threshold_types/threshold_type.h"
#include "synapse_types/synapse_types.h"
#include "plasticity/synapse_dynamics.h"
#include "../common/out_spikes.h"
#include "../common/recording.h"
#include <debug.h>
#include <string.h>

//! Array of neuron states
static neuron_pointer_t neuron_array;

//! Input states array
static input_type_pointer_t input_type_array;

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

//! The input buffers - from synapses.c
static input_t *input_buffers;

//! parameters that reside in the neuron_parameter_data_region in human
//! readable form
typedef enum parmeters_in_neuron_parameter_data_region {
    has_key, transmission_key, n_neurons_to_simulate,
    start_of_global_parameters,
} parmeters_in_neuron_parameter_data_region;


//! private method for doing output debug data on the neurons
//! \return nothing
static inline void _print_neurons() {
//! only if the models are compiled in debug mode will this method contain
//! said lines.
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print(&(neuron_array[n]));
    }
    log_debug("-------------------------------------\n");
    //}
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! \translate the data stored in the NEURON_PARAMS data region in SDRAM and
//! converts it into c based objects for use.
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[in] recording_flags_param the recordings parameters
//!            (contains which regions are active and how big they are)
//! \param[out] n_neurons_value The number of neurons this model is to emulate
//! \return boolean which is True is the translation was successful
//! otherwise False
bool neuron_initialise(address_t address, uint32_t recording_flags_param,
        uint32_t *n_neurons_value) {
    log_info("neuron_initialise: starting");

    // Check if there is a key to use
    use_key = address[has_key];

    // Read the spike key to use
    key = address[transmission_key];

    // output if this model is expecting to transmit
    if (!use_key){
        log_info("\tThis model is not expecting to transmit as it has no key");
    }
    else{
        log_info("\tThis model is expected to transmit with key = %08x", key);
    }

    // Read the neuron details
    n_neurons = address[n_neurons_to_simulate];
    *n_neurons_value = n_neurons;

    uint32_t next = start_of_global_parameters;

    // Read the global parameter details
    if (sizeof(global_neuron_params_t) > 0) {
        global_parameters = (global_neuron_params_t *) spin1_malloc(
            sizeof(global_neuron_params_t));
        if (global_parameters == NULL) {
            log_error("Unable to allocate global neuron parameters"
                      "- Out of DTCM");
            return false;
        }
        memcpy(global_parameters, &address[next],
               sizeof(global_neuron_params_t));
        next += sizeof(global_neuron_params_t) / 4;
    }

    log_info("\tneurons = %u", n_neurons);

    // Allocate DTCM for neuron array and copy block of data
    neuron_array = (neuron_t *) spin1_malloc(n_neurons * sizeof(neuron_t));
    if (neuron_array == NULL) {
        log_error("Unable to allocate neuron array - Out of DTCM");
        return false;
    }
    memcpy(neuron_array, &address[next], n_neurons * sizeof(neuron_t));
    next += (n_neurons * sizeof(neuron_t)) / 4;

    // Allocate DTCM for input type array and copy block of data
    input_type_array = (input_type_t *) spin1_malloc(
        n_neurons * sizeof(input_type_t));
    if (input_type_array == NULL) {
        log_error("Unable to allocate input type array - Out of DTCM");
        return false;
    }
    memcpy(input_type_array, &address[next], n_neurons * sizeof(input_type_t));
    next += (n_neurons * sizeof(input_type_t)) / 4;

    // Allocate DTCM for threshold type array and copy block of data
    threshold_type_array = (threshold_type_t *) spin1_malloc(
        n_neurons * sizeof(threshold_type_t));
    if (threshold_type_array == NULL) {
        log_error("Unable to allocate threshold type array - Out of DTCM");
        return false;
    }
    memcpy(threshold_type_array, &address[next],
           n_neurons * sizeof(threshold_type_t));

    // Set up the out spikes array
    if (!out_spikes_initialize(n_neurons)) {
        return false;
    }

    // Set up the neuron model
    neuron_model_set_global_neuron_params(global_parameters);

    recording_flags = recording_flags_param;

    return true;
}

//! \setter for the internal input buffers
//! \param[in] input_buffers_value the new input buffers
//! \return None this method does not return anything.
void neuron_set_input_buffers(input_t *input_buffers_value) {
    input_buffers = input_buffers_value;
}

//! \executes all the updates to neural parameters when a given timer period
//! has occurred.
//! \param[in] time the timer tic  value currently being executed
//! \return nothing
void neuron_do_timestep_update(timer_t time) {
    use(time);

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

        // Get the parameters for this neuron
        neuron_pointer_t neuron = &neuron_array[neuron_index];
        input_type_pointer_t input_type = &input_type_array[neuron_index];
        threshold_type_pointer_t threshold_type =
            &threshold_type_array[neuron_index];
        state_t voltage = neuron_model_get_membrane_voltage(neuron);

        // If we should be recording potential, record this neuron parameter
        if (recording_is_channel_enabled(recording_flags,
                e_recording_channel_neuron_potential)) {
            recording_record(e_recording_channel_neuron_potential, &voltage,
                             sizeof(state_t));
        }

        // Get excitatory and inhibitory input from synapses and convert it
        // to current input
        input_t exc_input_value = input_type_get_input_value(
            synapse_types_get_excitatory_input(input_buffers, neuron_index),
            input_type);
        input_t inh_input_value = input_type_get_input_value(
            synapse_types_get_inhibitory_input(input_buffers, neuron_index),
            input_type);
        input_t exc_input = input_type_convert_excitatory_input_to_current(
            exc_input_value, input_type, voltage);
        input_t inh_input = input_type_convert_inhibitory_input_to_current(
            inh_input_value, input_type, voltage);

        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
            synapse_dynamics_get_intrinsic_bias(time, neuron_index);

        // If we should be recording input, record the values
        if (recording_is_channel_enabled(recording_flags,
                e_recording_channel_neuron_gsyn)) {
            recording_record(e_recording_channel_neuron_gsyn,
                             &exc_input_value, sizeof(input_t));
            recording_record(e_recording_channel_neuron_gsyn,
                             &inh_input_value, sizeof(input_t));
        }

        // update neuron parameters
        state_t result = neuron_model_state_update(
            exc_input, inh_input, external_bias, neuron);

        // determine if a spike should occur
        bool spike = threshold_type_is_above_threshold(result, threshold_type);

        // If the neuron has spiked
        if (spike) {
            log_debug("the neuron %d has been determined to spike",
                      neuron_index);

            // Tell the neuron model
            neuron_model_has_spiked(neuron);

            // Do any required synapse processing
            synapse_dynamics_process_post_synaptic_event(time, neuron_index);

            // Record the spike
            out_spikes_set_spike(neuron_index);

            // Send the spike
            while (use_key &&
                   !spin1_send_mc_packet(key | neuron_index, 0, NO_PAYLOAD)) {
                spin1_delay_us(1);
            }
        } else {
            log_debug("the neuron %d has been determined to not spike",
                      neuron_index);
        }
    }

    // do logging stuff if required
    out_spikes_print();
    _print_neurons();

    // Record any spikes this timestep
    out_spikes_record(recording_flags);
    out_spikes_reset();
}
