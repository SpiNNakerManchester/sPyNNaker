/*! \file
 *
 * \brief implementation of the neuron.h interface.
 *
 */

#include "neuron.h"
#include "models/neuron_model.h"
#include "synapse_types/synapse_types.h"
#include "plasticity/synapse_dynamics.h"
#include "../common/out_spikes.h"
#include "../common/recording.h"
#include <debug.h>
#include <string.h>

//! Array of neuron states
static neuron_pointer_t neuron_array;

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
    has_key, transmission_key, number_of_neurons_to_simulate,
    num_neuron_parameters, start_of_global_parameters,
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

    // Check if theres a key to use
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
    n_neurons = address[number_of_neurons_to_simulate];
    *n_neurons_value = n_neurons;
    uint32_t n_params = address[num_neuron_parameters];

    // Read the global parameter details
    if (sizeof(global_neuron_params_t) > 0) {
        global_parameters = (global_neuron_params_t *) spin1_malloc(
            sizeof(global_neuron_params_t));
        if (global_parameters == NULL) {
            log_error("Unable to allocate global neuron parameters"
                      "- Out of DTCM");
            return false;
        }
        memcpy(global_parameters, &address[start_of_global_parameters],
               sizeof(global_neuron_params_t));
    }

    log_info("\tneurons = %u, params = %u", n_neurons, n_params);

    // Allocate DTCM for new format neuron array and copy block of data
    neuron_array = (neuron_t*) spin1_malloc(n_neurons * sizeof(neuron_t));
    if (neuron_array == NULL) {
        log_error("Unable to allocate neuron array - Out of DTCM");
        return false;
    }
    memcpy(neuron_array,
            &address[start_of_global_parameters +
                     (sizeof(global_neuron_params_t) / 4)],
            n_neurons * sizeof(neuron_t));

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
        neuron_pointer_t neuron = &neuron_array[neuron_index];

        // Get excitatory and inhibitory input from synapses
        // **NOTE** this may be in either conductance or current units
        input_t exc_neuron_input = neuron_model_convert_input(
            synapse_types_get_excitatory_input(input_buffers, neuron_index));
        input_t inh_neuron_input = neuron_model_convert_input(
            synapse_types_get_inhibitory_input(input_buffers, neuron_index));

        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
            synapse_dynamics_get_intrinsic_bias(time, neuron_index);

        // update neuron parameters (will inform us if the neuron should spike)
        bool spike = neuron_model_state_update(
            exc_neuron_input, inh_neuron_input, external_bias, neuron);

        // If we should be recording potential, record this neuron parameter
        if (recording_is_channel_enabled(recording_flags,
                e_recording_channel_neuron_potential)) {
            state_t voltage = neuron_model_get_membrane_voltage(neuron);
            recording_record(e_recording_channel_neuron_potential, &voltage,
                             sizeof(state_t));
        }

        // If we should be recording gsyn, get the neuron input
        if (recording_is_channel_enabled(recording_flags,
                e_recording_channel_neuron_gsyn)) {
            input_t temp_record_input = exc_neuron_input - inh_neuron_input;
            recording_record(e_recording_channel_neuron_gsyn,
                             &temp_record_input, sizeof(input_t));
        }

        // If the neuron has spiked
        if (spike) {
            log_debug("the neuron %d has been determined to spike",
                      neuron_index);
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
