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
#include "structural_plasticity/synaptogenesis_dynamics.h"
#include "../common/out_spikes.h"
#include "recording.h"
#include "./profile_tags.h"
#include <debug.h>
#include <string.h>
#include <profiler.h>

// declare spin1_wfi
void spin1_wfi();

#define SPIKE_RECORDING_CHANNEL 0
#define V_RECORDING_CHANNEL 1
#define GSYN_EXCITATORY_RECORDING_CHANNEL 2
#define GSYN_INHIBITORY_RECORDING_CHANNEL 3

#ifndef NUM_EXCITATORY_RECEPTORS
#define NUM_EXCITATORY_RECEPTORS 1
#error NUM_EXCITATORY_RECEPTORS was undefined.  It should be defined by a synapse\
       shaping include
#endif

#ifndef NUM_INHIBITORY_RECEPTORS
#define NUM_INHIBITORY_RECEPTORS 1
#error NUM_INHIBITORY_RECEPTORS was undefined.  It should be defined by a synapse\
       shaping include
#endif

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

typedef struct global_record_params_t {
    uint32_t spike_rate;
    uint32_t v_rate;
    uint32_t exc_rate;
    uint32_t inh_rate;
    uint8_t spike_recording;
    uint8_t v_recording;
    uint8_t exc_recording;
    uint8_t inh_recording;

} global_record_params_t;

static global_record_params_t* global_record_params;

typedef struct indexes_t {
    uint8_t spike;
    uint8_t v;
    uint8_t exc;
    uint8_t inh;
} indexes_t;

static indexes_t* indexes_array;

uint32_t spike_index;
uint32_t spike_increment;
uint32_t v_index;
uint32_t v_increment;
uint32_t exc_index;
uint32_t exc_increment;
uint32_t inh_index;
uint32_t inh_increment;

//! storage for neuron state with timestamp
static timed_state_t *voltages;
uint32_t voltages_size;

//! storage for neuron input with timestamp
static timed_input_t *inputs_excitatory;
static timed_input_t *inputs_inhibitory;
uint32_t exc_size;
uint32_t inh_size;

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
//! said lines
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


void _reset_record_counter(){
    if (global_record_params->spike_rate == 0){
        // Setting increment to zero means v_index will never equal v_rate
        spike_increment = 0;
        // Index is not rate so does not record. Nor one so we never reset
        spike_index = 2;
    } else {
        // Increase one each call so z_index gets to v_rate
        spike_increment = 1;
        // Using rate base here first zero time is record
        spike_index = global_record_params->spike_rate;
        // Reset as first pass we record no matter what the rate is
        out_spikes_reset();
    }
    if (global_record_params->v_rate == 0){
        // Setting increment to zero means v_index will never equal v_rate
        v_increment = 0;
        // Index is not rate so does not record
        v_index = 1;

    } else {
        // Increase one each call so z_index gets to v_rate
        v_increment = 1;
        // Using rate base here first zero time is record
        v_index = global_record_params->v_rate;
    }

    if (global_record_params->exc_rate == 0){
        exc_increment = 0;
        exc_index = 1;
    } else {
        exc_increment = 1;
        exc_index = global_record_params->exc_rate;
    }
    if (global_record_params->inh_rate == 0){
        inh_increment = 0;
        inh_index = 1;
    } else {
        inh_increment = 1;
        inh_index = global_record_params->inh_rate;
    }

}

