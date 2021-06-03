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
#define SYNAPSE_TYPE_BITS 2
#define SYNAPSE_TYPE_COUNT 4
//#define SYNAPSE_INDEX_BITS 5   // Was 6

#define NUM_EXCITATORY_RECEPTORS 2
#define NUM_INHIBITORY_RECEPTORS 2

 //---------------------------------------
 // Synapse parameters
 //---------------------------------------

input_t excitatory_response[NUM_EXCITATORY_RECEPTORS];
input_t inhibitory_response[NUM_INHIBITORY_RECEPTORS];

typedef struct bi_exp_params{
 	input_t exc_a_response;
 	input_t exc_a_A;
 	decay_t exc_a_decay;
 	decay_t exc_a_init;
 	input_t exc_b_response;
 	input_t exc_b_B;
 	decay_t exc_b_decay;
 	decay_t exc_b_init;
}bi_exp_params;


 typedef struct synapse_param_t {
	// excitatory
 	input_t exc_a_response;
 	input_t exc_a_A;
 	decay_t exc_a_decay;
 	decay_t exc_a_init;
 	input_t exc_b_response;
 	input_t exc_b_B;
 	decay_t exc_b_decay;
 	decay_t exc_b_init;

 	// excitatory2
 	input_t exc2_a_response;
 	input_t exc2_a_A;
 	decay_t exc2_a_decay;
 	decay_t exc2_a_init;
 	input_t exc2_b_response;
 	input_t exc2_b_B;
 	decay_t exc2_b_decay;
 	decay_t exc2_b_init;

 	// inhibitory
 	input_t inh_a_response;
 	input_t inh_a_A;
 	decay_t inh_a_decay;
 	decay_t inh_a_init;
 	input_t inh_b_response;
 	input_t inh_b_B;
 	decay_t inh_b_decay;
 	decay_t inh_b_init;

 	// inhibitory2
 	input_t inh2_a_response;
 	input_t inh2_a_A;
 	decay_t inh2_a_decay;
 	decay_t inh2_a_init;
 	input_t inh2_b_response;
 	input_t inh2_b_B;
 	decay_t inh2_b_decay;
 	decay_t inh2_b_init;

 } synapse_param_t;

