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
#define SYNAPSE_TYPE_BITS 3
#define SYNAPSE_TYPE_COUNT 8
#define SYNAPSE_INDEX_BITS 6

 //---------------------------------------
 // Synapse parameters
 //---------------------------------------

typedef struct {
 	input_t exc_a_response;
 	input_t exc_a_A;
 	decay_t exc_a_decay;
 	input_t exc_b_response;
 	input_t exc_b_B;
 	decay_t exc_b_decay;
} bi_exp_parm;


 typedef struct synapse_param_t {
	// excitatory
	// input_t exc_response;
// 	input_t exc_a_response;
// 	input_t exc_a_A;
// 	decay_t exc_a_decay;
// 	input_t exc_b_response;
// 	input_t exc_b_B;
// 	decay_t exc_b_decay;

	bi_exp_parm ex1_str;
	bi_exp_parm ex2_str;
	bi_exp_parm ex3_str;
	bi_exp_parm ex4_str;

	bi_exp_parm inh1_str;
	bi_exp_parm inh2_str;
	bi_exp_parm inh3_str;
	bi_exp_parm inh4_str;
 	// excitatory2

 } synapse_param_t;

#include "synapse_types.h"

 //! human readable definition for the positions in the input regions for the
 //! different synapse types.
 typedef enum input_buffer_regions {
 	EXCITATORY, EXCITATORY2, EXCITATORY3, EXCITATORY4, INHIBITORY, INHIBITORY2, INHIBITORY3, INHIBITORY4,
 } input_buffer_regions;


 static inline bi_exp_parm _shape_input(bi_exp_parm bi_exp_params){
	 	bi_exp_params.exc_a_response = decay_s1615(
	 			bi_exp_params.exc_a_response,
	 			bi_exp_params.exc_a_decay);

	 	bi_exp_params.exc_b_response = decay_s1615(
	 			bi_exp_params.exc_b_response,
	 			bi_exp_params.exc_b_decay);
	 	return bi_exp_params;
 }

 static inline void synapse_types_shape_input(synapse_param_pointer_t parameter){
 	// EXCITATORY
		parameter->ex1_str.exc_a_response = decay_s1615(
		 			parameter->ex1_str.exc_a_response,
		 			parameter->ex1_str.exc_a_decay);

    	parameter->ex1_str.exc_b_response = decay_s1615(
		 			parameter->ex1_str.exc_b_response,
		 			parameter->ex1_str.exc_b_decay);


 	// EXCITATORY2
	 _shape_input(parameter->ex2_str);
		parameter->ex2_str.exc_a_response = decay_s1615(
		 			parameter->ex2_str.exc_a_response,
		 			parameter->ex2_str.exc_a_decay);

    	parameter->ex2_str.exc_b_response = decay_s1615(
		 			parameter->ex2_str.exc_b_response,
		 			parameter->ex2_str.exc_b_decay);




 	// EXCITATORY3
	 _shape_input(parameter->ex3_str);
		parameter->ex3_str.exc_a_response = decay_s1615(
		 			parameter->ex3_str.exc_a_response,
		 			parameter->ex3_str.exc_a_decay);

    	parameter->ex3_str.exc_b_response = decay_s1615(
		 			parameter->ex3_str.exc_b_response,
		 			parameter->ex3_str.exc_b_decay);




 	// EXCITATORY4
	 _shape_input(parameter->ex4_str);
		parameter->ex4_str.exc_a_response = decay_s1615(
		 			parameter->ex4_str.exc_a_response,
		 			parameter->ex4_str.exc_a_decay);

    	parameter->ex4_str.exc_b_response = decay_s1615(
		 			parameter->ex4_str.exc_b_response,
		 			parameter->ex4_str.exc_b_decay);



 	// INHIBITORY
    //_shape_input(parameter->inh1_str);
		parameter->inh1_str.exc_a_response = decay_s1615(
		 			parameter->inh1_str.exc_a_response,
		 			parameter->inh1_str.exc_a_decay);

    	parameter->inh1_str.exc_b_response = decay_s1615(
		 			parameter->inh1_str.exc_b_response,
		 			parameter->inh1_str.exc_b_decay);




 	// INHIBITORY2

		parameter->inh2_str.exc_a_response = decay_s1615(
		 			parameter->inh2_str.exc_a_response,
		 			parameter->inh2_str.exc_a_decay);

    	parameter->inh2_str.exc_b_response = decay_s1615(
		 			parameter->inh2_str.exc_b_response,
		 			parameter->inh2_str.exc_b_decay);


	 // INHIBITORY3
		parameter->inh3_str.exc_a_response = decay_s1615(
		 			parameter->inh3_str.exc_a_response,
		 			parameter->inh3_str.exc_a_decay);

    	parameter->inh3_str.exc_b_response = decay_s1615(
		 			parameter->inh3_str.exc_b_response,
		 			parameter->inh3_str.exc_b_decay);


 	// INHIBITORY4
		parameter->inh4_str.exc_a_response = decay_s1615(
		 			parameter->inh4_str.exc_a_response,
		 			parameter->inh4_str.exc_a_decay);

    	parameter->inh4_str.exc_b_response = decay_s1615(
		 			parameter->inh4_str.exc_b_response,
		 			parameter->inh4_str.exc_b_decay);

/*
 	parameter->exc_response = (parameter->exc_a_A * parameter->exc_a_response) + (parameter->exc_b_B * parameter->exc_b_response);
 	parameter->exc2_response = (parameter->exc2_a_A * parameter->exc2_a_response) + (parameter->exc2_b_B * parameter->exc2_b_response);
 	parameter->exc3_response = (parameter->exc3_a_A * parameter->exc3_a_response) + (parameter->exc3_b_B * parameter->exc3_b_response);
 	parameter->exc4_response = (parameter->exc4_a_A * parameter->exc4_a_response) + (parameter->exc4_b_B * parameter->exc4_b_response);

 	parameter->inh_response = (parameter->inh_a_A * parameter->inh_a_response) + (parameter->inh_b_B * parameter->inh_b_response);
 	parameter->inh2_response = (parameter->inh2_a_A * parameter->inh2_a_response) + (parameter->inh2_b_B * parameter->inh2_b_response);
 	parameter->inh3_response = (parameter->inh3_a_A * parameter->inh3_a_response) + (parameter->inh3_b_B * parameter->inh3_b_response);
 	parameter->inh4_response = (parameter->inh4_a_A * parameter->inh4_a_response) + (parameter->inh4_b_B * parameter->inh4_b_response);
     */
 	/*
 	log_info("ex1 = %8.4k, ex2 = %8.4k, ex3 = %8.4k, ex4 = %8.4k, inh = %8.4k, inh2 = %8.4k, inh3 = %8.4k, inh4 = %8.4k,
 			parameter->exc_response,
			parameter->exc2_response,
			parameter->exc3_response,
			parameter->exc4_response,
			parameter->inh_response,
			parameter->inh2_response,
			parameter->inh3_response,
			parameter->inh4_response
			); */
 }

 static inline void _add_input(bi_exp_parm bi_exp_params, input_t input){
	 bi_exp_params.exc_a_response =  bi_exp_params.exc_a_response + input;
	 bi_exp_params.exc_b_response = bi_exp_params.exc_b_response + input;
 }

 static inline void synapse_types_add_neuron_input(
 		index_t synapse_type_index,
 		synapse_param_pointer_t parameter,
         input_t input){

 	if (synapse_type_index == EXCITATORY) {
 		//_add_input(parameter->ex1_str, input);
 		parameter->ex1_str.exc_a_response = parameter->ex1_str.exc_a_response + input;
 		parameter->ex1_str.exc_b_response = parameter->ex1_str.exc_b_response + input;


 	} else if (synapse_type_index == EXCITATORY2) {
 		parameter->ex2_str.exc_a_response =  parameter->ex2_str.exc_a_response + input;
 		parameter->ex2_str.exc_b_response = parameter->ex2_str.exc_b_response + input;

 	} else if (synapse_type_index == EXCITATORY3) {
 		parameter->ex3_str.exc_a_response =  parameter->ex3_str.exc_a_response + input;
 		parameter->ex3_str.exc_b_response = parameter->ex3_str.exc_b_response + input;


 	} else if (synapse_type_index == EXCITATORY4) {
 		parameter->ex4_str.exc_a_response =  parameter->ex4_str.exc_a_response + input;
 		parameter->ex4_str.exc_b_response = parameter->ex4_str.exc_b_response + input;



 	} else if (synapse_type_index == INHIBITORY) {
 		parameter->inh1_str.exc_a_response =  parameter->inh1_str.exc_a_response + input;
 		parameter->inh1_str.exc_b_response = parameter->inh1_str.exc_b_response + input;


 	} else if (synapse_type_index == INHIBITORY2) {
 		parameter->inh2_str.exc_a_response =  parameter->inh2_str.exc_a_response + input;
 		parameter->inh2_str.exc_b_response = parameter->inh2_str.exc_b_response + input;


 	} else if (synapse_type_index == INHIBITORY3) {
 		parameter->inh3_str.exc_a_response =  parameter->inh3_str.exc_a_response + input;
 		parameter->inh3_str.exc_b_response = parameter->inh3_str.exc_b_response + input;


 	} else if (synapse_type_index == INHIBITORY4) {
 		parameter->inh4_str.exc_a_response =  parameter->inh4_str.exc_a_response + input;
 		parameter->inh4_str.exc_b_response = parameter->inh4_str.exc_b_response + input;
 	}
 }

 static inline input_t synapse_types_get_excitatory_input(
 		synapse_param_pointer_t parameter) {
	 /*
 	return parameter->exc_response
 			+ parameter->exc2_response
 			+ parameter->exc3_response
 			+ parameter->exc4_response
 			*/
	 return ((parameter->ex1_str.exc_a_A * parameter->ex1_str.exc_a_response) + (parameter->ex1_str.exc_b_B * parameter->ex1_str.exc_b_response))+
			 ((parameter->ex2_str.exc_a_A * parameter->ex2_str.exc_a_response) + (parameter->ex2_str.exc_b_B * parameter->ex2_str.exc_b_response)) +
			 ((parameter->ex3_str.exc_a_A * parameter->ex3_str.exc_a_response) + (parameter->ex3_str.exc_b_B * parameter->ex3_str.exc_b_response)) +
			 ((parameter->ex4_str.exc_a_A * parameter->ex4_str.exc_a_response) + (parameter->ex4_str.exc_b_B * parameter->ex4_str.exc_b_response));
 }

 static inline input_t synapse_types_get_inhibitory_input(
 		synapse_param_pointer_t parameter) {
 	/*return parameter->inh_response
 			+ parameter->inh2_response
 			+ parameter->inh3_response
 			+ parameter->inh4_response
 			*/
	 return ((parameter->inh1_str.exc_a_A * parameter->inh1_str.exc_a_response) + (parameter->inh1_str.exc_b_B * parameter->inh1_str.exc_b_response))+
			 ((parameter->inh2_str.exc_a_A * parameter->inh2_str.exc_a_response) + (parameter->inh2_str.exc_b_B * parameter->inh2_str.exc_b_response)) +
			 ((parameter->inh3_str.exc_a_A * parameter->inh3_str.exc_a_response) + (parameter->inh3_str.exc_b_B * parameter->inh3_str.exc_b_response)) +
			 ((parameter->inh4_str.exc_a_A * parameter->inh4_str.exc_a_response) + (parameter->inh4_str.exc_b_B * parameter->inh4_str.exc_b_response));
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
 	}else if (synapse_type_index == INHIBITORY) {
 		return "I";
 	} else if (synapse_type_index == INHIBITORY2) {
 		return "I2";
 	} else if (synapse_type_index == INHIBITORY3) {
 		return "I3";
 	} else if (synapse_type_index == INHIBITORY4) {
 		return "I4";
 	} else {
 		log_debug("did not recognise synapse type %i", synapse_type_index);
 		return "?";
 	}
 }


 static inline void synapse_types_print_input(
         synapse_param_pointer_t parameter) {
	 use(parameter);
 }

 static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
 /*   log_info("-------------------------------------\n");

    log_info("exc_response  = %11.4k\n", parameter->exc_response);
 	log_info("exc_a_decay  = %11.4k\n", parameter->exc_a_decay);
 	log_info("exc_a_init   = %11.4k\n", parameter->exc_a_init);
 	log_info("exc_a_response  = %11.4k\n", parameter->exc_a_response);
 	log_info("exc_b_decay = %11.4k\n", parameter->exc_b_decay);
 	log_info("exc_b_init  = %11.4k\n", parameter->exc_b_init);
 	log_info("exc_b_response  = %11.4k\n", parameter->exc_b_response);

 	log_info("exc2_response  = %11.4k\n", parameter->exc2_response);
 	log_info("exc2_a_decay  = %11.4k\n", parameter->exc2_a_decay);
 	log_info("exc2_a_init   = %11.4k\n", parameter->exc2_a_init);
 	log_info("exc2_a_response  = %11.4k\n", parameter->exc2_a_response);
 	log_info("exc2_b_decay = %11.4k\n", parameter->exc2_b_decay);
 	log_info("exc2_b_init  = %11.4k\n", parameter->exc2_b_init);
 	log_info("exc2_b_response  = %11.4k\n", parameter->exc2_b_response);

 	log_info("exc3_response  = %11.4k\n", parameter->exc3_response);
 	log_info("exc3_a_decay  = %11.4k\n", parameter->exc3_a_decay);
 	log_info("exc3_a_init   = %11.4k\n", parameter->exc3_a_init);
 	log_info("exc3_a_response  = %11.4k\n", parameter->exc3_a_response);
 	log_info("exc3_b_decay = %11.4k\n", parameter->exc3_b_decay);
 	log_info("exc3_b_init  = %11.4k\n", parameter->exc3_b_init);
 	log_info("exc3_b_response  = %11.4k\n", parameter->exc3_b_response);

 	log_info("exc4_response  = %11.4k\n", parameter->exc4_response);
 	log_info("exc4_a_decay  = %11.4k\n", parameter->exc4_a_decay);
 	log_info("exc4_a_init   = %11.4k\n", parameter->exc4_a_init);
 	log_info("exc4_a_response  = %11.4k\n", parameter->exc4_a_response);
 	log_info("exc4_b_decay = %11.4k\n", parameter->exc4_b_decay);
 	log_info("exc4_b_init  = %11.4k\n", parameter->exc4_b_init);
 	log_info("exc4_b_response  = %11.4k\n", parameter->exc4_b_response);

 	log_info("inh_response  = %11.4k\n", parameter->inh_response);
 	log_info("inh_a_decay  = %11.4k\n", parameter->inh_a_decay);
 	log_info("inh_a_init   = %11.4k\n", parameter->inh_a_init);
 	log_info("inh_a_response  = %11.4k\n", parameter->inh_a_response);
 	log_info("inh_b_decay = %11.4k\n", parameter->inh_b_decay);
 	log_info("inh_b_init  = %11.4k\n", parameter->inh_b_init);
 	log_info("inh_b_response  = %11.4k\n", parameter->inh_b_response);

 	log_info("inh2_response  = %11.4k\n", parameter->inh2_response);
 	log_info("inh2_a_decay  = %11.4k\n", parameter->inh2_a_decay);
 	log_info("inh2_a_init   = %11.4k\n", parameter->inh2_a_init);
 	log_info("inh2_a_response  = %11.4k\n", parameter->inh2_a_response);
 	log_info("inh2_b_decay = %11.4k\n", parameter->inh2_b_decay);
 	log_info("inh2_b_init  = %11.4k\n", parameter->inh2_b_init);
 	log_info("inh2_b_response  = %11.4k\n", parameter->inh2_b_response);

 	log_info("inh3_response  = %11.4k\n", parameter->inh3_response);
 	log_info("inh3_a_decay  = %11.4k\n", parameter->inh3_a_decay);
 	log_info("inh3_a_init   = %11.4k\n", parameter->inh3_a_init);
 	log_info("inh3_a_response  = %11.4k\n", parameter->inh3_a_response);
 	log_info("inh3_b_decay = %11.4k\n", parameter->inh3_b_decay);
 	log_info("inh3_b_init  = %11.4k\n", parameter->inh3_b_init);
 	log_info("inh3_b_response  = %11.4k\n", parameter->inh3_b_response);

 	log_info("inh4_response  = %11.4k\n", parameter->inh4_response);
 	log_info("inh4_a_decay  = %11.4k\n", parameter->inh4_a_decay);
 	log_info("inh4_a_init   = %11.4k\n", parameter->inh4_a_init);
 	log_info("inh4_a_response  = %11.4k\n", parameter->inh4_a_response);
 	log_info("inh4_b_decay = %11.4k\n", parameter->inh4_b_decay);
 	log_info("inh4_b_init  = %11.4k\n", parameter->inh4_b_init);
 	log_info("inh4_b_response  = %11.4k\n", parameter->inh4_b_response);

 	*/
 }

 #endif // _DIFF_SYNAPSE_H_

