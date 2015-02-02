/* neuron.c
 *
 * Dave Lester, Yuri , Abigail...
 *
 *  CREATION DATE
 *    1 August, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 1 August 2013
 *    Version          : $Revision: 1.1 $
 *    Last modified on : $Date: 2013/08/06 15:55:57 $
 *    Last modified by : $Author: dave $
 *    $Id: neuron.c,v 1.1 2013/08/06 15:55:57 dave Exp dave $
 *
 *    $Log$
 *
 *
 */

#include "neuron.h"
#include "models/neuron_model.h"
#include "synapse_types/synapse_types.h"
#include "plasticity/synapse_dynamics.h"
#include "../common/out_spikes.h"
#include "../common/recording.h"
#include "../common/key_conversion.h"
#include <debug.h>
#include <string.h>

// Array of neuron states
static neuron_pointer_t neuron_array;

// The key to be used for this core (will be ORed with neuron id)
static key_t key;

// The number of neurons on the core
static uint32_t n_neurons;

// The recording flags
static uint32_t recording_flags;

// The input buffers - from synapses.c
static input_t *input_buffers;

static inline void _print_neurons() {
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print(&(neuron_array[n]));
    }
    log_debug("-------------------------------------\n");
    //}
#endif // LOG_LEVEL >= LOG_DEBUG
}

bool neuron_initialise(address_t address, uint32_t recording_flags_param,
        uint32_t *n_neurons_value) {
    log_info("neuron_initialise: starting");

    // Read the spike key to use
    key = address[0];
    log_info("\tkey = %08x, (x: %u, y: %u) proc: %u", key, key_x(key),
             key_y(key), key_p(key));

    // Read the neuron details
    n_neurons = address[1];
    *n_neurons_value = n_neurons;
    uint32_t n_params = address[2];
    timer_t timestep = address[3];

    log_info("\tneurons = %u, params = %u, time step = %u", n_neurons,
             n_params, timestep);

    // Allocate DTCM for new format neuron array and copy block of data
    neuron_array = (neuron_t*) spin1_malloc(n_neurons * sizeof(neuron_t));
    if (neuron_array == NULL) {
        log_error("Unable to allocate neuron array - Out of DTCM");
        return false;
    }
    memcpy(neuron_array, &address[4], n_neurons * sizeof(neuron_t));

    // Set up the out spikes array
    if (!out_spikes_initialize(n_neurons)) {
        return false;
    }

    // Set up the neuron model
    neuron_model_set_machine_timestep(timestep);

    recording_flags = recording_flags_param;

    return true;
}

void neuron_set_input_buffers(input_t *input_buffers_value) {
    input_buffers = input_buffers_value;
}

void neuron_do_timestep_update(timer_t time) {
    use(time);
    _print_neurons();

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
            synapse_dynamics_get_intrinsic_bias(neuron_index);

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

            // Do any required synapse processing
            synapse_dynamics_process_post_synaptic_event(time, neuron_index);

            // Record the spike
            out_spikes_set_spike(neuron_index);

            // Send the spike
            while (!spin1_send_mc_packet(key | neuron_index, 0, NO_PAYLOAD)) {
                spin1_delay_us(1);
            }
        }
    }

    // Record any spikes this timestep
    out_spikes_record(recording_flags);
    out_spikes_reset();
}
