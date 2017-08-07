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
#define SYNAPSE_TYPE_BITS 4
#define SYNAPSE_TYPE_COUNT 14
#define SYNAPSE_INDEX_BITS 6

 //---------------------------------------
 // Synapse parameters
 //---------------------------------------
 typedef struct synapse_param_t {
	// excitatory
	// input_t exc_response;
 	input_t exc_a_response;
 	input_t exc_a_A;
 	decay_t exc_a_decay;
 	input_t exc_b_response;
 	input_t exc_b_B;
 	decay_t exc_b_decay;

 	// excitatory2
 	// input_t exc2_response;
 	input_t exc2_a_response;
 	input_t exc2_a_A;
 	decay_t exc2_a_decay;
 	input_t exc2_b_response;
 	input_t exc2_b_B;
 	decay_t exc2_b_decay;

 	// excitatory3
 	// input_t exc3_response;
 	input_t exc3_a_response;
 	input_t exc3_a_A;
 	decay_t exc3_a_decay;
 	input_t exc3_b_response;
 	input_t exc3_b_B;
 	decay_t exc3_b_decay;

 	// excitatory2
 	// input_t exc4_response;
 	input_t exc4_a_response;
 	input_t exc4_a_A;
 	decay_t exc4_a_decay;
 	input_t exc4_b_response;
 	input_t exc4_b_B;
 	decay_t exc4_b_decay;

 	// excitatory5
 	// input_t exc5_response;
 	input_t exc5_a_response;
 	input_t exc5_a_A;
 	decay_t exc5_a_decay;
 	input_t exc5_b_response;
 	input_t exc5_b_B;
 	decay_t exc5_b_decay;

 	// excitatory5
 	// input_t exc6_response;
 	input_t exc6_a_response;
 	input_t exc6_a_A;
 	decay_t exc6_a_decay;
 	input_t exc6_b_response;
 	input_t exc6_b_B;
 	decay_t exc6_b_decay;

 	// excitatory7
 	// input_t exc7_response;
 	input_t exc7_a_response;
 	input_t exc7_a_A;
 	decay_t exc7_a_decay;
 	input_t exc7_b_response;
 	input_t exc7_b_B;
 	decay_t exc7_b_decay;

 	// inhibitory
 	// input_t inh_response;
 	input_t inh_a_response;
 	input_t inh_a_A;
 	decay_t inh_a_decay;
 	input_t inh_b_response;
 	input_t inh_b_B;
 	decay_t inh_b_decay;

 	// inhibitory2
 	// input_t inh2_response;
 	input_t inh2_a_response;
 	input_t inh2_a_A;
 	decay_t inh2_a_decay;
 	input_t inh2_b_response;
 	input_t inh2_b_B;
 	decay_t inh2_b_decay;

 	// inhibitory3
 	// input_t inh3_response;
 	input_t inh3_a_response;
 	input_t inh3_a_A;
 	decay_t inh3_a_decay;
 	input_t inh3_b_response;
 	input_t inh3_b_B;
 	decay_t inh3_b_decay;

 	// inhibitory4
 	// input_t inh4_response;
 	input_t inh4_a_response;
 	input_t inh4_a_A;
 	decay_t inh4_a_decay;
 	input_t inh4_b_response;
 	input_t inh4_b_B;
 	decay_t inh4_b_decay;

 	// inhibitory5
 	// input_t inh5_response;
 	input_t inh5_a_response;
 	input_t inh5_a_A;
 	decay_t inh5_a_decay;
 	input_t inh5_b_response;
 	input_t inh5_b_B;
 	decay_t inh5_b_decay;

 	// inhibitory6
 	// input_t inh6_response;
 	input_t inh6_a_response;
 	input_t inh6_a_A;
 	decay_t inh6_a_decay;
 	input_t inh6_b_response;
 	input_t inh6_b_B;
 	decay_t inh6_b_decay;

 	// inhibitory7
 	// input_t inh7_response;
 	input_t inh7_a_response;
 	input_t inh7_a_A;
 	decay_t inh7_a_decay;
 	input_t inh7_b_response;
 	input_t inh7_b_B;
 	decay_t inh7_b_decay;

 } synapse_param_t;

