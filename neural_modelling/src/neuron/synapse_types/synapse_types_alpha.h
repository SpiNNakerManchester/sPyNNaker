/*! \file
 * \brief implementation of synapse_types.h for an alpha synapse behaviour
 */

#ifndef _ALPHA_SYNAPSE_H_
#define _ALPHA_SYNAPSE_H_

#include <neuron/decay.h>
#include <debug.h>

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 1
#define SYNAPSE_TYPE_COUNT 2

//---------------------------------------
// Synapse parameters
//---------------------------------------
typedef struct synapse_param_t {

	input_t dt;

	input_t exc_response;

	input_t exc_exp_response;
	input_t exc_const_response;
	input_t exc_t;
	input_t exc_k;
	input_t exc_tau_inv;
	decay_t exc_decay;
	decay_t exc_init;


	input_t inh_response;
	input_t inh_exp_response;
	input_t inh_const_response;
	input_t inh_t;
	input_t inh_k;
	input_t inh_tau_inv;
	decay_t inh_decay;
	decay_t inh_init;

} synapse_param_t;

#include <neuron/synapse_types/synapse_types.h>

//! human readable definition for the positions in the input regions for the
//! different synapse types.
typedef enum input_buffer_regions {
	EXCITATORY, INHIBITORY,
} input_buffer_regions;

// Synapse shaping - called every timestep to evolve PSC
static inline void synapse_types_shape_input(synapse_param_pointer_t parameter){
	// Excitatory
	parameter->exc_exp_response = decay_s1615(
			parameter->exc_exp_response,
			parameter->exc_decay);

	parameter->exc_const_response =  parameter->exc_k
					  * parameter->exc_t
					  * parameter->exc_tau_inv;

	parameter->exc_response = parameter->exc_exp_response * parameter->exc_const_response;

	parameter->exc_t += parameter->dt;

}


// Add input from ring buffer - zero if no spikes, otherwise one or more weights
static inline void synapse_types_add_neuron_input(
		index_t synapse_type_index,
		synapse_param_pointer_t parameter,
        input_t input){

	if (synapse_type_index == EXCITATORY) {
		parameter->exc_exp_response = parameter->exc_exp_response + decay_s1615(
				input,	parameter->exc_init);
		if (input > 0.1){
			parameter->exc_t = 0;
		}
/*		parameter->exc_const_response = parameter->exc_const_response +
				(parameter->exc_k
				  * parameter->exc_t
				  * parameter->exc_tau_inv);
		parameter->exc_response =  parameter->exc_const_response * parameter->exc_exp_response;
		parameter->exc_t += parameter->dt;
*/
	} else if (synapse_type_index == INHIBITORY) {

	}
}

static inline input_t synapse_types_get_excitatory_input(
		synapse_param_pointer_t parameter) {
	return parameter->exc_response;
}

static inline input_t synapse_types_get_inhibitory_input(
		synapse_param_pointer_t parameter) {
	return parameter->inh_response;
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
        parameter->exc_response,
        parameter->inh_response);
}

static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
    log_info("-------------------------------------\n");
	log_info("exc_response  = %11.4k\n", parameter->exc_response);
	log_info("inh_response  = %11.4k\n", parameter->inh_response);
}

#endif // _ALPHA_SYNAPSE_H_
