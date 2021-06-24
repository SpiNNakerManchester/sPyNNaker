#ifndef _NEURON_IMPL_SINUSOID_READOUT_H_
#define _NEURON_IMPL_SINUSOID_READOUT_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/synapse_types/synapse_type_eprop_SHD.h>
#include <neuron/models/neuron_model_shd_readout_impl.h>
#include <neuron/input_types/input_type_current.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>
#include <neuron/threshold_types/threshold_type_static.h>

// Further includes
#include <common/out_spikes.h>
#include <common/maths-util.h>
#include <recording.h>
#include <debug.h>
#include <random.h>
#include <log.h>

#define V_RECORDING_INDEX 0
#define GSYN_EXCITATORY_RECORDING_INDEX 1
#define GSYN_INHIBITORY_RECORDING_INDEX 2

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
neuron_pointer_t neuron_array;

//! Input states array
static input_type_pointer_t input_type_array;

//! Additional input array
static additional_input_pointer_t additional_input_array;

//! Threshold states array
static threshold_type_pointer_t threshold_type_array;

//! Global parameters for the neurons
global_neuron_params_pointer_t global_parameters;

// The synapse shaping parameters
static synapse_param_t *neuron_synapse_shaping_params;

static REAL next_spike_time = 0;
extern uint32_t time;
extern key_t key;
extern REAL learning_signal[20];
static uint32_t target_ind = 0;

REAL output_errors[20] = {0.k};
REAL accumulated_softmax = 0.k;
REAL min_v_mem = 1000.k;
REAL max_v_mem = -1000.k;
bool printed_values = false;

static bool neuron_impl_initialise(uint32_t n_neurons) {

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
//        log_info("size = %u", sizeof(neuron_t));
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

    // Allocate DTCM for synapse shaping parameters
    if (sizeof(synapse_param_t) != 0) {
        neuron_synapse_shaping_params = (synapse_param_t *) spin1_malloc(
            n_neurons * sizeof(synapse_param_t));
        if (neuron_synapse_shaping_params == NULL) {
            log_error("Unable to allocate synapse parameters array"
                " - Out of DTCM");
            return false;
        }
    }

    // Initialise pointers to Neuron parameters in STDP code
//    synapse_dynamics_set_neuron_array(neuron_array);
    log_info("set pointer to neuron array in stdp code");

    return true;
}

static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // simple wrapper to synapse type input function
    synapse_param_pointer_t parameters =
            &(neuron_synapse_shaping_params[neuron_index]);
    synapse_types_add_neuron_input(synapse_type_index,
            parameters, weights_this_timestep);
}

static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("reading parameters, next is %u, n_neurons is %u ",
        next, n_neurons);

    //log_debug("writing neuron global parameters");
    spin1_memcpy(global_parameters, &address[next],
            sizeof(global_neuron_params_t));
    next += (sizeof(global_neuron_params_t) + 3) / 4;

    log_debug("reading neuron local parameters");
    spin1_memcpy(neuron_array, &address[next], n_neurons * sizeof(neuron_t));
    next += ((n_neurons * sizeof(neuron_t)) + 3) / 4;

    log_debug("reading input type parameters");
    spin1_memcpy(input_type_array, &address[next],
            n_neurons * sizeof(input_type_t));
    next += ((n_neurons * sizeof(input_type_t)) + 3) / 4;

    log_debug("reading threshold type parameters");
    spin1_memcpy(threshold_type_array, &address[next],
           n_neurons * sizeof(threshold_type_t));
    next += ((n_neurons * sizeof(threshold_type_t)) + 3) / 4;

    log_debug("reading synapse parameters");
    spin1_memcpy(neuron_synapse_shaping_params, &address[next],
           n_neurons * sizeof(synapse_param_t));
    next += ((n_neurons * sizeof(synapse_param_t)) + 3) / 4;

    log_debug("reading additional input type parameters");
        spin1_memcpy(additional_input_array, &address[next],
               n_neurons * sizeof(additional_input_t));
    next += ((n_neurons * sizeof(additional_input_t)) + 3) / 4;

    neuron_model_set_global_neuron_params(global_parameters);

