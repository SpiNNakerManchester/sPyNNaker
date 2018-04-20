/*! \file
 *
 * \brief implementation of the neuron.h interface.
 *
 */

#include "neuron.h"
#include "implementations/neuron_impl.h"
#include <debug.h>
#include <string.h>

// declare spin1_wfi
//void spin1_wfi();

//! The key to be used for this core (will be ORed with neuron id)
static key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
static bool use_key;

//! The number of neurons on the core
static uint32_t n_neurons;

//! The recording flags
static uint32_t recording_flags;

//! The number of clock ticks to back off before starting the timer, in an
//! attempt to avoid overloading the network
static uint32_t random_backoff;

//! The number of clock ticks between sending each spike
static uint32_t time_between_spikes;

//! The expected current clock tick of timer_1 when the next spike can be sent
static uint32_t expected_time;

//! parameters that reside in the neuron_parameter_data_region in human
//! readable form
typedef enum parameters_in_neuron_parameter_data_region {
    RANDOM_BACKOFF, TIME_BETWEEN_SPIKES, HAS_KEY, TRANSMISSION_KEY,
    N_NEURONS_TO_SIMULATE, INCOMING_SPIKE_BUFFER_SIZE,
    START_OF_GLOBAL_PARAMETERS,
} parameters_in_neuron_parameter_data_region;


//! private method for doing output debug data on the neurons
static inline void _print_neuron_state_variables() {

//! only if the models are compiled in debug mode will this method contain
//! said lines
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
    	neuron_impl_print_state_variables(n);
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
    	neuron_impl_print_parameters(n);
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

    // call the neuron implementation functions to do the work
    neuron_impl_load_neuron_parameters(address, next, n_neurons);
    neuron_impl_set_global_neuron_parameters();

    return true;
}

//! \brief interface for reloading neuron parameters as needed
//! \param[in] address: the address where the neuron parameters are stored
//! in SDRAM
//! \return bool which is true if the reload of the neuron parameters was
//! successful or not
bool neuron_reload_neuron_parameters(address_t address){
    log_debug("neuron_reloading_neuron_parameters: starting");
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
    log_debug("neuron_initialise: starting");

    random_backoff = address[RANDOM_BACKOFF];
    time_between_spikes = address[TIME_BETWEEN_SPIKES] * sv->cpu_clk;
    log_debug(
        "\t back off = %u, time between spikes %u",
        random_backoff, time_between_spikes);

    // Check if there is a key to use
    use_key = address[HAS_KEY];

    // Read the spike key to use
    key = address[TRANSMISSION_KEY];

    // output if this model is expecting to transmit
    if (!use_key){
        log_debug("\tThis model is not expecting to transmit as it has no key");
    } else{
        log_debug("\tThis model is expected to transmit with key = %08x", key);
    }

    // Read the neuron details
    n_neurons = address[N_NEURONS_TO_SIMULATE];  // is this still going to be here?
    *n_neurons_value = n_neurons;

    // Read the size of the incoming spike buffer to use
    *incoming_spike_buffer_size = address[INCOMING_SPIKE_BUFFER_SIZE];

    log_debug("\t n_neurons = %u, spike buffer size = %u", n_neurons,
            *incoming_spike_buffer_size);

    // Call the neuron implementation initialise function to setup DTCM etc.
    if (!neuron_impl_initialise(n_neurons)) {
    	return false;
    }

    // load the data into the allocated DTCM spaces.
    if (!_neuron_load_neuron_parameters(address)){
        return false;
    }

    neuron_impl_reset_record_counter();
    recording_flags = recording_flags_param;

    // Set up the out spikes array
   // size_t spike_size = neuron_impl_spike_size(n_neurons);

    if (!out_spikes_initialize(neuron_impl_spike_size(n_neurons))) {
        return false;
    }

    neuron_impl_initialise_recording(n_neurons);

    _print_neuron_parameters();

    return true;
}

//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
void neuron_store_neuron_parameters(address_t address){

    uint32_t next = START_OF_GLOBAL_PARAMETERS;

    // call neuron implementation function to do the work
    neuron_impl_store_neuron_parameters(address, next, n_neurons);
}

//! \setter for the internal input buffers
//! \param[in] input_buffers_value the new input buffers
void neuron_set_neuron_synapse_shaping_params(
        synapse_param_t *neuron_synapse_shaping_params_value) {
	neuron_impl_set_neuron_synapse_shaping_params(
			neuron_synapse_shaping_params_value);
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

    // Reset the out spikes before starting if at beginning of recording
    neuron_impl_wait_for_recordings_and_reset_out_spikes();

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

    	// call the implementation function (boolean for spike)
    	bool spike = neuron_impl_do_timestep_update(time, neuron_index);

        // If the neuron has spiked
        if (spike) {
            log_debug("neuron %u spiked at time %u", neuron_index, time);

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

    // now call the neuron implementation function to do required recording
    neuron_impl_do_recording(time); //, recording_flags);

    // do logging stuff if required
    out_spikes_print();
    _print_neuron_state_variables();

    // order seems to be important for some reason
    neuron_impl_record_spikes(time);

    // Re-enable interrupts
    spin1_mode_restore(cpsr);
}
