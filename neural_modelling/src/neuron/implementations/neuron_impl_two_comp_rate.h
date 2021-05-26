/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _NEURON_IMPL_TWO_COMP_RATE_H_
#define _NEURON_IMPL_TWO_COMP_RATE_H_

#include "neuron_impl.h"

// Includes for model parts used in this implementation
#include <synapse/synapse_types/synapse_types_two_comp_rate_exponential_impl.h>
#include <neuron/models/neuron_model_lif_two_comp_rate_impl.h>
#include <neuron/input_types/input_type_two_comp_rate.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>
#include <neuron/threshold_types/threshold_type_static.h>
#include <synapse/plasticity/stdp/post_events_rate.h>

// Further includes
#include <common/out_spikes.h>
#include <recording.h>
#include <debug.h>
#include <random.h>
#include <round.h>
#include <common/rate_generator.h>

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

#define DMA_TAG_WRITE_POSTSYNAPTIC_BUFFER 2

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

//! The synapse shaping parameters
static synapse_param_t *neuron_synapse_shaping_params;

//! Data structure for the output rate LUT
static REAL *rate_lut;
static uint32_t rate_lut_size;

//! Array containing the postsynaptic rates
static post_event_history_t *postsynaptic_rates;

//! Pointer to the SDRAM region for the postsynaptic rates
static post_event_history_t *postsynaptic_buffer;

static REAL *background_activity;

static uint32_t seeds[] = {100, 200, 300, 40}; 

static inline void generate_background_activity(uint32_t n_neurons) {
    for (index_t i = 0; i < n_neurons; i++) {
        background_activity[i] = 0.1k * gaussian_dist_variate(
                                            mars_kiss64_seed,
                                            seeds);
        //io_printf(IO_BUF, "rand %k\n", background_activity[i]);
    }
}

