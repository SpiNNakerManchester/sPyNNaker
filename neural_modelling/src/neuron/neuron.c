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
static neuron_pointer_t neuron_array = NULL;

//! The key to be used for this core (will be ORed with neuron id)
static key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
static bool use_key;

//! If firing rate of pre-synaptic neuron is too slow relative to
//! post-synaptic neuron post-synaptic event history event history can
//! overflow - if neuron hasn't fired for this long, it sends a 'flush'
//! spike to allow downstream plastic synapses connected to it to update
static uint32_t flush_time;

//! The number of neurons on the core
static uint32_t num_neurons;

//! The recording flags
uint32_t recording_flags;

//! The input buffers
static input_t *input_buffers = NULL;

//! Per-neuron counter used to trigger flushing
static uint16_t *time_since_last_spike = NULL;

//! parameters that reside in the neuron_parameter_data_region in human
//! readable form
typedef enum neuron_region_params {
    e_use_key,
    e_key,
    e_num_neurons,
    e_flush_time,
    e_sim_time_step_us,
    e_params_start,
} neuron_region_params;


//! private method for doing output debug data on the neurons
//! \return nothing
static inline void _print_neurons() {
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print(&(neuron_array[n]));
    }
    log_debug("-------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! \translate the data stored in the NEURON_PARAMS data region in SDRAM and
//! converts it into c based objects for use.
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[in] recording_flags_param the recordings parameters
//!            (contains which regions are active and how big they are)
//! \param[out] num_neurons_value The number of neurons this model is to emulate
//! \return boolean which is True is the translation was successful
//! otherwise False
bool neuron_initialise(address_t address, uint32_t recording_flags_param,
        uint32_t *num_neurons_value) {
    log_info("neuron_initialise: starting");

    // Check if theres a key to use
    use_key = address[e_use_key];

    // Read the spike key to use
    key = address[e_key];

    // output if this model is expecting to transmit
    if (!use_key){
        log_info("\tThis model is not expecting to transmit as it has no key");
    }
    else{
        log_info("\tThis model is expected to transmit with key = %08x", key);
    }

    // Read the neuron details
    num_neurons = address[e_num_neurons];
    flush_time = address[e_flush_time];
    *num_neurons_value = num_neurons;
    timer_t sim_time_step_us = address[e_sim_time_step_us];

    log_info("\tneurons = %u, simulations time step = %uus, flush time = %u",
             num_neurons, sim_time_step_us, flush_time);

    // If a flush time is specified
    if(flush_time != UINT32_MAX)
    {
        // Allocate counter for each neuron
        time_since_last_spike = (uint16_t*)spin1_malloc(num_neurons * sizeof(uint16_t));

        if (time_since_last_spike == NULL) {
            log_error("Unable to allocate time since last spike array - Out of DTCM");
            return false;
        }
        // Zero counters
        memset(time_since_last_spike, 0, num_neurons * sizeof(uint16_t));
    }

    // Allocate DTCM for new format neuron array and copy block of data
    neuron_array = (neuron_t*) spin1_malloc(num_neurons * sizeof(neuron_t));
    if (neuron_array == NULL) {
        log_error("Unable to allocate neuron array - Out of DTCM");
        return false;
    }
    memcpy(neuron_array, &address[e_params_start],
           num_neurons * sizeof(neuron_t));

    // Set up the out spikes array
    if (!out_spikes_initialize(num_neurons)) {
        return false;
    }

    // Pass time step to neuron model
    neuron_model_set_machine_timestep(sim_time_step_us);

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
    for (index_t n = 0; n < num_neurons; n++) {
        neuron_pointer_t neuron = &neuron_array[n];

        // Get excitatory and inhibitory input from synapses
        // **NOTE** this may be in either conductance or current units
        input_t exc_neuron_input = neuron_model_convert_input(
            synapse_types_get_excitatory_input(input_buffers, n));
        input_t inh_neuron_input = neuron_model_convert_input(
            synapse_types_get_inhibitory_input(input_buffers, n));

        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
            synapse_dynamics_get_intrinsic_bias(time, n);
        
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
        /*if (recording_is_channel_enabled(recording_flags,
                e_recording_channel_neuron_gsyn)) {
            //input_t temp_record_input = neuron->I_Ca2;
            input_t temp_record_input = exc_neuron_input - inh_neuron_input;
            recording_record(e_recording_channel_neuron_gsyn,
                             &temp_record_input, sizeof(input_t));
        }*/

        // If flushing is enabled
        bool flush = false;
        if(time_since_last_spike != NULL)
        {
            // If neuron's spiked, reset time since last spike
            if(spike)
            {
                time_since_last_spike[n] = 0;
            }
            // Otherwise
            else
            {
                // Increment time since last spike
                time_since_last_spike[n]++;

                // If flush time has elapsed, set flag and clear timer
                if(time_since_last_spike[n] > flush_time)
                {
                  flush = true;
                  time_since_last_spike[n] = 0;
                }
            }
        }

        // If the neuron has spiked or a flush is required
        if (spike || flush) {
            // Build source key
            key_t neuron_key = key | n;

            if(spike)
            {
                log_debug("neuron %u spiked", n);

                // Do any required synapse processing
                synapse_dynamics_process_post_synaptic_event(time, n);

                // Record the spike
                out_spikes_set_spike(n);
            }
            else
            {
                log_debug("neuron %u flushing", n);

                // Set flush bit in key
                neuron_key |= FLUSH_BIT;
            }

            // If this neuron actually transmits, do so!
            if(use_key)
            {
                while (!spin1_send_mc_packet(neuron_key, 0, NO_PAYLOAD)) {
                    spin1_delay_us(1);
                }
            }
        }
    }

    // do logging stuff if required
    out_spikes_print();
    _print_neurons();

    // Record any spikes this timestep
    out_spikes_record(recording_flags);
    out_spikes_reset();
}