#include "synapse_types.h"

 //! human readable definition for the positions in the input regions for the
 //! different synapse types.
 typedef enum input_buffer_regions {
 	EXCITATORY, EXCITATORY2, EXCITATORY3, EXCITATORY4, EXCITATORY5, EXCITATORY6, EXCITATORY7, INHIBITORY, INHIBITORY2, INHIBITORY3, INHIBITORY4, INHIBITORY5, INHIBITORY6, INHIBITORY7,
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
 	parameter->exc2_a_response = decay_s1615(
 			parameter->exc2_a_response,
 			parameter->exc2_a_decay);

 	parameter->exc2_b_response =  decay_s1615(
 			parameter->exc2_b_response,
 			parameter->exc2_b_decay);

 	// EXCITATORY3
 	parameter->exc3_a_response = decay_s1615(
 			parameter->exc3_a_response,
 			parameter->exc3_a_decay);

 	parameter->exc3_b_response =  decay_s1615(
 			parameter->exc3_b_response,
 			parameter->exc3_b_decay);

 	// EXCITATORY4
 	parameter->exc4_a_response = decay_s1615(
 			parameter->exc4_a_response,
 			parameter->exc4_a_decay);

 	parameter->exc4_b_response =  decay_s1615(
 			parameter->exc4_b_response,
 			parameter->exc4_b_decay);

 	// EXCITATORY5
 	parameter->exc5_a_response = decay_s1615(
 			parameter->exc5_a_response,
 			parameter->exc5_a_decay);

 	parameter->exc5_b_response =  decay_s1615(
 			parameter->exc5_b_response,
 			parameter->exc5_b_decay);

 	// EXCITATORY6
 	parameter->exc6_a_response = decay_s1615(
 			parameter->exc6_a_response,
 			parameter->exc6_a_decay);

 	parameter->exc6_b_response =  decay_s1615(
 			parameter->exc6_b_response,
 			parameter->exc6_b_decay);

 	// EXCITATORY7
 	parameter->exc7_a_response = decay_s1615(
 			parameter->exc7_a_response,
 			parameter->exc7_a_decay);

 	parameter->exc7_b_response =  decay_s1615(
 			parameter->exc7_b_response,
 			parameter->exc7_b_decay);

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

 	// INHIBITORY3
 	parameter->inh3_a_response = decay_s1615(
 			parameter->inh3_a_response,
 			parameter->inh3_a_decay);

 	parameter->inh3_b_response = decay_s1615(
 			parameter->inh3_b_response,
 			parameter->inh3_b_decay);

 	// INHIBITORY4
 	parameter->inh4_a_response = decay_s1615(
 			parameter->inh4_a_response,
 			parameter->inh4_a_decay);

 	parameter->inh4_b_response = decay_s1615(
 			parameter->inh4_b_response,
 			parameter->inh4_b_decay);

 	// INHIBITORY5
 	parameter->inh5_a_response = decay_s1615(
 			parameter->inh5_a_response,
 			parameter->inh5_a_decay);

 	parameter->inh5_b_response = decay_s1615(
 			parameter->inh5_b_response,
 			parameter->inh5_b_decay);

 	// INHIBITORY6
 	parameter->inh6_a_response = decay_s1615(
 			parameter->inh6_a_response,
 			parameter->inh6_a_decay);

 	parameter->inh6_b_response = decay_s1615(
 			parameter->inh6_b_response,
 			parameter->inh6_b_decay);

 	// INHIBITORY7
 	parameter->inh7_a_response = decay_s1615(
 			parameter->inh7_a_response,
 			parameter->inh7_a_decay);

 	parameter->inh7_b_response = decay_s1615(
 			parameter->inh7_b_response,
 			parameter->inh7_b_decay);
 }

 static inline void synapse_types_add_neuron_input(
 		index_t synapse_type_index,
 		synapse_param_pointer_t parameter,
         input_t input){

 	if (synapse_type_index == EXCITATORY) {

 		parameter->exc_a_response =  parameter->exc_a_response +
 				decay_s1615(input,
 				parameter->exc_a_decay);


 		parameter->exc_b_response = parameter->exc_b_response +
 				decay_s1615(input,
 				parameter->exc_b_decay);

 		// parameter->exc_response = (parameter->exc_a_A * parameter->exc_a_response) + (parameter->exc_b_B * parameter->exc_b_response);

 	} else if (synapse_type_index == EXCITATORY2) {

 		parameter->exc2_a_response =  parameter->exc2_a_response +
 				decay_s1615(input,
 				parameter->exc2_a_decay);


 		parameter->exc2_b_response = parameter->exc2_b_response +
 				decay_s1615(input,
 				parameter->exc2_b_decay);

 		// parameter->exc2_response = (parameter->exc2_a_A * parameter->exc2_a_response) + (parameter->exc2_b_B * parameter->exc2_b_response);

 	} else if (synapse_type_index == EXCITATORY3) {

 		parameter->exc3_a_response =  parameter->exc3_a_response +
 				decay_s1615(input,
 				parameter->exc3_a_decay);


 		parameter->exc3_b_response = parameter->exc3_b_response +
 				decay_s1615(input,
 				parameter->exc3_b_decay);

 		// parameter->exc3_response = (parameter->exc3_a_A * parameter->exc3_a_response) + (parameter->exc3_b_B * parameter->exc3_b_response);

 	} else if (synapse_type_index == EXCITATORY4) {

 		parameter->exc4_a_response =  parameter->exc4_a_response +
 				decay_s1615(input,
 				parameter->exc4_a_decay);


 		parameter->exc4_b_response = parameter->exc4_b_response +
 				decay_s1615(input,
 				parameter->exc4_b_decay);

 		// parameter->exc4_response = (parameter->exc4_a_A * parameter->exc4_a_response) + (parameter->exc4_b_B * parameter->exc4_b_response);

 	} else if (synapse_type_index == EXCITATORY5) {

 		parameter->exc5_a_response =  parameter->exc5_a_response +
 				decay_s1615(input,
 				parameter->exc5_a_decay);


 		parameter->exc5_b_response = parameter->exc5_b_response +
 				decay_s1615(input,
 				parameter->exc5_b_decay);

 		// parameter->exc5_response = (parameter->exc5_a_A * parameter->exc5_a_response) + (parameter->exc5_b_B * parameter->exc5_b_response);
 	} else if (synapse_type_index == EXCITATORY6) {

 		parameter->exc6_a_response =  parameter->exc6_a_response +
 				decay_s1615(input,
 				parameter->exc6_a_decay);


 		parameter->exc6_b_response = parameter->exc6_b_response +
 				decay_s1615(input,
 				parameter->exc6_b_decay);

 		// parameter->exc6_response = (parameter->exc6_a_A * parameter->exc6_a_response) + (parameter->exc6_b_B * parameter->exc6_b_response);
 	} else if (synapse_type_index == EXCITATORY7) {

 		parameter->exc7_a_response =  parameter->exc7_a_response +
 				decay_s1615(input,
 				parameter->exc7_a_decay);


 		parameter->exc7_b_response = parameter->exc7_b_response +
 				decay_s1615(input,
 				parameter->exc7_b_decay);

 		// parameter->exc7_response = (parameter->exc7_a_A * parameter->exc7_a_response) + (parameter->exc7_b_B * parameter->exc7_b_response);

 	} else if (synapse_type_index == INHIBITORY) {

 		parameter->inh_a_response =  parameter->inh_a_response +
 				decay_s1615(input,
 				parameter->inh_a_decay);

 		parameter->inh_b_response = parameter->inh_b_response +
 				decay_s1615(input,
 				parameter->inh_b_decay);

 		// parameter->inh_response = (parameter->inh_a_A * parameter->inh_a_response) + (parameter->inh_b_B * parameter->inh_b_response);

 	} else if (synapse_type_index == INHIBITORY2) {

 		parameter->inh2_a_response =  parameter->inh2_a_response +
 				decay_s1615(input,
 				parameter->inh2_a_decay);

 		parameter->inh2_b_response = parameter->inh2_b_response +
 				decay_s1615(input,
 				parameter->inh2_b_decay);

 		// parameter->inh2_response = (parameter->inh2_a_A * parameter->inh2_a_response) + (parameter->inh2_b_B * parameter->inh2_b_response);

 	} else if (synapse_type_index == INHIBITORY3) {

 		parameter->inh3_a_response =  parameter->inh3_a_response +
 				decay_s1615(input,
 				parameter->inh3_a_decay);

 		parameter->inh3_b_response = parameter->inh3_b_response +
 				decay_s1615(input,
 				parameter->inh3_b_decay);

 		// parameter->inh3_response = (parameter->inh3_a_A * parameter->inh3_a_response) + (parameter->inh3_b_B * parameter->inh3_b_response);

 	} else if (synapse_type_index == INHIBITORY4) {

 		parameter->inh4_a_response =  parameter->inh4_a_response +
 				decay_s1615(input,
 				parameter->inh4_a_decay);

 		parameter->inh4_b_response = parameter->inh4_b_response +
 				decay_s1615(input,
 				parameter->inh4_b_decay);

 		// parameter->inh4_response = (parameter->inh4_a_A * parameter->inh4_a_response) + (parameter->inh4_b_B * parameter->inh4_b_response);

 	} else if (synapse_type_index == INHIBITORY5) {

 		parameter->inh5_a_response =  parameter->inh5_a_response +
 				decay_s1615(input,
 				parameter->inh5_a_decay);

 		parameter->inh5_b_response = parameter->inh5_b_response +
 				decay_s1615(input,
 				parameter->inh5_b_decay);

 		// parameter->inh5_response = (parameter->inh5_a_A * parameter->inh5_a_response) + (parameter->inh5_b_B * parameter->inh5_b_response);
 	} else if (synapse_type_index == INHIBITORY6) {

 		parameter->inh6_a_response =  parameter->inh6_a_response +
 				decay_s1615(input,
 				parameter->inh6_a_decay);

 		parameter->inh6_b_response = parameter->inh6_b_response +
 				decay_s1615(input,
 				parameter->inh6_b_decay);

 		// parameter->inh6_response = (parameter->inh6_a_A * parameter->inh6_a_response) + (parameter->inh6_b_B * parameter->inh6_b_response);
 	} else if (synapse_type_index == INHIBITORY7) {

 		parameter->inh7_a_response =  parameter->inh7_a_response +
 				decay_s1615(input,
 				parameter->inh7_a_decay);

 		parameter->inh7_b_response = parameter->inh7_b_response +
 				decay_s1615(input,
 				parameter->inh7_b_decay);

 		// parameter->inh7_response = (parameter->inh7_a_A * parameter->inh7_a_response) + (parameter->inh7_b_B * parameter->inh7_b_response);
 	}
 }

 static inline input_t synapse_types_get_excitatory_input(
 		synapse_param_pointer_t parameter) {
	 return ((parameter->exc_a_A * parameter->exc_a_response) + (parameter->exc_b_B * parameter->exc_b_response))
			 + ((parameter->exc2_a_A * parameter->exc2_a_response) + (parameter->exc2_b_B * parameter->exc2_b_response))
			 + ((parameter->exc3_a_A * parameter->exc3_a_response) + (parameter->exc3_b_B * parameter->exc3_b_response))
			 + ((parameter->exc4_a_A * parameter->exc4_a_response) + (parameter->exc4_b_B * parameter->exc4_b_response))
			 + ((parameter->exc5_a_A * parameter->exc5_a_response) + (parameter->exc5_b_B * parameter->exc5_b_response))
			 + ((parameter->exc6_a_A * parameter->exc6_a_response) + (parameter->exc6_b_B * parameter->exc6_b_response))
			 + ((parameter->exc7_a_A * parameter->exc7_a_response) + (parameter->exc7_b_B * parameter->exc7_b_response));
 }

 static inline input_t synapse_types_get_inhibitory_input(
 		synapse_param_pointer_t parameter) {
	 return ((parameter->inh_a_A * parameter->inh_a_response) + (parameter->inh_b_B * parameter->inh_b_response))
			+ ((parameter->inh2_a_A * parameter->inh2_a_response) + (parameter->inh2_b_B * parameter->inh2_b_response))
			+ ((parameter->inh3_a_A * parameter->inh3_a_response) + (parameter->inh3_b_B * parameter->inh3_b_response))
			+ ((parameter->inh4_a_A * parameter->inh4_a_response) + (parameter->inh4_b_B * parameter->inh4_b_response))
			+ ((parameter->inh5_a_A * parameter->inh5_a_response) + (parameter->inh5_b_B * parameter->inh5_b_response))
			+ ((parameter->inh6_a_A * parameter->inh6_a_response) + (parameter->inh6_b_B * parameter->inh6_b_response))
			+ ((parameter->inh7_a_A * parameter->inh7_a_response) + (parameter->inh7_b_B * parameter->inh7_b_response));
 }

 static inline const char *synapse_types_get_type_char(
 		index_t synapse_type_index) {
 	if (synapse_type_index == EXCITATORY) {
 		return "X";
 	}else if (synapse_type_index == EXCITATORY2) {
 		return "X2";
 	}else if (synapse_type_index == EXCITATORY3) {
 		return "X3";
 	}else if (synapse_type_index == EXCITATORY4) {
 		return "X4";
 	}else if (synapse_type_index == EXCITATORY5) {
 		return "X5";
 	}else if (synapse_type_index == EXCITATORY6) {
 		return "X6";
 	}else if (synapse_type_index == EXCITATORY7) {
 		return "X7";
 	}else if (synapse_type_index == INHIBITORY) {
 		return "I";
 	} else if (synapse_type_index == INHIBITORY2) {
 		return "I2";
 	} else if (synapse_type_index == INHIBITORY3) {
 		return "I3";
 	} else if (synapse_type_index == INHIBITORY4) {
 		return "I4";
 	} else if (synapse_type_index == INHIBITORY5) {
 		return "I5";
 	} else if (synapse_type_index == INHIBITORY6) {
 		return "I6";
 	} else if (synapse_type_index == INHIBITORY7) {
 		return "I7";
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

         parameter->exc3_a_response,
         parameter->exc3_b_response,

         parameter->exc4_a_response,
         parameter->exc4_b_response,

         parameter->exc5_a_response,
         parameter->exc5_b_response,

		 parameter->exc6_a_response,
         parameter->exc6_b_response,

		 parameter->exc7_a_response,
         parameter->exc7_b_response,

         parameter->inh_a_response,
         parameter->inh_b_response,

         parameter->inh2_a_response,
         parameter->inh2_b_response,

         parameter->inh3_a_response,
         parameter->inh3_b_response,

         parameter->inh4_a_response,
         parameter->inh4_b_response,

         parameter->inh5_a_response,
         parameter->inh5_b_response,

		 parameter->inh6_a_response,
         parameter->inh6_b_response,

         parameter->inh7_a_response,
         parameter->inh7_b_response);
 }

 static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
 /*   log_info("-------------------------------------\n");

    log_info("exc_response  = %11.4k\n", parameter->exc_response);
 	log_info("exc_a_decay  = %11.4k\n", parameter->exc_a_decay);
 	log_info("exc_a_response  = %11.4k\n", parameter->exc_a_response);
 	log_info("exc_b_decay = %11.4k\n", parameter->exc_b_decay);
 	log_info("exc_b_response  = %11.4k\n", parameter->exc_b_response);

 	log_info("exc2_response  = %11.4k\n", parameter->exc2_response);
 	log_info("exc2_a_decay  = %11.4k\n", parameter->exc2_a_decay);
 	log_info("exc2_a_response  = %11.4k\n", parameter->exc2_a_response);
 	log_info("exc2_b_decay = %11.4k\n", parameter->exc2_b_decay);
 	log_info("exc2_b_response  = %11.4k\n", parameter->exc2_b_response);

 	log_info("exc3_response  = %11.4k\n", parameter->exc3_response);
 	log_info("exc3_a_decay  = %11.4k\n", parameter->exc3_a_decay);
 	log_info("exc3_a_response  = %11.4k\n", parameter->exc3_a_response);
 	log_info("exc3_b_decay = %11.4k\n", parameter->exc3_b_decay);
 	log_info("exc3_b_response  = %11.4k\n", parameter->exc3_b_response);

 	log_info("exc4_response  = %11.4k\n", parameter->exc4_response);
 	log_info("exc4_a_decay  = %11.4k\n", parameter->exc4_a_decay);
 	log_info("exc4_a_response  = %11.4k\n", parameter->exc4_a_response);
 	log_info("exc4_b_decay = %11.4k\n", parameter->exc4_b_decay);
 	log_info("exc4_b_response  = %11.4k\n", parameter->exc4_b_response);

 	log_info("exc5_response  = %11.4k\n", parameter->exc5_response);
 	log_info("exc5_a_decay  = %11.4k\n", parameter->exc5_a_decay);
 	log_info("exc5_a_response  = %11.4k\n", parameter->exc5_a_response);
 	log_info("exc5_b_decay = %11.4k\n", parameter->exc5_b_decay);
 	log_info("exc5_b_response  = %11.4k\n", parameter->exc5_b_response);

 	log_info("inh_response  = %11.4k\n", parameter->inh_response);
 	log_info("inh_a_decay  = %11.4k\n", parameter->inh_a_decay);
 	log_info("inh_a_response  = %11.4k\n", parameter->inh_a_response);
 	log_info("inh_b_decay = %11.4k\n", parameter->inh_b_decay);
 	log_info("inh_b_response  = %11.4k\n", parameter->inh_b_response);

 	log_info("inh2_response  = %11.4k\n", parameter->inh2_response);
 	log_info("inh2_a_decay  = %11.4k\n", parameter->inh2_a_decay);
 	log_info("inh2_a_response  = %11.4k\n", parameter->inh2_a_response);
 	log_info("inh2_b_decay = %11.4k\n", parameter->inh2_b_decay);
 	log_info("inh2_b_response  = %11.4k\n", parameter->inh2_b_response);

 	log_info("inh3_response  = %11.4k\n", parameter->inh3_response);
 	log_info("inh3_a_decay  = %11.4k\n", parameter->inh3_a_decay);
 	log_info("inh3_a_response  = %11.4k\n", parameter->inh3_a_response);
 	log_info("inh3_b_decay = %11.4k\n", parameter->inh3_b_decay);
 	log_info("inh3_b_response  = %11.4k\n", parameter->inh3_b_response);

 	log_info("inh4_response  = %11.4k\n", parameter->inh4_response);
 	log_info("inh4_a_decay  = %11.4k\n", parameter->inh4_a_decay);
 	log_info("inh4_a_response  = %11.4k\n", parameter->inh4_a_response);
 	log_info("inh4_b_decay = %11.4k\n", parameter->inh4_b_decay);
 	log_info("inh4_b_response  = %11.4k\n", parameter->inh4_b_response);

 	log_info("inh5_response  = %11.4k\n", parameter->inh5_response);
 	log_info("inh5_a_decay  = %11.4k\n", parameter->inh5_a_decay);
 	log_info("inh5_a_response  = %11.4k\n", parameter->inh5_a_response);
 	log_info("inh5_b_decay = %11.4k\n", parameter->inh5_b_decay);
 	log_info("inh5_b_response  = %11.4k\n", parameter->inh5_b_response);
 	*/
 }

 #endif // _DIFF_SYNAPSE_H_