static bool neuron_impl_initialise(uint32_t n_neurons) {
    // allocate DTCM for the global parameter details
    if (sizeof(global_neuron_params_t)) {
        global_parameters = spin1_malloc(sizeof(global_neuron_params_t));
        if (global_parameters == NULL) {
            log_error("Unable to allocate global neuron parameters"
                    "- Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for neuron array
    if (sizeof(neuron_t)) {
        neuron_array = spin1_malloc(n_neurons * sizeof(neuron_t));
        if (neuron_array == NULL) {
            log_error("Unable to allocate neuron array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for input type array and copy block of data
    if (sizeof(input_type_t)) {
        input_type_array = spin1_malloc(n_neurons * sizeof(input_type_t));
        if (input_type_array == NULL) {
            log_error("Unable to allocate input type array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for additional input array and copy block of data
    if (sizeof(additional_input_t)) {
        additional_input_array =
                spin1_malloc(n_neurons * sizeof(additional_input_t));
        if (additional_input_array == NULL) {
            log_error("Unable to allocate additional input array"
                    " - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for threshold type array and copy block of data
    if (sizeof(threshold_type_t)) {
        threshold_type_array =
                spin1_malloc(n_neurons * sizeof(threshold_type_t));
        if (threshold_type_array == NULL) {
            log_error("Unable to allocate threshold type array - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for synapse shaping parameters
    if (sizeof(synapse_param_t)) {
        neuron_synapse_shaping_params =
                spin1_malloc(n_neurons * sizeof(synapse_param_t));
        if (neuron_synapse_shaping_params == NULL) {
            log_error("Unable to allocate synapse parameters array"
                    " - Out of DTCM");
            return false;
        }
    }

    postsynaptic_rates = post_events_init_buffers(n_neurons);

    background_activity = spin1_malloc(n_neurons * sizeof(REAL));
    if (background_activity == NULL) {
        log_error("Unable to allocate background activity array - Out of DTCM");
        return false;
    }

    generate_background_activity(n_neurons);

    return true;
}

static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // simple wrapper to synapse type input function
    synapse_param_pointer_t parameters =
            &neuron_synapse_shaping_params[neuron_index];
    synapse_types_add_neuron_input(synapse_type_index,
            parameters, weights_this_timestep);
}

static uint32_t n_words_needed(uint32_t size) {
    return (size + (sizeof(uint32_t) - 1)) / sizeof(uint32_t);
}

static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("reading parameters, next is %u, n_neurons is %u ",
            next, n_neurons);

    if (sizeof(global_neuron_params_t)) {
        log_debug("writing neuron global parameters");
        spin1_memcpy(global_parameters, &address[next],
                sizeof(global_neuron_params_t));
        next += n_words_needed(sizeof(global_neuron_params_t));
    }

    if (sizeof(neuron_t)) {
        log_debug("reading neuron local parameters");
        spin1_memcpy(neuron_array, &address[next],
                n_neurons * sizeof(neuron_t));
        next += n_words_needed(n_neurons * sizeof(neuron_t));
    }

    //io_printf(IO_BUF, "copied neuron params\n");

    // THIS COPIES 0 BYTES, REMOVE?
    if (sizeof(input_type_t)) {
        log_debug("reading input type parameters");
        spin1_memcpy(input_type_array, &address[next],
                n_neurons * sizeof(input_type_t));
        next += n_words_needed(n_neurons * sizeof(input_type_t));
    }

    if (sizeof(threshold_type_t)) {
        log_debug("reading threshold type parameters");
        spin1_memcpy(threshold_type_array, &address[next],
                n_neurons * sizeof(threshold_type_t));
        next += n_words_needed(n_neurons * sizeof(threshold_type_t));
    }

    if (sizeof(synapse_param_t)) {
        log_debug("reading synapse parameters");
        spin1_memcpy(neuron_synapse_shaping_params, &address[next],
                n_neurons * sizeof(synapse_param_t));
        next += n_words_needed(n_neurons * sizeof(synapse_param_t));
    }

    if (sizeof(additional_input_t)) {
        log_debug("reading additional input type parameters");
        spin1_memcpy(additional_input_array, &address[next],
                n_neurons * sizeof(additional_input_t));
        next += n_words_needed(n_neurons * sizeof(additional_input_t));
    }

    neuron_model_set_global_neuron_params(global_parameters);

    rate_lut_size = address[next++];

    rate_lut = spin1_malloc(rate_lut_size * sizeof(REAL));
    if(rate_lut == NULL) {
        log_error("Cannot allocate space for output rate LUT");
    }

    spin1_memcpy(rate_lut, &address[next], rate_lut_size * sizeof(REAL));
    next += n_words_needed(rate_lut_size * sizeof(REAL));


    //io_printf(IO_BUF, "LUT vals:\n");
    //for(uint i = 0; i < 17; i++)
    //    io_printf(IO_BUF, "%k\n", rate_lut[i]);


#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        neuron_model_print_parameters(&neuron_array[n]);
    }
    log_debug("-------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}



// &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

// Rate Update Function

static inline REAL set_spike_source_rate(REAL somatic_voltage) {

	// Compute the rate function based on sigmoid approximation
//	if (somatic_voltage < 0.0k){
//		rate = 0.001k;
//	} else if (somatic_voltage > 2.0k) {
//		rate = 150.0k;
//	}
//	else {
//
//        // Compute the square and cube for the rate function (the values are shifted to stay on 32 bits)
//	    //REAL voltage_sq = ((somatic_voltage * somatic_voltage));
//	    //REAL voltage_cube = ((voltage_sq * somatic_voltage));
//
//	    //io_printf(IO_BUF, "sq %k, cub %k\n", voltage_sq, voltage_cube);
//
//	    //rate = ((cubic_term * voltage_cube)) +
//	    //       ((square_term * voltage_sq)) +
//	    //       ((linear_term * somatic_voltage)) +
//	    //       constant_term;
//	    rate = rate_lut[(uint32_t) (somatic_voltage << 4)];
//	}
//    } else {
//        rate = somatic_voltage > 0.0k ? somatic_voltage : 0.0k;
//    }

    return out_rate(somatic_voltage);
}
// &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&


static bool neuron_impl_do_timestep_update(index_t neuron_index,
        input_t external_bias, state_t *recorded_variable_values) {

    //io_printf(IO_BUF, "neuron index %d\n", neuron_index);
    // Get the neuron itself
    neuron_pointer_t neuron = &neuron_array[neuron_index];

    // Get the input_type parameters and voltage for this neuron
    input_type_pointer_t input_type = &input_type_array[neuron_index];

    additional_input_pointer_t additional_input =
            &additional_input_array[neuron_index];
    synapse_param_pointer_t synapse_type =
            &neuron_synapse_shaping_params[neuron_index];

    // Get the voltage
    //state_t voltage = neuron_model_get_membrane_voltage(neuron);
    state_t voltage = neuron->U_membrane;
    state_t g_som = neuron->g_som;

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

    for (int i = 0; i < NUM_EXCITATORY_RECEPTORS; i++) {
        total_exc += exc_input_values[i];
    }
    for (int i = 0; i < NUM_INHIBITORY_RECEPTORS; i++) {
        total_inh += inh_input_values[i];
    }


    // Call functions to convert exc_input and inh_input to current
    input_type_convert_excitatory_input_to_current(
            exc_input_values, input_type, g_som);
    input_type_convert_inhibitory_input_to_current(
            inh_input_values, input_type, g_som);

    external_bias += additional_input_get_input_value_as_current(
            additional_input, voltage);

    //io_printf(IO_BUF, "pre rate %k pre diff %k\n", neuron->rate_at_last_setting, neuron->rate_diff);

    //io_printf(IO_BUF, "ex %k, in %k\n", exc_input_values[2], inh_input_values[2]);

    // update neuron parameters
    state_t result = neuron_model_state_update(
            NUM_EXCITATORY_RECEPTORS, exc_input_values,
            NUM_INHIBITORY_RECEPTORS, inh_input_values,
            external_bias, neuron);

    // ************************************************************************
    // determine if a spike should occur
    // bool spike = threshold_type_is_above_threshold(result, threshold_type);
    REAL soma_voltage = result;

    // Compute rate diff
    //ONLY USE IS FOR RECORDING, BUT IT'S A USELESS OPERATION!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    REAL rate = set_spike_source_rate(soma_voltage);

    //REAL rate_diff = rate - neuron->rate_at_last_setting;

    //io_printf(IO_BUF, "curr rate %k, rate diff %k\n", rate, rate_diff);

    //neuron->rate_diff = rate_diff;

   // bool rate_updated = false;

	// Has rate changed by more than a predefined threshold since it was last
	// used to update the mean isi ticks?
	//if ((rate_diff) >= neuron->rate_update_threshold || (rate_diff) <= -neuron->rate_update_threshold){
		// then update the rate
		neuron->rate_at_last_setting = rate;

		bool rate_updated = true;
	//}
    // ************************************************************************

    // TMP test for Um
//    REAL Um = 0;
//    if((exc_input_values[2] + inh_input_values[2]) != 0)
//        Um = (exc_input_values[0] + inh_input_values[0]) / (exc_input_values[2] + inh_input_values[2]);

    // Call functions to get the input values to be recorded
    recorded_variable_values[V_RECORDING_INDEX] = neuron->U_membrane;
    recorded_variable_values[GSYN_EXCITATORY_RECORDING_INDEX] = neuron->V;
    recorded_variable_values[GSYN_INHIBITORY_RECORDING_INDEX] = neuron->rate_at_last_setting;

    //io_printf(IO_BUF, "final rate %k\n", neuron->rate_at_last_setting);

#if LOG_LEVEL >= LOG_DEBUG
    neuron_model_print_state_variables(neuron);
#endif // LOG_LEVEL >= LOG_DEBUG

    // Return the boolean to the model timestep update
    return rate_updated;
}

//! \brief stores neuron parameter back into sdram
//! \param[in] address: the address in sdram to start the store
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    log_debug("writing parameters");
    //if (global_parameters == NULL) {
    //   log_error("global parameter storage not allocated");
    //   rt_error(RTE_SWERR);
    //   return;
    //}

    if (sizeof(global_neuron_params_t)) {
        log_debug("writing neuron global parameters");
        spin1_memcpy(&address[next], global_parameters,
                sizeof(global_neuron_params_t));
        next += n_words_needed(sizeof(global_neuron_params_t));
    }

    if (sizeof(neuron_t)) {
        log_debug("writing neuron local parameters");
        spin1_memcpy(&address[next], neuron_array,
                n_neurons * sizeof(neuron_t));
        next += n_words_needed(n_neurons * sizeof(neuron_t));
    }

    if (sizeof(input_type_t)) {
        log_debug("writing input type parameters");
        spin1_memcpy(&address[next], input_type_array,
                n_neurons * sizeof(input_type_t));
        next += n_words_needed(n_neurons * sizeof(input_type_t));
    }

    if (sizeof(threshold_type_t)) {
        log_debug("writing threshold type parameters");
        spin1_memcpy(&address[next], threshold_type_array,
                n_neurons * sizeof(threshold_type_t));
        next += n_words_needed(n_neurons * sizeof(threshold_type_t));
    }

    if (sizeof(synapse_param_t)) {
        log_debug("writing synapse parameters");
        spin1_memcpy(&address[next], neuron_synapse_shaping_params,
                n_neurons * sizeof(synapse_param_t));
        next += n_words_needed(n_neurons * sizeof(synapse_param_t));
    }

    if (sizeof(additional_input_t)) {
        log_debug("writing additional input type parameters");
        spin1_memcpy(&address[next], additional_input_array,
                n_neurons * sizeof(additional_input_t));
        next += n_words_needed(n_neurons * sizeof(additional_input_t));
    }
}

//! \brief Returns the difference between the last updated value of rate and the previous one
//! \param[in] neuron_index: the index of the neuron
static inline uint neuron_impl_get_v(index_t neuron_index) {

    union {
        REAL input;
        uint output;
    } converter;

    converter.input = (neuron_array[neuron_index].U_membrane  + 0.5k);

    //io_printf(IO_BUF, "returning %k conv %k\n", neuron_array[neuron_index].rate_at_last_setting, converter.output);

    return converter.output;
}

//! \brief Returns the starting rate
//! \param[in] neuron_index: the index of the neuron
uint32_t neuron_impl_get_starting_rate() {

    //io_printf(IO_BUF, "returning %k\n", neuron_array[0].rate_at_last_setting);

    return neuron_array[0].rate_at_last_setting;;
}

static inline void neuron_impl_process_post_synaptic_event(index_t neuron_index) {

    neuron_pointer_t neuron = &neuron_array[neuron_index];
    
    post_events_update(&postsynaptic_rates[neuron_index],
        set_spike_source_rate(neuron->U_membrane * neuron->plasticity_rate_multiplier) -
        set_spike_source_rate(neuron->V));

}

static inline void neuron_impl_send_postsynaptic_buffer(uint32_t n_neurons) {

    spin1_dma_transfer(
        DMA_TAG_WRITE_POSTSYNAPTIC_BUFFER, postsynaptic_buffer, postsynaptic_rates,
        DMA_WRITE, n_neurons * sizeof(post_event_history_t));

    generate_background_activity(n_neurons);
}

static void neuron_impl_allocate_postsynaptic_region(uint tag, uint n_neurons) {

    postsynaptic_buffer = 
        (post_event_history_t *) sark_xalloc(
            sv->sdram_heap, n_neurons * sizeof(post_event_history_t), tag, 1);
}

#if LOG_LEVEL >= LOG_DEBUG
void neuron_impl_print_inputs(uint32_t n_neurons) {
	bool empty = true;
	for (index_t i = 0; i < n_neurons; i++) {
		empty = empty && (0 == bitsk(
		        synapse_types_get_excitatory_input(&neuron_synapse_shaping_params[i])
		        - synapse_types_get_inhibitory_input(&neuron_synapse_shaping_params[i])));
	}

	if (!empty) {
		log_debug("-------------------------------------\n");

		for (index_t i = 0; i < n_neurons; i++) {
			input_t input =
			        synapse_types_get_excitatory_input(&neuron_synapse_shaping_params[i])
			        - synapse_types_get_inhibitory_input(&neuron_synapse_shaping_params[i]);
			if (bitsk(input) != 0) {
				log_debug("%3u: %12.6k (= ", i, input);
				synapse_types_print_input(&neuron_synapse_shaping_params[i]);
				log_debug(")\n");
			}
		}
		log_debug("-------------------------------------\n");
	}
}

void neuron_impl_print_synapse_parameters(uint32_t n_neurons) {
	log_debug("-------------------------------------\n");
	for (index_t n = 0; n < n_neurons; n++) {
	    synapse_types_print_parameters(&neuron_synapse_shaping_params[n]);
	}
	log_debug("-------------------------------------\n");
}

const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
	return synapse_types_get_type_char(synapse_type);
}

#endif // LOG_LEVEL >= LOG_DEBUG

#endif // _NEURON_IMPL_STANDARD_H_
