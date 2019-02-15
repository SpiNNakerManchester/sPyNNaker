#ifndef _NEURON_IMPL_STANDARD_H_
#define _NEURON_IMPL_STANDARD_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <neuron/synapse_types/synapse_types_exponential_impl.h>
#include <neuron/models/neuron_model_lif_poisson_impl.h>
#include <neuron/input_types/input_type_current.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>
#include <neuron/threshold_types/threshold_type_static.h>

// Further includes
#include <common/out_spikes.h>
#include <recording.h>
#include <debug.h>
#include <random.h>

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
static neuron_pointer_t neuron_array;

//! Input states array
static input_type_pointer_t input_type_array;

//! Additional input array
static additional_input_pointer_t additional_input_array;

//! Threshold states array
static threshold_type_pointer_t threshold_type_array;

//! Global parameters for the neurons
static global_neuron_params_pointer_t global_parameters;

// The synapse shaping parameters
static synapse_param_t *neuron_synapse_shaping_params;

static REAL next_spike_time;
static REAL rate_at_last_time_calc;

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

//    io_printf(IO_BUF, "Printing global params\n");
//    io_printf(IO_BUF, "seed 1: %u \n", global_parameters[0]);
//    io_printf(IO_BUF, "seed 2: %u \n", global_parameters[1]);
//    io_printf(IO_BUF, "seed 3: %u \n", global_parameters[2]);
//    io_printf(IO_BUF, "seed 4: %u \n", global_parameters[3]);
//    io_printf(IO_BUF, "seconds_per_tick: %k \n", global_parameters[4]);
//    io_printf(IO_BUF, "ticks_per_second: %k \n", global_parameters[5]);


    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
    }

    io_printf(IO_BUF, "size of global params: %u",
    		sizeof(global_neuron_params_t));



    #if LOG_LEVEL >= LOG_DEBUG
        log_debug("-------------------------------------\n");
        for (index_t n = 0; n < n_neurons; n++) {
            neuron_model_print_parameters(&neuron_array[n]);
        }
        log_debug("-------------------------------------\n");
        //}
    #endif // LOG_LEVEL >= LOG_DEBUG
}


// &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

// Poisson Spike Source Functions

static inline REAL slow_spike_source_get_time_to_spike(
        REAL mean_inter_spike_interval_in_ticks, neuron_pointer_t neuron) {
    return exponential_dist_variate(
            mars_kiss64_seed,
			neuron->spike_source_seed
//			global_parameters->spike_source_seed
			)
        * mean_inter_spike_interval_in_ticks;
    rate_at_last_time_calc = neuron->V_membrane;
}



void set_spike_source_rate(neuron_pointer_t neuron, REAL rate,
		threshold_type_pointer_t threshold_type) {

	// clip rate to ensure divde by 0 and overflow don't occur
	if (rate < 0.25){
		rate = 0.25;
	} else if (rate > threshold_type->threshold_value) {
		rate = threshold_type->threshold_value;
	}

    neuron->mean_isi_ticks =
//                rate *
////				global_parameters->ticks_per_second; // shouldn't this be ticks_per_second/rate?
//				neuron->ticks_per_second   ; // shouldn't this be ticks_per_second/rate?
			neuron->ticks_per_second / rate  ; // shouldn't this be ticks_per_second/rate?

    io_printf(IO_BUF, "New rate: %k, New mean ISI ticks: %k\n",
        		rate, neuron->mean_isi_ticks);

    if (neuron->mean_isi_ticks < neuron->time_to_spike_ticks) {
    	neuron->time_to_spike_ticks = neuron->mean_isi_ticks;
    }
////
//    // This ensures we update to reduced time_to_next_spike, even without spiking
//    if (next_spike_time > neuron->mean_isi_ticks << 3){
//    	neuron->time_to_spike_ticks = neuron->mean_isi_ticks; // update to the new mean
//    } else if (next_spike_time < neuron->mean_isi_ticks >> 3) {
//    	neuron->time_to_spike_ticks = neuron->mean_isi_ticks; // update to the new mean
//    }

//    REAL mod_rate_diff = (rate_at_last_time_calc - rate);
//
//    if (mod_rate_diff > 5) {
//    	neuron->time_to_spike_ticks = slow_spike_source_get_time_to_spike(
//                neuron->mean_isi_ticks, neuron);
//    } else if (mod_rate_diff < -5) {
//    	neuron->time_to_spike_ticks = slow_spike_source_get_time_to_spike(
//                neuron->mean_isi_ticks, neuron);
//    }
}





bool timer_update_determine_poisson_spiked(neuron_pointer_t neuron) {
	// NOTE: ALL SOURCES TREATED AS SLOW SOURCES!!!
	// NOTE: NO SOURCE CAN SPIKE MORE THAN ONCE PER TIMESTEP
    // If this spike source should spike now

	bool has_spiked = false;


	io_printf(IO_BUF, " 				Time to next spike: %k\n",
			neuron->time_to_spike_ticks);

    if (REAL_COMPARE(
            neuron->time_to_spike_ticks, <=,
            REAL_CONST(0.0))) {

        // Update time to spike
    	next_spike_time = slow_spike_source_get_time_to_spike(
                neuron->mean_isi_ticks, neuron);

        neuron->time_to_spike_ticks += next_spike_time;
//        neuron->time_to_spike_ticks +=slow_spike_source_get_time_to_spike(
//                neuron->mean_isi_ticks, neuron);


        has_spiked = true;
    }

    // Subtract tick
    neuron->time_to_spike_ticks -= REAL_CONST(1.0);


    return has_spiked;
}

// &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&







static bool neuron_impl_do_timestep_update(index_t neuron_index,
        input_t external_bias, state_t *recorded_variable_values) {

    // Get the neuron itself
    neuron_pointer_t neuron = &neuron_array[neuron_index];

    io_printf(IO_BUF, "Updating Neuron Index: %u\n", neuron_index);


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
    recorded_variable_values[V_RECORDING_INDEX] = voltage;

    // Get the exc and inh values from the synapses
    input_t* exc_value = synapse_types_get_excitatory_input(synapse_type);
    input_t* inh_value = synapse_types_get_inhibitory_input(synapse_type);

    // Call functions to obtain exc_input and inh_input
    input_t* exc_input_values = input_type_get_input_value(
            exc_value, input_type, NUM_EXCITATORY_RECEPTORS);
    input_t* inh_input_values = input_type_get_input_value(
            inh_value, input_type, NUM_INHIBITORY_RECEPTORS);

    // Sum g_syn contributions from all receptors for recording
    REAL total_exc = 0;
    REAL total_inh = 0;

    for (int i = 0; i < NUM_EXCITATORY_RECEPTORS; i++){
        total_exc += exc_input_values[i];
    }
    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++){
        total_inh += inh_input_values[i];
    }

    // Call functions to get the input values to be recorded
    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = total_exc;
    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = total_inh;

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
            external_bias, neuron);

    // determine if a spike should occur
    // bool spike = threshold_type_is_above_threshold(result, threshold_type);


    // Update Poisson neuron rate based on updated V
    REAL rate = result; // just a linear scaling for now
    set_spike_source_rate(neuron, rate, threshold_type);

    // judge whether poisson neuron should have fired
    bool spike = timer_update_determine_poisson_spiked(neuron);




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

#endif // _NEURON_IMPL_STANDARD_H_
