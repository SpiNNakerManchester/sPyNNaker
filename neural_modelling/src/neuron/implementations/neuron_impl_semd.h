#ifndef _NEURON_IMPL_SEMD_H_
#define _NEURON_IMPL_SEMD_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include "../models/neuron_model.h"
#include "../input_types/input_type.h"
#include "../additional_inputs/additional_input.h"
#include "../threshold_types/threshold_type.h"
#include "../synapse_types/synapse_types.h"

// Further includes
#include "../plasticity/synapse_dynamics.h"
#include "../structural_plasticity/synaptogenesis_dynamics.h"
#include "../../common/out_spikes.h"
#include <recording.h>
#include <debug.h>
#include <string.h>

//! neuron_impl_t struct
typedef struct neuron_impl_t {
} neuron_impl_t;

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

// declare spin1_wfi
void spin1_wfi();

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

//! The number of recordings outstanding
static uint32_t n_recordings_outstanding = 0;

//! TODO: Add comment about this here
static void neuron_impl_reset_record_counter()
{
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

//! \brief Initialise the particular implementation of the data
//! \param[in] data_address The address of the data to be initialised
//! \return boolean for error
static bool neuron_impl_initialise(uint32_t n_neurons)
{
    // log message for debug purposes
    log_debug(
        "\t neurons = %u, params size = %u,"
        "input type size = %u, threshold size = %u", n_neurons,
        sizeof(neuron_t), sizeof(input_type_t), sizeof(threshold_type_t));

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

    return true;

}

//    voltages_size = sizeof(uint32_t) + sizeof(state_t) * n_neurons;
//    voltages = (timed_state_t *) spin1_malloc(voltages_size);
//    input_size = sizeof(uint32_t) + sizeof(input_struct_t) * n_neurons;
//    inputs_excitatory = (timed_input_t *) spin1_malloc(input_size);
//    inputs_inhibitory = (timed_input_t *) spin1_malloc(input_size);

static void neuron_impl_initialise_recording(uint32_t n_neurons)
{
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

}

//! \brief return value for spike size
static size_t neuron_impl_spike_size()
{
	size_t spike_size;

    if (global_record_params->spike_recording == n_neurons){
        spike_size = n_neurons;
    } else {
        spike_size = global_record_params->spike_recording + 1;
    }

	return spike_size;
}

//! \brief Add inputs as required to the implementation
//! \param[in] synapse_type_index the synapse type (exc. or inh.)
//! \param[in] parameter parameters for synapse shaping
//! \param[in] weights_this_timestep Weight inputs to be added
static void neuron_impl_add_inputs(
		index_t synapse_type_index, synapse_param_pointer_t parameter,
		input_t weights_this_timestep)
{
	// simple wrapper to synapse type input function
	synapse_types_add_neuron_input(synapse_type_index,
			parameter, weights_this_timestep);
}

//! \bried Load in the neuron parameters
//! \return None
static void neuron_impl_load_neuron_parameters(address_t address, uint32_t next)
{
    log_debug("writing parameters, next is %u ", next);

    log_debug("writing global recording parameters");
    memcpy(global_record_params, &address[next], sizeof(global_record_params_t));
    next += sizeof(global_record_params_t) / 4;

    log_debug("writing index local parameters");
    memcpy(indexes_array, &address[next], n_neurons * sizeof(indexes_t));
    next += (n_neurons * sizeof(indexes_t)) / 4;

    //log_debug("writing neuron global parameters");
    memcpy(global_parameters, &address[next], sizeof(global_neuron_params_t));
    next += sizeof(global_neuron_params_t) / 4;

    log_debug("writing neuron local parameters");
    memcpy(neuron_array, &address[next], n_neurons * sizeof(neuron_t));
    next += (n_neurons * sizeof(neuron_t)) / 4;

    log_debug("writing input type parameters");
    memcpy(input_type_array, &address[next], n_neurons * sizeof(input_type_t));
    next += (n_neurons * sizeof(input_type_t)) / 4;

    log_debug("writing additional input type parameters");
    memcpy(additional_input_array, &address[next],
           n_neurons * sizeof(additional_input_t));
    next += (n_neurons * sizeof(additional_input_t)) / 4;

    log_debug("writing threshold type parameters");
    memcpy(threshold_type_array, &address[next],
           n_neurons * sizeof(threshold_type_t));

}

//! \brief Wrapper to set global neuron parameters ?
//! \return None
static void neuron_impl_set_global_neuron_parameters()
{
    neuron_model_set_global_neuron_params(global_parameters);
}

//! \brief forgot about this one
static void neuron_impl_wait_for_recordings_and_reset_out_spikes() {
    // Wait until recordings have completed, to ensure the recording space
    // can be re-written
    while (n_recordings_outstanding > 0) {
        spin1_wfi();
    }
	if (spike_index == 1) {
	    out_spikes_reset();
	}
}

//! \brief Do the timestep update for the particular implementation
//! \param[in] neuron index
//! \return bool value for whether a spike has occurred
static bool neuron_impl_do_timestep_update(timer_t time, index_t neuron_index)
{
	// Array for index recording
    indexes_t* indexes = &indexes_array[neuron_index];

	// Get the neuron itself
    neuron_pointer_t neuron = &neuron_array[neuron_index];

    // Get the input_type parameters and voltage for this neuron
    input_type_pointer_t input_type = &input_type_array[neuron_index];

    // Get threshold and additional input parameters for this neuron
    threshold_type_pointer_t threshold_type =
        &threshold_type_array[neuron_index];
    additional_input_pointer_t additional_input =
        &additional_input_array[neuron_index];

    // Get the voltage
    state_t voltage = neuron_impl_get_membrane_voltage(neuron_index);

    // If we should be recording potential, record this neuron parameter
    voltages->states[indexes->v] = voltage;

    // Get the exc and inh values from the synapses
    input_t* exc_value = synapse_types_get_excitatory_input(
    		&(neuron_synapse_shaping_params[neuron_index]));
    input_t* inh_value = synapse_types_get_inhibitory_input(
    		&(neuron_synapse_shaping_params[neuron_index]));

    // Call functions to obtain exc_input and inh_input
    input_t* exc_input_value = input_type_get_input_value(
    		exc_value, input_type, NUM_EXCITATORY_RECEPTORS);
    input_t* inh_input_value = input_type_get_input_value(
    		inh_value, input_type, NUM_INHIBITORY_RECEPTORS);

    // Call functions to convert exc_input to current
    input_type_convert_excitatory_input_to_current(
    		exc_input_value, input_type, voltage);

    // Set the inhibitory multiplicator value
    input_type_set_inhibitory_multiplicator_value(
    		exc_input_value, input_type, inh_input_value);

    // Call functions to convert exc_input and inh_input to current
    input_type_convert_inhibitory_input_to_current(
    		inh_input_value, input_type, voltage);

    // Sum g_syn contributions from all receptors for recording
    REAL total_exc = 0;
    REAL total_inh = 0;

    for (int i=0; i<NUM_EXCITATORY_RECEPTORS; i++){
        total_exc += exc_input_value[i];
    }
    for (int i=0; i<NUM_INHIBITORY_RECEPTORS; i++){
        total_inh += inh_input_value[i];
    }

    // Call functions to get the input values to be recorded
    inputs_excitatory->inputs[indexes->exc].input = total_exc;
    inputs_inhibitory->inputs[indexes->inh].input = total_inh;

    // Get external bias from any source of intrinsic plasticity
    input_t external_bias =
        synapse_dynamics_get_intrinsic_bias(time, neuron_index) +
        additional_input_get_input_value_as_current(
            additional_input, voltage);

    // update neuron parameters
    state_t result = neuron_model_state_update(
    		NUM_EXCITATORY_RECEPTORS, exc_input_value,
			NUM_INHIBITORY_RECEPTORS, inh_input_value,
			external_bias, neuron);

    // determine if a spike should occur
    bool spike = threshold_type_is_above_threshold(result, threshold_type);

    // If spike occurs, communicate to relevant parts of model
    if (spike) {
        // Call relevant model-based functions
    	// Tell the neuron model
    	neuron_model_has_spiked(neuron);

    	// Tell the additional input
    	additional_input_has_spiked(additional_input);

        // Do any required synapse processing
        synapse_dynamics_process_post_synaptic_event(time, neuron_index);

        // Record the spike
        out_spikes_set_spike(neuron_index);
    }

    // Return the boolean to the model timestep update
    return spike;
}

//! \setter for the internal input buffers
//! \param[in] input_buffers_value the new input buffers
static void neuron_impl_set_neuron_synapse_shaping_params(
		synapse_param_t *neuron_synapse_shaping_params_value)
{
    neuron_synapse_shaping_params = neuron_synapse_shaping_params_value;
}

//! \brief Wrapper for the neuron model's print state variables function
static void neuron_impl_print_state_variables(index_t neuron_index)
{
	// wrapper to the model print function
	neuron_model_print_state_variables(&(neuron_array[neuron_index]));
}

//! \brief Wrapper for the neuron model's print parameters function
static void neuron_impl_print_parameters(index_t neuron_index)
{
	neuron_model_print_parameters(&(neuron_array[neuron_index]));
}

//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
static void neuron_impl_store_neuron_parameters(address_t address, uint32_t next){

    log_debug("writing parameters");

    log_debug("writing global recording parameters");
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

//! \brief callback at end of recording
void recording_done_callback() {
    n_recordings_outstanding -= 1;
}

//! \brief Do any required recording
//! \param[in] recording_flags
//! \return None
static void neuron_impl_do_recording(timer_t time) //, uint32_t recording_flags)
{
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
}

//! \brief not sure this is needed but something weird is happening
static void neuron_impl_record_spikes(timer_t time)
{
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
}

//! \return The membrane voltage value
static input_t neuron_impl_get_membrane_voltage(index_t neuron_index)
{
    neuron_pointer_t neuron = &neuron_array[neuron_index];
	return neuron_model_get_membrane_voltage(neuron);
}

#endif // _NEURON_IMPL_SEMD_H_