//! \brief does the memory copy for the neuron parameters
//! \param[in] address: the address where the neuron parameters are stored
//! in SDRAM
//! \return bool which is true if the mem copy's worked, false otherwise
bool _neuron_load_neuron_parameters(address_t address){
    uint32_t next = START_OF_GLOBAL_PARAMETERS;

    log_debug("loading parameters");
    //log_debug("loading global record parameters");
    memcpy(global_record_params, &address[next], sizeof(global_record_params_t));
    next += sizeof(global_record_params_t) / 4;

    //log_debug("loading indexes parameters");
    memcpy(indexes_array, &address[next], n_neurons * sizeof(indexes_t));
    next += (n_neurons * sizeof(indexes_t)) / 4;

    //for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {
    //    indexes_t indexes = &indexes_array[neuron_index];
    //    log_debug("neuron = %u, spike index = %u, v index = %u,"
    //        "exc index = %u, inh index = %u", neuron_index,
    //        indexes->spike, indexes->v,
    //        indexes->exc, indexes->inh);
    //}

    //log_debug("loading neuron global parameters");
    memcpy(global_parameters, &address[next], sizeof(global_neuron_params_t));
    next += sizeof(global_neuron_params_t) / 4;

    log_debug("loading neuron local parameters");
    memcpy(neuron_array, &address[next], n_neurons * sizeof(neuron_t));
    next += (n_neurons * sizeof(neuron_t)) / 4;

    log_debug("loading input type parameters");
    memcpy(input_type_array, &address[next], n_neurons * sizeof(input_type_t));
    next += (n_neurons * sizeof(input_type_t)) / 4;

    log_debug("loading additional input type parameters");
    memcpy(additional_input_array, &address[next],
           n_neurons * sizeof(additional_input_t));
    next += (n_neurons * sizeof(additional_input_t)) / 4;

    log_debug("loading threshold type parameters");
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
    n_neurons = address[N_NEURONS_TO_SIMULATE];
    *n_neurons_value = n_neurons;

    // Read the size of the incoming spike buffer to use
    *incoming_spike_buffer_size = address[INCOMING_SPIKE_BUFFER_SIZE];

    // log message for debug purposes
    log_debug(
        "\t neurons = %u, spike buffer size = %u, params size = %u,"
        "input type size = %u, threshold size = %u", n_neurons,
        *incoming_spike_buffer_size, sizeof(neuron_t),
        sizeof(input_type_t), sizeof(threshold_type_t));

    // allocate DTCM for the global record details
    if (sizeof(global_record_params_t) > 0) {
        global_record_params = (global_record_params_t *)
            spin1_malloc(sizeof(global_record_params_t));
        if (global_record_params == NULL) {
            log_error("Unable to allocate global record parameters"
                      "- Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for indexes
    if (sizeof(index_t) != 0) {
        indexes_array = (indexes_t *) spin1_malloc(
            n_neurons * sizeof(indexes_t));
        if (indexes_array == NULL) {
            log_error("Unable to allocate neuron array - Out of DTCM");
            return false;
        }
    }

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

    _reset_record_counter();
    recording_flags = recording_flags_param;

    // Set up the out spikes array
    size_t spike_size;
    if (global_record_params->spike_recording == n_neurons){
        spike_size = n_neurons;
    } else {
        spike_size = global_record_params->spike_recording + 1;
    }
    if (!out_spikes_initialize(spike_size)) {
        return false;
    }

    // Size of recording indexes
    if (global_record_params->v_recording == n_neurons){
        voltages_size = sizeof(uint32_t) + sizeof(state_t) * n_neurons;
        voltages = (timed_state_t *) spin1_malloc(voltages_size);
    } else {
        voltages_size = sizeof(uint32_t) +
            sizeof(state_t) * global_record_params->v_recording;
        // one extra for overflow
        voltages = (timed_state_t *) spin1_malloc(
            voltages_size + sizeof(state_t));
    }
    //log_debug("voltage_size = %u", voltages_size);

    if (global_record_params->exc_recording == n_neurons){
        exc_size = sizeof(uint32_t) + sizeof(input_struct_t) * n_neurons;
        inputs_excitatory = (timed_input_t *) spin1_malloc(exc_size);
    } else {
        exc_size = sizeof(uint32_t) +
            sizeof(input_struct_t) * global_record_params->exc_recording;
        // one extra for overflow
        inputs_excitatory = (timed_input_t *) spin1_malloc(
            exc_size + sizeof(input_struct_t));
    }
    //log_debug("exc_size = %u", exc_size);

    if (global_record_params->inh_recording == n_neurons){
        inh_size = sizeof(uint32_t) + sizeof(input_struct_t) * n_neurons;
        inputs_inhibitory = (timed_input_t *) spin1_malloc(exc_size);
    } else {
        inh_size = sizeof(uint32_t) +
            sizeof(input_struct_t) * global_record_params->inh_recording;
        // one extra for overflow
        inputs_inhibitory = (timed_input_t *) spin1_malloc(
            inh_size + sizeof(input_struct_t));
    }
    //log_debug("inh_size = %u", inh_size);

    _print_neuron_parameters();

    return true;
}

//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
void neuron_store_neuron_parameters(address_t address){

    uint32_t next = START_OF_GLOBAL_PARAMETERS;

    log_debug("writing parameters");

    log_debug("writing gobal recordi parameters");
    memcpy(&address[next], global_record_params, sizeof(global_record_params_t));
    next += sizeof(global_record_params_t) / 4;

    log_debug("writing index local parameters");
    memcpy(&address[next], indexes_array, n_neurons * sizeof(indexes_t));
    next += (n_neurons * sizeof(indexes_t)) / 4;

    //log_debug("writing neuron global parameters");
    memcpy(&address[next], global_parameters, sizeof(global_neuron_params_t));
    next += sizeof(global_neuron_params_t) / 4;

    log_debug("writing neuron local parameters");
    memcpy(&address[next], neuron_array, n_neurons * sizeof(neuron_t));
    next += (n_neurons * sizeof(neuron_t)) / 4;

    log_debug("writing input type parameters");
    memcpy(&address[next], input_type_array, n_neurons * sizeof(input_type_t));
    next += (n_neurons * sizeof(input_type_t)) / 4;

    log_debug("writing additional input type parameters");
    memcpy(&address[next], additional_input_array,
           n_neurons * sizeof(additional_input_t));
    next += (n_neurons * sizeof(additional_input_t)) / 4;

    log_debug("writing threshold type parameters");
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

//    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER_NEURON_UPDATE);

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

    // Reset the out spikes before starting if a beginning of recording
    if (spike_index == 1) {
        out_spikes_reset();
    }

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

        indexes_t* indexes = &indexes_array[neuron_index];

        // Get the parameters for this neuron
        neuron_pointer_t neuron = &neuron_array[neuron_index];
        input_type_pointer_t input_type = &input_type_array[neuron_index];
        threshold_type_pointer_t threshold_type =
            &threshold_type_array[neuron_index];
        additional_input_pointer_t additional_input =
            &additional_input_array[neuron_index];
        state_t voltage = neuron_model_get_membrane_voltage(neuron);

        // record this neuron parameter. Just as cheap to set then to gate
        voltages->states[indexes->v] = voltage;

        // Get excitatory and inhibitory input from synapses and convert it
        // to current input
        input_t* exc_syn_input = input_type_get_input_value(
        		synapse_types_get_excitatory_input(
        				&(neuron_synapse_shaping_params[neuron_index])),
						input_type, NUM_EXCITATORY_RECEPTORS);
        input_t* inh_syn_input = input_type_get_input_value(
        		synapse_types_get_inhibitory_input(
        				&(neuron_synapse_shaping_params[neuron_index])),
						input_type, NUM_INHIBITORY_RECEPTORS);

        // Sum g_syn contributions from all receptors for recording
        REAL total_exc = 0;
        REAL total_inh = 0;

        for (int i = 0; i < NUM_EXCITATORY_RECEPTORS; i++){
        	total_exc += exc_syn_input[i];
        }
        for (int i=0; i< NUM_INHIBITORY_RECEPTORS; i++){
        	total_inh += inh_syn_input[i];
        }

        // record these neuron parameter. Just as cheap to set then to gate
        inputs_excitatory->inputs[indexes->exc].input = total_exc;
        inputs_inhibitory->inputs[indexes->inh].input = total_inh;

        // Perform conversion of g_syn to current, including evaluation of
        // voltage-dependent inputs
        input_type_convert_excitatory_input_to_current(
        		exc_syn_input, input_type, voltage);
        input_type_convert_inhibitory_input_to_current(
        		inh_syn_input, input_type, voltage);

        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
            synapse_dynamics_get_intrinsic_bias(time, neuron_index) +
            additional_input_get_input_value_as_current(
                additional_input, voltage);

        // Update neuron parameters
        state_t result = neuron_model_state_update(
            NUM_EXCITATORY_RECEPTORS, exc_syn_input,
			NUM_INHIBITORY_RECEPTORS, inh_syn_input,
			external_bias, neuron);

        // Determine if a spike should occur
        bool spike = threshold_type_is_above_threshold(result, threshold_type);

        // If the neuron has spiked
        if (spike) {
            //log_debug("neuron %u spiked at time %u", neuron_index, time);

            // Tell the neuron model
            neuron_model_has_spiked(neuron);

            // Tell the additional input
            additional_input_has_spiked(additional_input);

            // Do any required synapse processing
            synapse_dynamics_process_post_synaptic_event(time, neuron_index);

            // Record the spike
            out_spikes_set_spike(indexes->spike);

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

    if (v_index == global_record_params->v_rate) {
        v_index = 1;
        // record neuron state (membrane potential) if needed
        n_recordings_outstanding += 1;
        voltages->time = time;
        recording_record_and_notify(
            V_RECORDING_CHANNEL, voltages, voltages_size,
            recording_done_callback);
    } else {
        // if not recording v_increment is 0 so v_index remains as 1 forever
        v_index += v_increment;
    }

    // record neuron inputs (excitatory) if needed
    if (exc_index == global_record_params->exc_rate) {
        exc_index = 1;
        n_recordings_outstanding += 1;
        inputs_excitatory->time = time;
        recording_record_and_notify(
            GSYN_EXCITATORY_RECORDING_CHANNEL, inputs_excitatory, exc_size,
            recording_done_callback);
    } else {
        exc_index += exc_increment;
    }

    // record neuron inputs (inhibitory) if needed
    if (inh_index == global_record_params->inh_rate) {
        inh_index = 1;
        n_recordings_outstanding += 1;
        inputs_inhibitory->time = time;
        recording_record_and_notify(
            GSYN_INHIBITORY_RECORDING_CHANNEL, inputs_inhibitory, inh_size,
            recording_done_callback);
    } else {
        inh_index += inh_increment;
    }

    // do logging stuff if required
    out_spikes_print();
    _print_neurons();

    // Record any spikes this timestep
    // record neuron inputs (inhibitory) if needed
    if (spike_index == global_record_params->spike_rate) {
        spike_index = 1;
        if (out_spikes_record(
                SPIKE_RECORDING_CHANNEL, time, recording_done_callback)) {
            n_recordings_outstanding += 1;
        }
   } else {
        spike_index += spike_increment;
   }

    // Re-enable interrupts
    spin1_mode_restore(cpsr);

//    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER_NEURON_UPDATE);
}
