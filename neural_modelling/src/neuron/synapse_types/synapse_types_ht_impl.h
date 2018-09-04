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

#define NUM_EXCITATORY_RECEPTORS 2
#define NUM_INHIBITORY_RECEPTORS 2
#define NUM_NEUROMODULATORS 0

 //---------------------------------------
 // Synapse parameters
 //---------------------------------------

input_t excitatory_response[NUM_EXCITATORY_RECEPTORS];
input_t inhibitory_response[NUM_INHIBITORY_RECEPTORS];

typedef struct {
 	input_t a_response;
 	input_t a_A;
 	decay_t a_decay;
 	input_t b_response;
 	input_t b_B;
 	decay_t b_decay;
} bi_exp_parm;


 typedef struct synapse_param_t {

	// 2 excitatory bi-exponential synapses
	bi_exp_parm ex1_str;
	bi_exp_parm ex2_str;

	// 2 inhibitory bi-exponential synapses
	bi_exp_parm inh1_str;
	bi_exp_parm inh2_str;

 } synapse_param_t;

#include "synapse_types.h"

 //! human readable definition for the positions in the input regions for the
 //! different synapse types.
 typedef enum input_buffer_regions {
 	EXCITATORY, EXCITATORY2,
	INHIBITORY, INHIBITORY2
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

//	 synapse_types_print_parameters(parameter);

	 // EXCITATORY
	_shape_input(&parameter->ex1_str);
	_shape_input(&parameter->ex2_str);

	// INHIBITORY
	_shape_input(&parameter->inh1_str);
	_shape_input(&parameter->inh2_str);

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

 	} else if (synapse_type_index == INHIBITORY) {
 		_add_input(&parameter->inh1_str, input);

 	} else if (synapse_type_index == INHIBITORY2) {
 		_add_input(&parameter->inh2_str, input);

 	}
 }

 static inline input_t* synapse_types_get_excitatory_input(
 		synapse_param_pointer_t parameter) {

	 excitatory_response[0] = ((parameter->ex1_str.a_A * parameter->ex1_str.a_response)
			 + (parameter->ex1_str.b_B * parameter->ex1_str.b_response));

	 excitatory_response[1] = ((parameter->ex2_str.a_A * parameter->ex2_str.a_response)
					 + (parameter->ex2_str.b_B * parameter->ex2_str.b_response));

	 return &excitatory_response[0];
 }

 static inline input_t* synapse_types_get_inhibitory_input(
 		synapse_param_pointer_t parameter) {

	 inhibitory_response[0] = ((parameter->inh1_str.a_A * parameter->inh1_str.a_response)
			 + (parameter->inh1_str.b_B * parameter->inh1_str.b_response));

	 inhibitory_response[1] = ((parameter->inh2_str.a_A * parameter->inh2_str.a_response)
					 + (parameter->inh2_str.b_B * parameter->inh2_str.b_response));

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
	 use(parameter);
 }

 static inline void _print_ht_synapse_struct(bi_exp_parm* bi_exp_syn){
	 log_info(
			 "a_response: %k, a_A: %k, a_decay: %k, b_response: %k, b_B: %k, b_decay: %k",
 		 	bi_exp_syn->a_response,
 		 	bi_exp_syn->a_A,
 		 	bi_exp_syn->a_decay,
 		 	bi_exp_syn->b_response,
 		 	bi_exp_syn->b_B,
 		 	bi_exp_syn->b_decay);
 }

 static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
	 log_info("AMPA:");
	 _print_ht_synapse_struct(&parameter->ex1_str);
	 log_info("NMDA:");
	 _print_ht_synapse_struct(&parameter->ex2_str);
	 log_info("GABA_A:");
	 _print_ht_synapse_struct(&parameter->inh1_str);
	 log_info("GABA_B:");
	 _print_ht_synapse_struct(&parameter->inh2_str);
	 log_info("\n");

 }


 #endif // _DIFF_SYNAPSE_H_
