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

typedef struct alpha_params{
	input_t dt;

	// buffer for linear term
	input_t lin_buff;

	// buffer for exponential term
	input_t exp_buff;

	// Inverse of tau
	input_t inv_tau_sqr;

	// Exponential decay multiplier
	decay_t decay;
}alpha_params;

//---------------------------------------
// Synapse parameters
//---------------------------------------
typedef struct synapse_param_t {
	alpha_params exc;
	alpha_params inh;
} synapse_param_t;

#include "synapse_types.h"

//! human readable definition for the positions in the input regions for the
//! different synapse types.
typedef enum input_buffer_regions {
	EXCITATORY, INHIBITORY,
} input_buffer_regions;


static inline void _alpha_shaping(alpha_params* a_params){
	a_params->lin_buff = a_params->lin_buff + a_params->dt * a_params->inv_tau_sqr;

	// Update exponential buffer
	a_params->exp_buff = decay_s1615(
			a_params->exp_buff,
			a_params->decay);
}


// Synapse shaping - called every timestep to evolve PSC
static inline void synapse_types_shape_input(synapse_param_pointer_t parameter){
	_alpha_shaping(&parameter->exc);
	_alpha_shaping(&parameter->inh);

	log_info("lin: %12.6k, exp: %12.6k, comb: %12.6k",
			parameter->exc.lin_buff,
			parameter->exc.exp_buff,
			parameter->exc.lin_buff * parameter->exc.exp_buff);
}


static inline void _add_input_alpha(alpha_params* a_params, input_t input){
	a_params->exp_buff = a_params->exp_buff * input + 1;
	a_params->lin_buff = (a_params->lin_buff
			+ a_params->dt * a_params->inv_tau_sqr)
					* ( 1 - 1/a_params->exp_buff);
}


// Add input from ring buffer - zero if no spikes, otherwise one or more weights
static inline void synapse_types_add_neuron_input(
		index_t synapse_type_index,
		synapse_param_pointer_t parameter,
        input_t input){

	if (input > 0.0){
		if (synapse_type_index == EXCITATORY) {
				_add_input_alpha(&parameter->exc, input);

		} else if (synapse_type_index == INHIBITORY) {
				_add_input_alpha(&parameter->inh, input);
		}
	}
}

static inline input_t synapse_types_get_excitatory_input(
		synapse_param_pointer_t parameter) {
	return parameter->exc.lin_buff * parameter->exc.exp_buff;
}

static inline input_t synapse_types_get_inhibitory_input(
		synapse_param_pointer_t parameter) {
	return parameter->inh.lin_buff * parameter->inh.exp_buff;
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
//    io_printf(
//        IO_BUF, "EX: %12.6k + INH: %12.6k",
}

static inline void synapse_types_print_parameters(synapse_param_pointer_t parameter) {
    log_info("-------------------------------------\n");
	log_info("exc_response  = %11.4k\n", parameter->exc.lin_buff * parameter->exc.exp_buff);
	log_info("inh_response  = %11.4k\n", parameter->inh.lin_buff * parameter->inh.exp_buff);
}

#endif // _ALPHA_SYNAPSE_H_
