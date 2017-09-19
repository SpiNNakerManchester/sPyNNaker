/*! \file
 * \brief implementation of synapse_types.h for an alpha synapse behaviour
 */

#ifndef _ALPHA_SYNAPSE_H_
#define _ALPHA_SYNAPSE_H_

#include "../decay.h"
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

	// buffer for linear term
	input_t exc_lin_buff;

	// buffer for exponential term
	input_t exc_exp_buff;

	// Inverse of tau
	input_t inv_exc_tau_sqr;

	// Exponential decay multiplier
	decay_t exc_decay;


	input_t inh_lin_buff;
	input_t inh_exp_buff;
	input_t inv_inh_tau_sqr;
	decay_t inh_decay;

} synapse_param_t;

#include "synapse_types.h"

//! human readable definition for the positions in the input regions for the
//! different synapse types.
typedef enum input_buffer_regions {
	EXCITATORY, INHIBITORY,
} input_buffer_regions;

// Synapse shaping - called every timestep to evolve PSC
static inline void synapse_types_shape_input(synapse_param_pointer_t parameter){
	// Excitatory

	// Update linear buffer
	parameter->exc_lin_buff = parameter->exc_lin_buff + parameter->dt * parameter->inv_exc_tau_sqr;

	// Update exponential buffer
	parameter->exc_exp_buff = decay_s1615(
			parameter->exc_exp_buff,
			parameter->exc_decay);

	log_info("lin: %12.6k, exp: %12.6k, comb: %12.6k", parameter->exc_lin_buff, parameter->exc_exp_buff, parameter->exc_lin_buff*parameter->exc_exp_buff);

	//INHIBITORY


}


// Add input from ring buffer - zero if no spikes, otherwise one or more weights
static inline void synapse_types_add_neuron_input(
		index_t synapse_type_index,
		synapse_param_pointer_t parameter,
        input_t input){

	if (synapse_type_index == EXCITATORY) {

		if (input > 0.0){
			// Update exponential buffer
			parameter->exc_exp_buff = parameter->exc_exp_buff * decay_s1615(
				input,	parameter->exc_decay) + 1;

			// Update linear buffer second (need t+1 value of exponential buffer)
			parameter->exc_lin_buff = (parameter->exc_lin_buff + parameter->dt * parameter->inv_exc_tau_sqr) * (1 - 1/parameter->exc_exp_buff);
		}

	} else if (synapse_type_index == INHIBITORY) {

	}
}

static inline input_t synapse_types_get_excitatory_input(
		synapse_param_pointer_t parameter) {
	return parameter->exc_lin_buff * parameter->exc_exp_buff;
}

static inline input_t synapse_types_get_inhibitory_input(
		synapse_param_pointer_t parameter) {
	return parameter->inh_lin_buff * parameter->inh_exp_buff;
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
        IO_BUF, "EX: %12.6k + INH: %12.6k",
        parameter->exc_lin_buff * parameter->exc_exp_buff,
        parameter->inh_lin_buff * parameter->inh_exp_buff);
}

static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
    log_info("-------------------------------------\n");
	log_info("exc_response  = %11.4k\n", parameter->exc_lin_buff);
	log_info("inh_response  = %11.4k\n", parameter->inh_lin_buff);
}

#endif // _ALPHA_SYNAPSE_H_
