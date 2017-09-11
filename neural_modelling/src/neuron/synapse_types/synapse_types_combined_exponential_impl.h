/*! \file
 * \brief implementation of synapse_types.h for a synapse behaviour
 *  calculated as the difference between two exponential functions
 */

#ifndef _DIFF_SYNAPSE_H_
#define _DIFF_SYNAPSE_H_

#include "../decay.h"
#include <debug.h>

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 1
#define SYNAPSE_TYPE_COUNT 2
#define SYNAPSE_INDEX_BITS 8

//---------------------------------------
// Synapse parameters
//---------------------------------------
typedef struct synapse_param_t {
	input_t exc_a_response;
	input_t exc_a_A;
	decay_t exc_a_decay;
	decay_t exc_a_init;
	input_t exc_b_response;
	input_t exc_b_B;
	decay_t exc_b_decay;
	decay_t exc_b_init;

	input_t inh_a_response;
	input_t inh_a_A;
	decay_t inh_a_decay;
	decay_t inh_a_init;
	input_t inh_b_response;
	input_t inh_b_B;
	decay_t inh_b_decay;
	decay_t inh_b_init;

} synapse_param_t;

#include "synapse_types.h"

//! human readable definition for the positions in the input regions for the
//! different synapse types.
typedef enum input_buffer_regions {
	EXCITATORY, INHIBITORY,
} input_buffer_regions;


static inline void synapse_types_shape_input(synapse_param_pointer_t parameter){
	// Excitatory
	parameter->exc_a_response = decay_s1615(
			parameter->exc_a_response,
			parameter->exc_a_decay);

	parameter->exc_b_response =  decay_s1615(
			parameter->exc_b_response,
			parameter->exc_b_decay);

	// Inhibitory
	parameter->inh_a_response = decay_s1615(
			parameter->inh_a_response,
			parameter->inh_a_decay);

	parameter->inh_b_response = decay_s1615(
			parameter->inh_b_response,
			parameter->inh_b_decay);
}

static inline void synapse_types_add_neuron_input(
		index_t synapse_type_index,
		synapse_param_pointer_t parameter,
        input_t input){

	if (synapse_type_index == EXCITATORY) {

		parameter->exc_a_response = parameter->exc_a_response + input;
				/*
				 parameter->exc_a_response +
				decay_s1615(input,
				parameter->exc_a_decay);
				*/

		parameter->exc_b_response = parameter->exc_b_response + input;
				/*
				 parameter->exc_b_response +
				decay_s1615(input,
				parameter->exc_b_decay);
				*/

	} else if (synapse_type_index == INHIBITORY) {

		parameter->inh_a_response = parameter->inh_a_response + input;
				/*
				parameter->inh_a_response +
				decay_s1615(input,
				parameter->inh_a_decay);
				*/
		parameter->inh_b_response = parameter->inh_b_response + input;
				/*
				parameter->inh_b_response +
				decay_s1615(input,
				parameter->inh_b_decay);
				*/
	}
}

static inline input_t synapse_types_get_excitatory_input(
		synapse_param_pointer_t parameter) {
	//log_info("%11.6k,  %11.6k, %11.6k, %11.6k", parameter->exc_a_decay, parameter->exc_a_response, parameter->exc_b_decay, parameter->exc_b_response);
	return (parameter->exc_a_A * parameter->exc_a_response) + (parameter->exc_b_B * parameter->exc_b_response);
}

static inline input_t synapse_types_get_inhibitory_input(
		synapse_param_pointer_t parameter) {
	return (parameter->inh_a_A * parameter->inh_a_response) + (parameter->inh_b_B * parameter->inh_b_response);
}

static inline const char *synapse_types_get_type_char(
		index_t synapse_type_index) {
	if (synapse_type_index == EXCITATORY) {
		return "X";
	} else if (synapse_type_index == INHIBITORY) {
		return "I";
	} else {
		log_debug("did not recognise synapse type %i", synapse_type_index);
		return "?";
	}
}

static inline void synapse_types_print_input(
        synapse_param_pointer_t parameter) {
    io_printf(
        IO_BUF, "%12.6k + %12.6k - %12.6k",
        parameter->exc_a_response,
        parameter->exc_b_response,
        parameter->inh_a_response,
        parameter->inh_b_response);
}

static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
    log_info("-------------------------------------\n");
	log_info("exc_a_decay  = %11.4k\n", parameter->exc_a_decay);
	log_info("exc_a_init   = %11.4k\n", parameter->exc_a_init);
	log_info("exc_a_response  = %11.4k\n", parameter->exc_a_response);
	log_info("exc_b_decay = %11.4k\n", parameter->exc_b_decay);
	log_info("exc_b_init  = %11.4k\n", parameter->exc_b_init);
	log_info("exc_b_response  = %11.4k\n", parameter->exc_b_response);
	log_info("inh_a_decay  = %11.4k\n", parameter->inh_a_decay);
	log_info("inh_a_init   = %11.4k\n", parameter->inh_a_init);
	log_info("inh_a_response  = %11.4k\n", parameter->inh_a_response);
	log_info("inh_b_decay = %11.4k\n", parameter->inh_b_decay);
	log_info("inh_b_init  = %11.4k\n", parameter->inh_b_init);
	log_info("inh_b_response  = %11.4k\n", parameter->inh_b_response);
}

#endif // _DIFF_SYNAPSE_H_