#include "synapse_types.h"

 //! human readable definition for the positions in the input regions for the
 //! different synapse types.
 typedef enum input_buffer_regions {
 	EXCITATORY, EXCITATORY2, INHIBITORY, INHIBITORY2,
 } input_buffer_regions;

 static inline void synapse_types_shape_input(synapse_param_pointer_t parameter){
 	// EXCITATORY
 	parameter->exc_a_response = decay_s1615(
 			parameter->exc_a_response,
 			parameter->exc_a_decay);

 	parameter->exc_b_response =  decay_s1615(
 			parameter->exc_b_response,
 			parameter->exc_b_decay);

 	// EXCITATORY2
 	parameter->exc2_a_response = 0; // make this (the Teacher) a Delta synapse
//	= decay_s1615(
// 			parameter->exc2_a_response,
// 			parameter->exc2_a_decay);
//
// 	parameter->exc2_b_response =  decay_s1615(
// 			parameter->exc2_b_response,
// 			parameter->exc2_b_decay);

 	// INHIBITORY
 	parameter->inh_a_response = decay_s1615(
 			parameter->inh_a_response,
 			parameter->inh_a_decay);

 	parameter->inh_b_response = decay_s1615(
 			parameter->inh_b_response,
 			parameter->inh_b_decay);

 	// INHIBITORY2
 	parameter->inh2_a_response = decay_s1615(
 			parameter->inh2_a_response,
 			parameter->inh2_a_decay);

 	parameter->inh2_b_response = decay_s1615(
 			parameter->inh2_b_response,
 			parameter->inh2_b_decay);

 	log_debug("ex1 = %8.4k, ex2 = %8.4k, inh = %8.4k, inh2 = %8.4k",
 			((parameter->exc_a_A * parameter->exc_a_response) + (parameter->exc_b_B * parameter->exc_b_response)),
 			((parameter->exc2_a_A * parameter->exc2_a_response) + (parameter->exc2_b_B * parameter->exc2_b_response)),
 			((parameter->inh_a_A * parameter->inh_a_response) + (parameter->inh_b_B * parameter->inh_b_response)),
 			((parameter->inh2_a_A * parameter->inh2_a_response) + (parameter->inh2_b_B * parameter->inh2_b_response))
			);

 }

 static inline void synapse_types_add_neuron_input(
 		index_t synapse_type_index,
 		synapse_param_pointer_t parameter,
         input_t input){

 	if (synapse_type_index == EXCITATORY) {
                //log_info("ip: %5.6k", input);

 		parameter->exc_a_response =  parameter->exc_a_response + input;
 				/*
 				decay_s1615(input,
 				parameter->exc_a_init);
				*/

 		parameter->exc_b_response = parameter->exc_b_response + input;
 				/*
				decay_s1615(input,
 				parameter->exc_b_init);
				*/

 	} else if (synapse_type_index == EXCITATORY2) {

 		parameter->exc2_a_response = input; // Add input to delta (Teacher) synapse
 				/*
 				decay_s1615(input,
 				parameter->exc2_a_init);
				*/

// 		parameter->exc2_b_response = parameter->exc2_b_response + input;
 				/*
 				decay_s1615(input,
 				parameter->exc2_b_init);
				*/

 	} else if (synapse_type_index == INHIBITORY) {

 		parameter->inh_a_response =  parameter->inh_a_response + input;
 				/*
 				decay_s1615(input,
 				parameter->inh_a_init);
				*/

 		parameter->inh_b_response = parameter->inh_b_response + input;
 				/*
 				decay_s1615(input,
 				parameter->inh_b_init);
				*/

 	} else if (synapse_type_index == INHIBITORY2) {

 		parameter->inh2_a_response =  parameter->inh2_a_response + input;
 				/*
				decay_s1615(input,
 				parameter->inh2_a_init);
				*/

 		parameter->inh2_b_response = parameter->inh2_b_response + input;
 				/*
				decay_s1615(input,
 				parameter->inh2_b_init);
				*/
 	}
 }

 static inline input_t* synapse_types_get_excitatory_input(
 		synapse_param_pointer_t parameter) {
	 excitatory_response[0] = (parameter->exc_a_A * parameter->exc_a_response) +
			 (parameter->exc_b_B * parameter->exc_b_response);
	 excitatory_response[1] = parameter->exc2_a_response;
//			 (parameter->exc2_a_A * parameter->exc2_a_response) +
//			 (parameter->exc2_b_B * parameter->exc2_b_response);

	 return &excitatory_response[0];
 }

 static inline input_t* synapse_types_get_inhibitory_input(
 		synapse_param_pointer_t parameter) {
	 inhibitory_response[0] = (parameter->inh_a_A * parameter->inh_a_response) +
			 	 (parameter->inh_b_B * parameter->inh_b_response);
	 inhibitory_response[1] = (parameter->inh2_a_A * parameter->inh2_a_response) +
	 	 	 	 (parameter->inh2_b_B * parameter->inh2_b_response);
 	 return &inhibitory_response[0];
 }

 static inline const char *synapse_types_get_type_char(
 		index_t synapse_type_index) {
 	if (synapse_type_index == EXCITATORY) {
 		return "X";
 	}else if (synapse_type_index == EXCITATORY2) {
 		return "X2";
 	}else if (synapse_type_index == INHIBITORY) {
 		return "I";
 	} else if (synapse_type_index == INHIBITORY2) {
 		return "I2";
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
         parameter->exc2_a_response,
         parameter->exc2_b_response,
         parameter->inh_a_response,
         parameter->inh_b_response,
         parameter->inh2_a_response,
         parameter->inh2_b_response);
 }

 static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
    log_debug("-------------------------------------\n");

 	log_debug("exc_a_decay  = %11.4k\n", parameter->exc_a_decay);
 	log_debug("exc_a_init   = %11.4k\n", parameter->exc_a_init);
 	log_debug("exc_a_response  = %11.4k\n", parameter->exc_a_response);
 	log_debug("exc_b_decay = %11.4k\n", parameter->exc_b_decay);
 	log_debug("exc_b_init  = %11.4k\n", parameter->exc_b_init);
 	log_debug("exc_b_response  = %11.4k\n", parameter->exc_b_response);

 	log_debug("exc2_a_decay  = %11.4k\n", parameter->exc2_a_decay);
 	log_debug("exc2_a_init   = %11.4k\n", parameter->exc2_a_init);
 	log_debug("exc2_a_response  = %11.4k\n", parameter->exc2_a_response);
 	log_debug("exc2_b_decay = %11.4k\n", parameter->exc2_b_decay);
 	log_debug("exc2_b_init  = %11.4k\n", parameter->exc2_b_init);
 	log_debug("exc2_b_response  = %11.4k\n", parameter->exc2_b_response);

 	log_debug("inh_a_decay  = %11.4k\n", parameter->inh_a_decay);
 	log_debug("inh_a_init   = %11.4k\n", parameter->inh_a_init);
 	log_debug("inh_a_response  = %11.4k\n", parameter->inh_a_response);
 	log_debug("inh_b_decay = %11.4k\n", parameter->inh_b_decay);
 	log_debug("inh_b_init  = %11.4k\n", parameter->inh_b_init);
 	log_debug("inh_b_response  = %11.4k\n", parameter->inh_b_response);

 	log_debug("inh2_a_decay  = %11.4k\n", parameter->inh2_a_decay);
 	log_debug("inh2_a_init   = %11.4k\n", parameter->inh2_a_init);
 	log_debug("inh2_a_response  = %11.4k\n", parameter->inh2_a_response);
 	log_debug("inh2_b_decay = %11.4k\n", parameter->inh2_b_decay);
 	log_debug("inh2_b_init  = %11.4k\n", parameter->inh2_b_init);
 	log_debug("inh2_b_response  = %11.4k\n", parameter->inh2_b_response);
 }


 static inline void flush_synaptic_input(synapse_param_pointer_t parameter){
	 parameter->exc_a_response =  0.0k;
	 parameter->exc_b_response = 0.0k;
 }

 #endif // _DIFF_SYNAPSE_H_