//    io_printf(IO_BUF, "\nPrinting global params\n");
//    io_printf(IO_BUF, "seed 1: %u \n", global_parameters->spike_source_seed[0]);
//    io_printf(IO_BUF, "seed 2: %u \n", global_parameters->spike_source_seed[1]);
//    io_printf(IO_BUF, "seed 3: %u \n", global_parameters->spike_source_seed[2]);
//    io_printf(IO_BUF, "seed 4: %u \n", global_parameters->spike_source_seed[3]);
    io_printf(IO_BUF, "eta: %k\n\n", global_parameters->eta);
    io_printf(IO_BUF, "target data 0: %u\n\n", global_parameters->target_V[0]);
    io_printf(IO_BUF, "target data 1: %u\n\n", global_parameters->target_V[1]);
    io_printf(IO_BUF, "target data 2: %u\n\n", global_parameters->target_V[2]);
    io_printf(IO_BUF, "target data 3: %u\n\n", global_parameters->target_V[3]);
    io_printf(IO_BUF, "target data 4: %u\n\n", global_parameters->target_V[4]);
    io_printf(IO_BUF, "target data 5: %u\n\n", global_parameters->target_V[5]);
    io_printf(IO_BUF, "target data 6: %u\n\n", global_parameters->target_V[6]);
    io_printf(IO_BUF, "target data 7: %u\n\n", global_parameters->target_V[7]);
    io_printf(IO_BUF, "target data 8: %u\n\n", global_parameters->target_V[8]);
    io_printf(IO_BUF, "target data 9: %u\n\n", global_parameters->target_V[9]);


    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
    }

//    io_printf(IO_BUF, "size of global params: %u",
//    		sizeof(global_neuron_params_t));



    #if LOG_LEVEL >= LOG_DEBUG
        log_debug("-------------------------------------\n");
        for (index_t n = 0; n < n_neurons; n++) {
            neuron_model_print_parameters(&neuron_array[n]);
        }
        log_debug("-------------------------------------\n");
        //}
    #endif // LOG_LEVEL >= LOG_DEBUG
}




