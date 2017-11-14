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
 	input_t a_response;
 	input_t a_A;
 	decay_t a_decay;
 	input_t b_response;
 	input_t b_B;
 	decay_t b_decay;
} bi_exp_parm;


 typedef struct synapse_param_t {

	// 4 excitatory bi-exponential synapses
	bi_exp_parm ex1_str;
	bi_exp_parm ex2_str;
	bi_exp_parm ex3_str;

	// 4 inhibitory bi-exponential synapses
	bi_exp_parm inh1_str;
	bi_exp_parm inh2_str;
	bi_exp_parm inh3_str;
 } synapse_param_t;

#include "synapse_types.h"

 //! human readable definition for the positions in the input regions for the
 //! different synapse types.
 typedef enum input_buffer_regions {
 	EXCITATORY, EXCITATORY2, EXCITATORY3, INHIBITORY, INHIBITORY2, INHIBITORY3
 } input_buffer_regions;


 //static inline bi_exp_parm _shape_input(bi_exp_parm bi_exp_params){
 static inline void _shape_input(bi_exp_parm* bi_exp_params){
	 	bi_exp_params->a_response = decay_s1615(
	 			bi_exp_params->a_response,
	 			bi_exp_params->a_decay);

	 	bi_exp_params->b_response = decay_s1615(
	 			bi_exp_params->b_response,
	 			bi_exp_params->b_decay);
 }

 static inline void synapse_types_shape_input(synapse_param_pointer_t parameter){

 	// EXCITATORY
	_shape_input(&parameter->ex1_str);
	_shape_input(&parameter->ex2_str);
	_shape_input(&parameter->ex3_str);

	// INHIBITORY
	_shape_input(&parameter->inh1_str);
	_shape_input(&parameter->inh2_str);
	_shape_input(&parameter->inh3_str);
 }

 static inline void _add_input(bi_exp_parm* bi_exp_params, input_t input){
	 bi_exp_params->a_response =  bi_exp_params->a_response + input;
	 bi_exp_params->b_response = bi_exp_params->b_response + input;
 }

 static inline void synapse_types_add_neuron_input(
 		index_t synapse_type_index,
 		synapse_param_pointer_t parameter,
         input_t input){

 	if (synapse_type_index == EXCITATORY) {
 		_add_input(&parameter->ex1_str, input);

 	} else if (synapse_type_index == EXCITATORY2) {
 		_add_input(&parameter->ex2_str, input);

 	} else if (synapse_type_index == EXCITATORY3) {
 		_add_input(&parameter->ex3_str, input);

 	} else if (synapse_type_index == INHIBITORY) {
 		_add_input(&parameter->inh1_str, input);

 	} else if (synapse_type_index == INHIBITORY2) {
 		_add_input(&parameter->inh2_str, input);

 	} else if (synapse_type_index == INHIBITORY3) {
 		_add_input(&parameter->inh3_str, input);

 	}
 }

 static inline input_t synapse_types_get_excitatory_input(
 		synapse_param_pointer_t parameter) {

	 return ((parameter->ex1_str.a_A * parameter->ex1_str.a_response) + (parameter->ex1_str.b_B * parameter->ex1_str.b_response))+
			 ((parameter->ex2_str.a_A * parameter->ex2_str.a_response) + (parameter->ex2_str.b_B * parameter->ex2_str.b_response)) +
			 ((parameter->ex3_str.a_A * parameter->ex3_str.a_response) + (parameter->ex3_str.b_B * parameter->ex3_str.b_response));
 }

 static inline input_t synapse_types_get_inhibitory_input(
 		synapse_param_pointer_t parameter) {
	 return ((parameter->inh1_str.a_A * parameter->inh1_str.a_response) + (parameter->inh1_str.b_B * parameter->inh1_str.b_response))+
			 ((parameter->inh2_str.a_A * parameter->inh2_str.a_response) + (parameter->inh2_str.b_B * parameter->inh2_str.b_response)) +
			 ((parameter->inh3_str.a_A * parameter->inh3_str.a_response) + (parameter->inh3_str.b_B * parameter->inh3_str.b_response));
 }

 static inline const char *synapse_types_get_type_char(
 		index_t synapse_type_index) {
 	if (synapse_type_index == EXCITATORY) {
 		return "X";
 	}else if (synapse_type_index == EXCITATORY2) {
 		return "X2";
 	}else if (synapse_type_index == EXCITATORY3) {
 		return "X3";
 	}else if (synapse_type_index == INHIBITORY) {
 		return "I";
 	} else if (synapse_type_index == INHIBITORY2) {
 		return "I2";
 	} else if (synapse_type_index == INHIBITORY3) {
 		return "I3";
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

    log_info("response  = %11.4k\n", parameter->response);
 	log_info("a_decay  = %11.4k\n", parameter->a_decay);
 	log_info("a_init   = %11.4k\n", parameter->a_init);
 	log_info("a_response  = %11.4k\n", parameter->a_response);
 	log_info("b_decay = %11.4k\n", parameter->b_decay);
 	log_info("b_init  = %11.4k\n", parameter->b_init);
 	log_info("b_response  = %11.4k\n", parameter->b_response);

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