static bool neuron_impl_do_timestep_update(index_t neuron_index,
        input_t external_bias, state_t *recorded_variable_values) {

    // Get the neuron itself
    neuron_pointer_t neuron = &neuron_array[neuron_index];
    bool spike = false;

//    io_printf(IO_BUF, "Updating Neuron Index: %u\n", neuron_index);
//    io_printf(IO_BUF, "Target: %k\n\n",
//    		global_parameters->target_V[target_ind]);

    // Get the input_type parameters and voltage for this neuron
    input_type_pointer_t input_type = &input_type_array[neuron_index];

    // Get threshold and additional input parameters for this neuron
    threshold_type_pointer_t threshold_type =
    		&threshold_type_array[neuron_index];
    additional_input_pointer_t additional_input =
    		&additional_input_array[neuron_index];
    synapse_param_pointer_t synapse_type =
    		&neuron_synapse_shaping_params[neuron_index];

    // Get the voltage
    state_t voltage = neuron_model_get_membrane_voltage(neuron);


    // Get the exc and inh values from the synapses
    input_t* exc_value = synapse_types_get_excitatory_input(synapse_type);
    input_t* inh_value = synapse_types_get_inhibitory_input(synapse_type);

    // Call functions to obtain exc_input and inh_input
    input_t* exc_input_values = input_type_get_input_value(
           exc_value, input_type, NUM_EXCITATORY_RECEPTORS);
    input_t* inh_input_values = input_type_get_input_value(
           inh_value, input_type, NUM_INHIBITORY_RECEPTORS);

    // Sum g_syn contributions from all receptors for recording
//    REAL total_exc = 0;
//    REAL total_inh = 0;
//
//    for (int i = 0; i < NUM_EXCITATORY_RECEPTORS-1; i++){
//    	total_exc += exc_input_values[i];
//    }
//    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS-1; i++){
//    	total_inh += inh_input_values[i];
//    }

    // Call functions to get the input values to be recorded
//    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = total_exc;
//    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = total_inh;

    // Call functions to convert exc_input and inh_input to current
    input_type_convert_excitatory_input_to_current(
    		exc_input_values, input_type, voltage);
    input_type_convert_inhibitory_input_to_current(
    		inh_input_values, input_type, voltage);

    external_bias += additional_input_get_input_value_as_current(
    		additional_input, voltage);

        // update neuron parameters
    state_t result = neuron_model_state_update(
                NUM_EXCITATORY_RECEPTORS, exc_input_values,
                NUM_INHIBITORY_RECEPTORS, inh_input_values,
                external_bias, neuron, neuron_index);

//    REAL mem_downscale = 1.k;
//    if (result / mem_downscale > 8.75k){
//        output_errors[neuron_index] = expk(8.75k);
//    }
//    else{
//        output_errors[neuron_index] = expk(result / mem_downscale);
//    }
    if (neuron_index == 0){
        max_v_mem = -1000.k;
        min_v_mem = 1000.k;
        accumulated_softmax = 0.k;
    }
    output_errors[neuron_index] = result;
    if (result > max_v_mem){
        max_v_mem = result;
    }
//    if (result < min_v_mem){
//        min_v_mem = result;
//    }
//    accumulated_softmax += output_errors[neuron_index];
//    if (!printed_values){
//        io_printf(IO_BUF, "out:%d, vmem:%k, res:%k\n", neuron_index, voltage, result);
//    }


//    if (time % 100 == 0){
//        io_printf(IO_BUF, "%u n_ind:%u, [%u]target:%u\n", time, neuron_index, target_ind,
//                                                            global_parameters->target_V[target_ind]);
//    }
//    recorded_variable_values[V_RECORDING_INDEX] = voltage;
    if (neuron_index == 19){
//        if (!printed_values){
//            io_printf(IO_BUF, "%d Printing learning values: max_v %k\n", time, max_v_mem);
//        }
        REAL norm_rescale = max_v_mem - 8.k;
//        if (norm_rescale > 8.75k){
//            norm_rescale = 8.75k;
//        }
        // Normalise errors and exp
        for (uint32_t n_ind=0; n_ind < 20; n_ind++){
//            if (!printed_values){
//                io_printf(IO_BUF, "output:%d, error:%k, resscale:%k\n", n_ind, output_errors[n_ind], norm_rescale);
//            }
//            if (norm_rescale > 0){
//                output_errors[n_ind] -= min_v_mem;
//                output_errors[n_ind] /= (max_v_mem - min_v_mem) * 0.05k;
//                output_errors[n_ind] -= 1.k;
//                output_errors[n_ind] *= norm_rescale;
//            }
            output_errors[n_ind] -= norm_rescale;
            output_errors[n_ind] = expk(output_errors[n_ind]);
            accumulated_softmax += output_errors[n_ind];
        }
        // Calculate error
        for (uint32_t n_ind=0; n_ind < 20; n_ind++){  // set to 20 when english and german
//            if (!printed_values){
//                io_printf(IO_BUF, "output:%d, error:%k, sm:%k", n_ind, output_errors[n_ind], accumulated_softmax);
//            }
            if (accumulated_softmax > 0.k){ // because overflow and e^-x=0
                output_errors[n_ind] /= accumulated_softmax;
            }
            REAL correct_output = 0.k;

            if (n_ind == global_parameters->target_V[target_ind]){

//                if (time % 1000 == 0){
//                    io_printf(IO_BUF, "32 == 8\n");
//                }

                correct_output = 1.k;
            }
            learning_signal[n_ind] = output_errors[n_ind] - correct_output;
//            if (!printed_values){
//                io_printf(IO_BUF, " corr:%k, L:%k\n", correct_output, learning_signal[n_ind]);
//            }
            // Send error (learning signal) as packet with payload
            while (!spin1_send_mc_packet(
                    key | n_ind,  bitsk(learning_signal[n_ind]), 1 )) {
                spin1_delay_us(1);
            }
        }
//        printed_values = true;
//        if (time % 51 == 0){
//            io_printf(IO_BUF, "\n");
//            printed_values = false;
//        }
        if (time % 1000 == 999){ // after every test is finished
            target_ind += 1;
//            io_printf(IO_BUF, "tar idx %u\n", target_ind);
//            for (uint32_t n_ind=0; n_ind < 10; n_ind++){
//                neuron_pointer_t neuron_resetting = &neuron_array[n_ind];
//                neuron_resetting->V_membrane = neuron_resetting->V_rest;
//            }
        }
    }
//    else{
//        // Record 'Error'
//        recorded_variable_values[V_RECORDING_INDEX] =
////                neuron->syn_state[0].z_bar;
//                global_parameters->target_V[target_ind];
////        recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] =
////                - global_parameters->target_V[target_ind];
//    }
//    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->syn_state[neuron_index*20].z_bar;
    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] =
                                    learning_signal[global_parameters->target_V[target_ind]];
//                                    neuron->syn_state[neuron_index*25].z_bar;
//                                    neuron->L;
//                                    *exc_input_values;
//                                    neuron->syn_state[neuron_index*5].delta_w;
//                                    neuron->syn_state[neuron_index*5].update_ready;
//        			                  exc_input_values[1];

    // Record target
    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] =
//        			global_parameters->target_V[target_ind];
//                    learning_signal[neuron_index];
//                    neuron->syn_state[neuron_index*69].delta_w;
        			neuron->syn_state[neuron_index*2].delta_w * global_parameters->eta;
//        			exc_input_values[0];

    recorded_variable_values[V_RECORDING_INDEX] = result;
//                                    neuron->syn_state[neuron_index*5].z_bar;

    // If spike occurs, communicate to relevant parts of model
    if (spike) {
        // Call relevant model-based functions
        // Tell the neuron model
//        neuron_model_has_spiked(neuron);

        // Tell the additional input
        additional_input_has_spiked(additional_input);
    }

    // Shape the existing input according to the included rule
    synapse_types_shape_input(synapse_type);

    #if LOG_LEVEL >= LOG_DEBUG
        neuron_model_print_state_variables(neuron);
    #endif // LOG_LEVEL >= LOG_DEBUG

    // Return the boolean to the model timestep update
    return spike;
}





//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("writing parameters");

    //log_debug("writing neuron global parameters");
    spin1_memcpy(&address[next], global_parameters,
            sizeof(global_neuron_params_t));
    next += (sizeof(global_neuron_params_t) + 3) / 4;

    log_debug("writing neuron local parameters");
    spin1_memcpy(&address[next], neuron_array,
            n_neurons * sizeof(neuron_t));
    next += ((n_neurons * sizeof(neuron_t)) + 3) / 4;

    log_debug("writing input type parameters");
    spin1_memcpy(&address[next], input_type_array,
            n_neurons * sizeof(input_type_t));
    next += ((n_neurons * sizeof(input_type_t)) + 3) / 4;

    log_debug("writing threshold type parameters");
    spin1_memcpy(&address[next], threshold_type_array,
            n_neurons * sizeof(threshold_type_t));
    next += ((n_neurons * sizeof(threshold_type_t)) + 3) / 4;

    log_debug("writing synapse parameters");
    spin1_memcpy(&address[next], neuron_synapse_shaping_params,
            n_neurons * sizeof(synapse_param_t));
    next += ((n_neurons * sizeof(synapse_param_t)) + 3) / 4;

    log_debug("writing additional input type parameters");
    spin1_memcpy(&address[next], additional_input_array,
            n_neurons * sizeof(additional_input_t));
    next += ((n_neurons * sizeof(additional_input_t)) + 3) / 4;
}

#if LOG_LEVEL >= LOG_DEBUG
void neuron_impl_print_inputs(uint32_t n_neurons) {
	bool empty = true;
	for (index_t i = 0; i < n_neurons; i++) {
		empty = empty
				&& (bitsk(synapse_types_get_excitatory_input(
						&(neuron_synapse_shaping_params[i]))
					- synapse_types_get_inhibitory_input(
						&(neuron_synapse_shaping_params[i]))) == 0);
	}

	if (!empty) {
		log_debug("-------------------------------------\n");

		for (index_t i = 0; i < n_neurons; i++) {
			input_t input =
				synapse_types_get_excitatory_input(
					&(neuron_synapse_shaping_params[i]))
				- synapse_types_get_inhibitory_input(
					&(neuron_synapse_shaping_params[i]));
			if (bitsk(input) != 0) {
				log_debug("%3u: %12.6k (= ", i, input);
				synapse_types_print_input(
					&(neuron_synapse_shaping_params[i]));
				log_debug(")\n");
			}
		}
		log_debug("-------------------------------------\n");
	}
}

void neuron_impl_print_synapse_parameters(uint32_t n_neurons) {
	log_debug("-------------------------------------\n");
	for (index_t n = 0; n < n_neurons; n++) {
	    synapse_types_print_parameters(&(neuron_synapse_shaping_params[n]));
	}
	log_debug("-------------------------------------\n");
}

const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
	return synapse_types_get_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_SINUSOID_READOUT_H_
